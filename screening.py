"""Input preparation and deterministic author-screening rules."""
import math
import hashlib
import pandas as pd


def normalize_scope(value):
    return str(value).replace("\r\n", "\n").replace("\r", "\n").strip()


def scope_fingerprint(value):
    return hashlib.sha256(normalize_scope(value).encode("utf-8")).hexdigest()


def keywords_from_text(value):
    return list(dict.fromkeys(word.strip().casefold() for word in value.splitlines() if word.strip()))


def validate_settings(lower, upper, enabled=False, keywords=""):
    if not all(math.isfinite(x) and -1 <= x <= 1 for x in (lower, upper)) or lower >= upper:
        raise ValueError("Score thresholds must be between -1 and 1, with the lower threshold below the upper threshold")
    if enabled and not keywords_from_text(keywords):
        raise ValueError("Enter affiliation keywords, one per line, when affiliation screening is enabled")


def prepare_research(df):
    columns = {str(col).strip().casefold(): col for col in df.columns}
    for field in ("email", "article"):
        if field not in columns:
            raise ValueError(f"Excel must contain a {field.title()} column; ref/refs/Reference are no longer supported")
        if df[columns[field]].fillna("").astype(str).str.strip().eq("").any():
            raise ValueError(f"The {field.title()} column contains blank values. Complete them and try again")
    if df.empty:
        raise ValueError("The Excel file contains no data rows")
    texts = []
    for _, row in df.iterrows():
        parts = []
        for field in ("article", "keywords", "abstract"):
            value = row[columns[field]] if field in columns else None
            if pd.notna(value) and str(value).strip():
                parts.append(f"{field.title()}: {str(value).strip()}")
        texts.append("\n".join(parts))
    return texts


def add_screening_results(df, topic, lower, upper, enabled, keywords):
    words = keywords_from_text(keywords)
    research, sources, finals = [], [], []
    df.drop(columns=["affiliation_result", "affiliation_matches"], errors="ignore", inplace=True)
    for _, row in df.iterrows():
        decision = row["scope_decision"]
        source = "仅评分" if decision == "embedding_only" else "用户阈值" if decision.endswith("by_score") else "LLM 审核"
        if decision == "embedding_only":
            scope = "未审核"
        elif decision in {"in_scope", "in_scope_by_score"} and row["scope_confidence"] != "low":
            scope = "符合范围"
        elif bool(row["exclude"]):
            scope = "不符合范围"
        else:
            scope = "需人工复核"
        final = "符合筛选条件" if scope == "符合范围" else scope
        research.append(scope)
        sources.append(source)
        finals.append(final)
    df["research_decision"] = research
    df["decision_source"] = sources
    df["final_decision"] = finals
    df["final_exclude"] = [value == "不符合范围" for value in finals]
    df["screening_topic"] = topic
    df["screening_topic_hash"] = scope_fingerprint(topic)
    df["score_lower_threshold"] = lower
    df["score_upper_threshold"] = upper
    df["affiliation_filter_enabled"] = enabled
    df["affiliation_filter_keywords"] = "\n".join(words) if enabled else ""
    return df


RESULT_COLUMNS = {
    "score", "scope_decision", "scope_confidence", "exclude", "screening_reason",
    "research_decision", "decision_source", "final_decision", "final_exclude",
    "screening_topic", "screening_topic_hash", "score_lower_threshold", "score_upper_threshold",
    "affiliation_filter_enabled", "affiliation_filter_keywords",
    "affiliation_result", "affiliation_matches",
}


def write_screening_excel(df, output_file, enabled=False, keywords=""):
    """Export a concise first sheet with separate audit details and settings."""
    from openpyxl.styles import PatternFill, Font, Alignment
    from openpyxl.utils import get_column_letter

    settings = ["screening_topic", "screening_topic_hash", "score_lower_threshold", "score_upper_threshold",
                "affiliation_filter_enabled", "affiliation_filter_keywords"]
    original = [column for column in df.columns if column not in RESULT_COLUMNS]
    scores_only = "scope_decision" in df and df["scope_decision"].eq("embedding_only").all()
    summary = ("score",) if scores_only else ("score", "final_decision", "screening_reason")
    visible = original + [column for column in summary if column in df]
    words = keywords_from_text(keywords)
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df[visible].to_excel(writer, sheet_name="Results", index=False)
        detail_columns = [column for column in ("scope_decision", "scope_confidence", "exclude",
                          "research_decision", "decision_source", "final_exclude") if column in df]
        if detail_columns and not scores_only:
            details = df[detail_columns].copy()
            details.insert(0, "result_row", range(2, len(df) + 2))
            email = next((c for c in df.columns if str(c).strip().casefold() == "email"), None)
            if email is not None:
                details.insert(1, "Email", df[email].values)
            details.to_excel(writer, sheet_name="Details", index=False)
        if len(df) and any(column in df for column in settings):
            pd.DataFrame([(column, df[column].iloc[0]) for column in settings if column in df],
                         columns=["Setting", "Value"]).to_excel(writer, sheet_name="Settings", index=False)
        for sheet in writer.sheets.values():
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            for cell in sheet[1]:
                cell.fill = PatternFill(fill_type="solid", fgColor="17365D")
                cell.font = Font(color="FFFFFF", bold=True)
                cell.alignment = Alignment(wrap_text=True, vertical="center")
                width = 48 if str(cell.value).lower() in {"article", "abstract", "affiliation", "screening_reason", "value"} else 24
                sheet.column_dimensions[get_column_letter(cell.column)].width = width
            sheet.row_dimensions[1].height = 30
            for row in sheet.iter_rows(min_row=2):
                for cell in row:
                    cell.alignment = Alignment(wrap_text=True, vertical="top")
        sheet = writer.sheets["Results"]
        if "score" in visible:
            for row in sheet.iter_rows(min_row=2, min_col=visible.index("score") + 1, max_col=visible.index("score") + 1):
                row[0].number_format = "0.0000"
        column = next((i for i, name in enumerate(visible, 1)
                       if str(name).strip().casefold() == "affiliation"), None)
        if enabled and words and column is not None:
            green = PatternFill(fill_type="solid", fgColor="C6EFCE")
            for row in sheet.iter_rows(min_row=2, min_col=column, max_col=column):
                cell = row[0]
                text = str(cell.value).casefold() if cell.value is not None else ""
                if any(word in text for word in words):
                    cell.fill = green
