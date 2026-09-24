# NEET-PG Admission Predictor

Student enters NEET-PG application number + category, sees their 2026 result, then gets
predicted Gujarat category merit and every Gujarat college/branch they can realistically get.

Status: design phase. `prototype/` holds the throwaway analysis scripts that produced the
first manual report (candidate PG26114274, OBC). They use hard-coded scratch paths and are
reference only, not product code.

## Layout

- `prototype/` — analysis scripts (result parse, MCC/Gujarat PDF parsers, chance builder)
- `data/raw/` — source PDFs (NBEMS 2026 result, MCC 2024/2025, Gujarat ACPPGMEC 2025-26). Not committed.
- `data/interim/` — parsed pickles from the prototype. Not committed.
- `docs/` — design spec and plans

## Data sources

- NBEMS NEET-PG 2026 published result (PDF)
- MCC: 2024 final allotment Round 3 (R1-R3), 2025 stray round result — mcc.nic.in
- Gujarat ACPPGMEC 2025-26: last merit R1-R4, SEBC merit list, seats, fees — medadmgujarat.org
