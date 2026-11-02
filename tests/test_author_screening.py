import unittest
import tempfile
from pathlib import Path
from openpyxl import load_workbook
import pandas as pd
from screening import prepare_research, add_screening_results, validate_settings, write_screening_excel


class AuthorScreeningTests(unittest.TestCase):
    def test_new_fields_and_ignored_metadata(self):
        frame = pd.DataFrame({'Email': ['A'], 'Article': ['Heart'], 'Keywords': ['vascular'], 'Abstract': ['Study'], 'Affiliation': ['SECRET'], 'Country/Region': ['SECRET'], 'Journal title': ['SECRET']})
        self.assertEqual(prepare_research(frame), ['Article: Heart\nKeywords: vascular\nAbstract: Study'])
        self.assertEqual(prepare_research(frame[['Email', 'Article']]), ['Article: Heart'])
        with self.assertRaises(ValueError):
            prepare_research(pd.DataFrame({'Email': ['A'], 'ref': ['Heart']}))
        with self.assertRaises(ValueError):
            prepare_research(pd.DataFrame({'Email': ['A'], 'Article': [None]}))

    def test_email_required_and_name_optional(self):
        frame = pd.DataFrame({'Email': ['author@example.org'], 'Article': ['Heart']})
        expected = prepare_research(frame)
        frame['Name'] = None
        self.assertEqual(prepare_research(frame), expected)
        frame['Name'] = 'Any Name'
        self.assertEqual(prepare_research(frame), expected)
        with self.assertRaisesRegex(ValueError, 'Email'):
            prepare_research(frame.drop(columns=['Email']))
        frame['Email'] = '   '
        with self.assertRaisesRegex(ValueError, 'Email'):
            prepare_research(frame)
        frame['Email'] = None
        with self.assertRaisesRegex(ValueError, 'Email'):
            prepare_research(frame)
        frame = pd.DataFrame({' email ': ['author@example.org'], 'Article': ['Heart']})
        self.assertEqual(prepare_research(frame), expected)

    def test_affiliation_matrix_and_row_independence(self):
        frame = pd.DataFrame({'Article': ['same'] * 6, 'Affiliation': ['CARDIOLOGY', 'Other', None, 'cardiology', 'cardiology', 'cardiology'], 'scope_decision': ['in_scope_by_score'] * 3 + ['out_of_scope', 'uncertain', 'embedding_only'], 'scope_confidence': ['not_checked'] * 3 + ['high', 'low', 'not_checked'], 'exclude': [False] * 3 + [True, False, False]})
        output = add_screening_results(frame, 'heart', .25, .35, True, 'cardiology\n心血管')
        self.assertEqual(output.final_decision.tolist(), ['符合筛选条件', '符合筛选条件', '符合筛选条件', '不符合范围', '需人工复核', '未审核'])
        self.assertNotIn('affiliation_matches', output.columns)
        self.assertNotIn('affiliation_result', output.columns)
        self.assertEqual(output.final_exclude.tolist(), [False, False, False, True, False, False])
        disabled = add_screening_results(frame, 'heart', .25, .35, False, '')
        self.assertEqual(disabled.final_decision.iloc[1], '符合筛选条件')

    def test_affiliation_cell_highlighting(self):
        frame = pd.DataFrame({'Email': ['A', 'B', 'C', 'D'], 'Affiliation': ['CARDIOLOGY', 'Other', None, '心血管中心']})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'result.xlsx'
            for enabled in (True, False):
                write_screening_excel(frame, path, enabled, 'cardiology\n心血管')
                book = load_workbook(path)
                sheet = book.active
                self.assertEqual([sheet.cell(row, 2).fill.patternType for row in range(2, 6)],
                                 ['solid', None, None, 'solid'] if enabled else [None] * 4)
                if enabled:
                    self.assertEqual(sheet['B2'].fill.fgColor.rgb, '00C6EFCE')
                self.assertIsNone(sheet['A2'].fill.patternType)
                book.close()
            write_screening_excel(frame[['Email']], path, True, 'cardiology')

    def test_invalid_thresholds_and_keywords(self):
        for lower, upper in [(float('nan'), .3), (.3, float('inf')), (.5, .3), (.3, .3), (-2, .3)]:
            with self.assertRaises(ValueError):
                validate_settings(lower, upper)
        with self.assertRaises(ValueError):
            validate_settings(.25, .35, True, '  \n')
