import os
import json
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd

import main


class FakeEmbeddings:
    def __init__(self):
        self.calls = []

    def create(self, model, input):
        self.calls.append((model, list(input)))
        data = [
            SimpleNamespace(embedding=[float(index + 1), 1.0, 0.5])
            for index, _ in enumerate(input)
        ]
        return SimpleNamespace(data=data)


class FakeClient:
    def __init__(self):
        self.embeddings = FakeEmbeddings()
        self.chat = SimpleNamespace(completions=FakeChatCompletions())


class FakeChatCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **request):
        self.calls.append(request)
        content = json.dumps(
            {
                "results": [
                    {
                        "id": "0",
                        "decision": "uncertain",
                        "confidence": "low",
                        "reason": "Mocked conservative result",
                    }
                ]
            }
        )
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


class QwenScoringTests(unittest.TestCase):
    def test_qwen_embedding_only_splits_batches_and_uses_model_cache_key(self):
        fake_client = FakeClient()
        with tempfile.TemporaryDirectory() as tmp:
            input_path = os.path.join(tmp, "input.xlsx")
            output_path = os.path.join(tmp, "output.xlsx")
            cache_path = os.path.join(tmp, "cache.pkl")
            refs = [f"paper {index}" for index in range(12)]
            pd.DataFrame({"Email": ["Author"] * len(refs), "Article": refs}).to_excel(input_path, index=False)

            with patch("main.make_openai_client", return_value=fake_client):
                result = main.qwen_ai_score_ref_column(
                    input_file=input_path,
                    output_file=output_path,
                    api_key="test-key",
                    topic="test topic",
                    cache_file=cache_path,
                    batch_size=100,
                    embedding_only=True,
                )

            self.assertEqual(result, output_path)
            self.assertTrue(os.path.exists(output_path))
            self.assertTrue(os.path.exists(cache_path))
            output = pd.read_excel(output_path)
            self.assertIn("score", output.columns)
            self.assertEqual(output.columns.tolist(), ["Email", "Article", "score"])
            self.assertNotIn("final_decision", output.columns)

            call_sizes = [len(call_input) for _, call_input in fake_client.embeddings.calls]
            self.assertEqual(call_sizes, [1, 10, 2])
            self.assertTrue(
                all(model == main.QWEN_EMBEDDING_MODEL for model, _ in fake_client.embeddings.calls)
            )

    def test_scope_roundtrip_windows_newlines_and_long_text(self):
        for scope in ("Heart research\r\nVascular studies", "a" * 33000, "NA"):
            with self.subTest(length=len(scope)), tempfile.TemporaryDirectory() as tmp:
                source, scores, result = [os.path.join(tmp, name) for name in ("input.xlsx", "scores.xlsx", "result.xlsx")]
                pd.DataFrame({"Email": ["a@example.org"], "Article": ["Heart"]}).to_excel(source, index=False)
                with patch("main.make_openai_client", return_value=FakeClient()):
                    main.qwen_ai_score_ref_column(source, scores, "key", scope, embedding_only=True, cache_file=os.path.join(tmp, "cache.pkl"))
                    main.qwen_ai_score_ref_column(scores, result, "key", scope, llm_only=True)
                    with self.assertRaisesRegex(ValueError, "different scope"):
                        main.qwen_ai_score_ref_column(scores, result, "key", "Different research", llm_only=True)
                    if "\r" in scope:
                        # Existing workbooks have no fingerprint. Verify backward compatibility.
                        import openpyxl
                        book = openpyxl.load_workbook(scores)
                        sheet = book["Settings"]
                        for row in range(sheet.max_row, 1, -1):
                            if sheet.cell(row, 1).value == "screening_topic_hash":
                                sheet.delete_rows(row)
                        for row in range(2, sheet.max_row + 1):
                            if sheet.cell(row, 1).value == "screening_topic":
                                sheet.cell(row, 2).value = scope.replace("\r", "_x000D_")
                        book.save(scores)
                        book.close()
                        main.qwen_ai_score_ref_column(scores, result, "key", scope, llm_only=True)

    def test_full_and_llm_only_modes_emit_expected_columns(self):
        fake_client = FakeClient()
        messages = []
        expected_columns = {"score", "final_decision", "screening_reason"}
        with tempfile.TemporaryDirectory() as tmp:
            full_input = os.path.join(tmp, "full_input.xlsx")
            full_output = os.path.join(tmp, "full_output.xlsx")
            llm_input = os.path.join(tmp, "llm_input.xlsx")
            llm_output = os.path.join(tmp, "llm_output.xlsx")
            cache_path = os.path.join(tmp, "cache.pkl")
            pd.DataFrame({"Email": ["A", "B"], "Article": ["topic-aligned paper", "borderline paper"]}).to_excel(full_input, index=False)
            pd.DataFrame({"Email": ["A", "B", "C"], "Article": ["same paper", "same paper", "same paper"], "score": [0.25, 0.3, 0.35]}).to_excel(
                llm_input,
                index=False,
            )

            with patch("main.make_openai_client", return_value=fake_client):
                result = main.qwen_ai_score_ref_column(
                    progress_callback=lambda progress, message, done=False: messages.append(message),
                    input_file=full_input,
                    output_file=full_output,
                    api_key="test-key",
                    topic="test topic",
                    cache_file=cache_path,
                    batch_size=100,
                )
                main.qwen_ai_score_ref_column(
                    progress_callback=lambda progress, message, done=False: messages.append(message),
                    input_file=llm_input,
                    output_file=llm_output,
                    api_key="test-key",
                    topic="test topic",
                    cache_file=cache_path,
                    llm_only=True,
                )

            self.assertTrue(messages)
            for message in messages:
                self.assertNotRegex(message, r"[\u4e00-\u9fff]")
            with pd.ExcelFile(full_output) as workbook:
                self.assertEqual(workbook.sheet_names, ["Results", "Details", "Settings"])
            self.assertEqual(pd.read_excel(full_output, sheet_name="Details").result_row.tolist(), [2, 3])
            self.assertEqual(result, full_output)
            self.assertEqual(pd.read_excel(llm_output).final_decision.tolist(), ["不符合范围", "需人工复核", "符合筛选条件"])
            self.assertTrue(expected_columns.issubset(pd.read_excel(full_output).columns))
            self.assertTrue(expected_columns.issubset(pd.read_excel(llm_output).columns))


if __name__ == "__main__":
    unittest.main()
