# NEET-PG Gujarat Admission Predictor — Design

Date: 2026-09-24
Status: draft, awaiting review

## Goal

A student enters their NEET-PG 2026 application number, category and Gujarat domicile.
The app shows their 2026 result, then, on request, predicts their Gujarat category merit
position and lists every Gujarat college/branch they can realistically get, with a chance
label, earliest round, fee and a plain-language reason.

Success: a student gets a correct, explained shortlist in under a minute without reading
any PDF. For candidate PG11111111 / SEBC / Gujarat domicile, the output matches the manual
report produced on 2026-09-24 (SEBC merit ~99, General merit ~510, same chance labels).

## Scope

In v1:
- Local only. No hosting, no accounts, no payments.
- Frontend-only app: static HTML/CSS/JS plus static JSON data, served with
  `python -m http.server`.
- Categories: General, EWS, SEBC/OBC, SC, ST.
- Gujarat domicile yes/no.
- Routes: Gujarat state quota (Govt Quota + Management Quota) and MCC seats in Gujarat
  colleges (All India 50%, Deemed, DNB).

Out of v1: PwD, NRI, in-service, institutional quota, other states, AFMS/minority/central
university quotas, hosting, backend.

## Architecture

Three units, each testable on its own:

```
pipeline/ (Python, offline)  ──writes──>  web/data/*.json  <──reads──  web/ (HTML + JS)
                                                                        ├─ engine.js (pure logic)
                                                                        └─ app.js    (UI)
```

1. **Pipeline** — downloads source PDFs, parses them, validates counts, writes JSON.
   Run manually when data changes. The only Python in the product.
2. **Engine** (`web/engine.js`) — pure functions, no DOM, no fetch. Input: rank, category,
   domicile, loaded data. Output: merit estimates and a list of options. Tested with
   `node --test` (no dependencies).
3. **App** (`web/app.js`, `index.html`, `styles.css`) — loads JSON, handles the form,
   renders result and prediction, exports CSV. No framework.

## Data sources

| Source | Used for |
|---|---|
| NBEMS NEET-PG 2026 published result PDF | application no → roll no, score, rank |
| Gujarat ACPPGMEC 2025-26 first merit lists: General, SEBC, SC, ST, EWS | AIR → Gujarat General merit and category merit |
| Gujarat ACPPGMEC 2025-26 last merit, Rounds 1–4 | last admitted merit per college × branch × seat type × category × round |
| Gujarat seat list and fee list 2025-26 | seats and annual tuition per college × branch × seat type |
| Gujarat institute-wise admitted list | college code → full name |
| MCC 2024 final allotment Round 3 (contains R1–R3) | last rank per college × course × quota × allotted category |
| MCC 2025 stray round result | same, stray round |

Source URLs live in one file, `pipeline/sources.py`, so a new year or round is a one-line change.

## Pipeline

Modules:
- `sources.py` — URL list and local paths under `data/raw/`.
- `fetch.py` — downloads missing files only.
- `parse_nbems.py` — result PDF → rows. Must yield 273,096 rows with unique S.No.;
  ABSENT/WITHHELD kept with null score/rank.
- `parse_gujarat.py` — merit lists (text regex), last merit tables (word coordinates,
  as in the prototype), seats, fees, code → name map.
- `parse_mcc.py` — MCC tables via pdfplumber, 8 worker processes.
- `build.py` — joins, normalises stream names, writes JSON, prints a validation report.

Validation (build fails if any check fails):
- NBEMS row count and unique application numbers.
- Every Gujarat last-merit college code has a name.
- Each category merit map is monotonic (higher AIR → higher merit).
- Spot checks: AMED Anaesthesiology R4 OPEN = 1102; AIR 8723 → SEBC merit 98.

Output files in `web/data/`:
- `results.json` — `{appNo: [rollNo, score, rank]}`, plus the score histogram used for
  percentiles. ~8 MB; compact arrays keep it small.
- `merit_map.json` — per category, sorted `[air, generalMerit, categoryMerit]` points.
- `gujarat.json` — one record per college × branch × seat type: name, code, type
  (Govt / Municipal / GMERS / Private), stream, degree, fee, and last merit per
  round × category.
- `mcc.json` — one record per Gujarat college × course × quota: last rank per
  eligible category.
- `meta.json` — data versions, source dates, build time.

## Engine

`estimateMerit(rank, category, meritMap)`
- Finds the two 2025 merit-list points around `rank` and returns General merit and
  category merit (linear interpolation, rounded). General category returns only
  General merit.

`gujaratOptions(merit, category, gujarat)` — only when domicile = yes
- Govt Quota seat: candidate competes on General merit against the OPEN last merit, and
  (if reserved category) on category merit against that category's last merit.
  The better ratio wins. Ratio = last merit ÷ candidate merit.
- Management Quota seat: OPEN last merit only.
- A value of 99999 in the source means the seat went vacant; treat it as reachable.
- Earliest round = first round whose ratio ≥ 1.

`mccOptions(rank, category, mcc)`
- Eligible allotments: Open seats plus the candidate's own category seats.
  Deemed seats have no reservation, so every allotment counts.
- Ratio = last eligible rank ÷ candidate rank.

Labels (both routes): High ≥ 1.15, Good ≥ 1.0, Borderline ≥ 0.9, else Low.

Every option carries a reason string, e.g.
`"Round 1 2025 last SEBC merit 132; your SEBC merit ~99"`.

`insights(options)`
- Count of options per stream × college type.
- Best Govt option per stream.
- Streams not reachable in Govt, with the gap (e.g. "Radiology at BJMC closed at SEBC merit 20").
- Fee range per stream.

Engine tests (`web/engine.test.js`, `node --test`):
- AIR 8839 SEBC → General ~510, SEBC ~99.
- SMIMER Dermatology GQ, SEBC 99 → High, Round 1.
- BJMC Radiology GQ, SEBC 99 → Low.
- General candidate never matched against SEBC last merit.
- Domicile = no → no Gujarat state quota options.
- Vacant seat (99999) → reachable.

## App

Single page, three steps:
1. **Form:** application number, category, domicile. Unknown number → clear error.
   ABSENT/WITHHELD → show status, no prediction.
2. **Result card:** score, AIR, percentiles (≤ score, < score, mid-rank, from rank),
   top %, candidates ahead, candidates with same score. Button "Predict my Gujarat options".
3. **Prediction:**
   - Merit estimate panel with a one-line explanation of how it was derived.
   - Insights panel.
   - Options table with filters: stream, college type, route, chance. Sorted Govt first,
     then by chance. Columns: stream, course, college, type, route, chance, earliest round,
     fee, reason.
   - Legend explaining High/Good/Borderline/Low.
   - "Download CSV" button (native Blob download, no library).
   - Disclaimer: estimates from 2025 state and 2024/2025 MCC cutoffs; not a guarantee;
     verify against the official 2026 merit list.

Loading: `results.json` is fetched once with a loading indicator. Everything else is small.

## Folder layout

```
neet-pg-predictor/
  pipeline/        sources.py fetch.py parse_*.py build.py
  web/             index.html styles.css app.js engine.js engine.test.js data/
  prototype/       existing throwaway scripts (reference only)
  data/raw/        downloaded PDFs (git-ignored)
  docs/
```

Run:
```
python -m pipeline.build          # regenerate web/data
node --test web/                  # engine tests
cd web && python -m http.server   # open http://localhost:8000
```

## Risks

- **Merit mapping assumes 2026 pool ≈ 2025.** Mitigation: show it as an estimate; when the
  2026 Gujarat merit lists are published, swap the source URL and rebuild.
- **PDF layouts change between years.** Mitigation: parser validation checks fail the build
  instead of producing silent bad data.
- **Small seat counts** (1–3 per category) make cutoffs volatile. Mitigation: show the
  per-round values in the reason, not only the label.
- **Data exposure:** `results.json` contains every candidate's score. Acceptable for
  local use; a public release needs a backend lookup.
