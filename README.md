# NEET-PG Admission Predictor

Student enters NEET-PG application number + category, sees their 2026 result, then gets
predicted Gujarat category merit and every Gujarat college/branch they can realistically get.

Status: v1, local only. `prototype/` holds the original throwaway analysis scripts (reference only).

## Run

    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
    # put the NBEMS result PDF at data/raw/nbems/NEET-PG 2026 Published Result_DS.pdf
    .venv/bin/python -m pipeline.build          # downloads other sources, writes web/data/
    .venv/bin/pytest                             # pipeline tests
    node --test web/engine.test.js web/engine.data.test.js
    cd web && python3 -m http.server 8000        # open http://localhost:8000

Needs poppler (`pdftotext`) and Node 20+ (tests only).

## Updating data

Change URLs or paths in `pipeline/sources.py` (for example when the 2026 Gujarat merit lists
are published), delete the old file from `data/raw/`, and rerun `.venv/bin/python -m pipeline.build`.

## Layout

- `prototype/` — analysis scripts (result parse, MCC/Gujarat PDF parsers, chance builder)
- `data/raw/` — source PDFs (NBEMS 2026 result, MCC 2024/2025, Gujarat ACPPGMEC 2025-26). Not committed.
- `data/interim/` — parsed pickles from the prototype. Not committed.
- `docs/` — design spec and plans

## Data sources

- NBEMS NEET-PG 2026 published result (PDF)
- MCC: 2024 final allotment Round 3 (R1-R3), 2025 stray round result — mcc.nic.in
- Gujarat ACPPGMEC 2025-26: last merit R1-R4, SEBC merit list, seats, fees — medadmgujarat.org

## Deploy (GitHub Pages)

    .venv/bin/python -m pipeline.publish          # builds site/ (web files + data, roll numbers removed)
    cd site && python3 -m http.server 8000         # optional local check
    .venv/bin/python -m pipeline.publish --push   # force-pushes site/ as a single commit to origin gh-pages

Then in GitHub: Settings → Pages → Deploy from a branch → `gh-pages` / root.
The published `results.json` contains every candidate's application number, score and rank.
