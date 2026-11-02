## Context
Local React/FastAPI application.
## Goals / Non-Goals
Implement agreed author screening; no journal classification, country rules or history.
## Decisions
Require nonempty Email and Article. Optional Keywords/Abstract enrich research text. Affiliation is separate case-insensitive substring ANY matching, one keyword per line. Affiliation is visual-only: matching cells receive green fill; missing or unmatched affiliations do not affect decisions. No affiliation_result or affiliation_matches columns are exported. Score-only mode has no final scope decision. Persist settings in result columns. Keep row-level decisions, never merge authors by name. Reused scores must be finite in [-1,1].
## Risks / Trade-offs
Broad keywords can overmatch. Default thresholds require user calibration.
## Open Questions
None.

## User interface refinement
Models and request batch information are hidden. Batch sizes and delays are fixed server-side. The API Key field includes official Beijing-region onboarding guidance.

## Concise workbook output
Results retains input fields plus score, final_decision and screening_reason. Details holds per-record audit fields with original result_row and Email. Settings stores run parameters once. Scores retain precision for reuse; affiliation highlighting remains on Results.

## Calibration workflow
First-time users start with score-only export (original columns plus score). Manual review precedes explicit browser-local confirmation of the scope and thresholds. Existing-score review uses uploaded reviewed workbooks; next sessions default to full screening with the saved calibration. Workbook scope metadata is checked before score reuse.
