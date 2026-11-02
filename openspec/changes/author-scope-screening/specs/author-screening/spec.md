## ADDED Requirements
### Requirement: Author research input
The system SHALL require Email and Article and SHALL reject legacy-only reference inputs. Abstract and Keywords MAY enrich research text.
#### Scenario: Optional fields absent
- **WHEN** Email and Article are supplied
- **THEN** scoring succeeds without optional fields
### Requirement: Institution filter
The system SHALL offer disabled-by-default case-insensitive ANY keyword matching on Affiliation, independent of research scoring.
#### Scenario: Missing institution
- **WHEN** filtering is enabled and Affiliation is empty
- **THEN** the affiliation cell remains uncolored and research decisions remain unchanged
### Requirement: Traceable results
The system SHALL preserve rows and export research decisions, final decisions and settings, highlighting matched Affiliation cells green without match-status columns.
#### Scenario: Institution mismatch
- **WHEN** research is in scope but no institution keyword matches
- **THEN** the affiliation cell remains uncolored and the final result follows the research decision
