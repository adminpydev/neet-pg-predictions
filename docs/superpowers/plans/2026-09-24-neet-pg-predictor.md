# NEET-PG Gujarat Admission Predictor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Local, frontend-only web app: student enters application number, category and Gujarat domicile, sees their 2026 result, then gets predicted Gujarat merit and every reachable Gujarat college/branch with a chance, reason and fee.

**Architecture:** Offline Python pipeline parses source PDFs into static JSON under `web/data/`. A pure JavaScript engine (`web/engine.js`) turns rank + category + domicile into merit estimates and options. A plain HTML/JS page (`web/app.js`) loads the JSON, calls the engine and renders results.

**Tech Stack:** Python 3.14 + pdfplumber + pytest (pipeline); poppler `pdftotext` (text extraction); vanilla ES modules, Node 20 `node --test` (engine tests); `python -m http.server` (local serving).

**Spec:** `docs/superpowers/specs/2026-09-24-neet-pg-predictor-design.md`

## Global Constraints

- Local only. No backend, no hosting, no accounts.
- Frontend: plain HTML/CSS/JS, no framework, no npm dependencies.
- Categories (UI and all JSON keys): `GEN`, `EWS`, `SEBC`, `SC`, `ST`. Gujarat last-merit keys: `OPEN`, `EWS`, `SEBC`, `SC`, `ST`.
- Gujarat routes only when domicile = yes. MCC quotas in v1: All India 50% (`AI`), Deemed (`PS`), DNB (`AD`).
- Out of v1: PwD, NRI, in-service, institutional quota, other states.
- Chance labels: High ≥ 1.15, Good ≥ 1.0, Borderline ≥ 0.9, else Low. Ratio = last admitted merit (or rank) ÷ candidate merit (or rank).
- Source value `99999` in Gujarat last merit = seat went vacant = reachable.
- Raw PDFs live in `data/raw/` (git-ignored). Generated JSON in `web/data/` (git-ignored via `data/` rule).
- Commit messages: no AI attribution lines.

## Review Focus

1. Application number typed with spaces or lowercase (` pg11111111 `) → must still be found. Pinned in Task 9 (`normalizeAppNo`).
2. Unknown application number → clear "not found" message, no crash. Pinned in Task 9 (`lookup` returns `null`).
3. ABSENT / WITHHELD candidate → show status, no prediction. Pinned in Task 9 (`resultStats` status).
4. Rank beyond the 2025 merit list range (e.g. ST candidate rank 200000) → estimate with `extrapolated: true`, no NaN. Pinned in Task 10.
5. Round with no value for the candidate's category → skipped, never NaN ratio. Pinned in Task 11.

---

## File Structure

```
requirements.txt                 pdfplumber, pytest
pipeline/__init__.py             empty
pipeline/sources.py              paths + source URLs (one place to change year/round)
pipeline/fetch.py                download missing raw files
pipeline/pdftext.py              pdftotext wrapper
pipeline/streams.py              course name → stream / degree
pipeline/parse_nbems.py          NBEMS result text → rows
pipeline/parse_gujarat.py        Gujarat merit lists, last merit, names, fees, seats
pipeline/colleges.py             Gujarat college code → type
pipeline/parse_mcc.py            MCC allotment PDFs → Gujarat records
pipeline/build.py                orchestrate, validate, write web/data/*.json
tests/                           pytest tests per pipeline module
web/package.json                 {"type": "module"} for node tests
web/engine.js                    pure prediction logic
web/engine.test.js               unit tests
web/engine.data.test.js          end-to-end check against built data (skips if absent)
web/index.html, styles.css, app.js   UI
```

---

### Task 1: Pipeline scaffold, sources, fetch, pdftotext helper

**Files:**
- Modify: `requirements.txt`
- Create: `pipeline/__init__.py`, `pipeline/sources.py`, `pipeline/fetch.py`, `pipeline/pdftext.py`
- Test: `tests/test_fetch.py`

**Interfaces:**
- Produces: `sources.RAW`, `sources.OUT` (`Path`), `sources.SOURCES: dict[str, str | None]` (relative raw path → URL, `None` = manual), `sources.MERIT: dict[str, str]` (category → raw rel path), `sources.LAST_MERIT: dict[int, str]` (round → rel path), `sources.NBEMS`, `sources.MCC_R3`, `sources.MCC_STRAY`, `sources.GUJ_INST`, `sources.GUJ_SEATS`, `sources.GUJ_FEES` (rel paths); `fetch.fetch(sources=SOURCES, raw=RAW) -> list[str]` (missing manual files); `pdftext.pdftotext(path) -> str`.

- [ ] **Step 1: Set up venv and requirements**

`requirements.txt`:
```
pdfplumber
pytest
```
`pytest.ini` (so tests can `import pipeline` from the repo root):
```
[pytest]
pythonpath = .
testpaths = tests
```

Run: `python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt`

- [ ] **Step 2: Write failing test** — `tests/test_fetch.py`

```python
from pipeline.fetch import fetch


def test_manual_source_reported_missing(tmp_path):
    assert fetch({"nbems/result.pdf": None}, tmp_path) == ["nbems/result.pdf"]


def test_existing_file_not_downloaded(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "x.pdf").write_bytes(b"old")
    assert fetch({"a/x.pdf": "http://invalid.invalid/x.pdf"}, tmp_path) == []
    assert (tmp_path / "a" / "x.pdf").read_bytes() == b"old"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_fetch.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'pipeline'`

- [ ] **Step 4: Implement**

`pipeline/__init__.py`: empty file.

`pipeline/sources.py`:
```python
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "web" / "data"

GUJ = "http://medadmgujarat.ncode.in/web/PG2025/MDMS"
MCC = "https://cdnbbsr.s3waas.gov.in/s3e0f7a4d0ef9b84b83b693bbf3feb8e6e/uploads"

NBEMS = "nbems/NEET-PG 2026 Published Result_DS.pdf"
MCC_R3 = "mcc/r3_2024.pdf"
MCC_STRAY = "mcc/stray.pdf"
GUJ_INST = "gujarat/inst.pdf"
GUJ_SEATS = "gujarat/seats.pdf"
GUJ_FEES = "gujarat/fees.pdf"
MERIT = {"GEN": "gujarat/gen0.pdf", "SEBC": "gujarat/se0.pdf", "SC": "gujarat/sc0.pdf",
         "ST": "gujarat/st0.pdf", "EWS": "gujarat/ew0.pdf"}
LAST_MERIT = {1: "gujarat/r1_last_merit_xyz1.pdf", 2: "gujarat/r2_last_merit_22122025.pdf",
              3: "gujarat/r3_last_merit_1.pdf", 4: "gujarat/r4_last_merit.pdf"}

SOURCES = {
    NBEMS: None,  # downloaded manually from NBEMS
    MCC_R3: f"{MCC}/2025/01/2025012533.pdf",
    MCC_STRAY: f"{MCC}/2026/02/20260223177387794.pdf",
    GUJ_INST: f"{GUJ}/inst_branchwise_adm_07042026.pdf",
    GUJ_SEATS: f"{GUJ}/PG%20MD%20MS%20SEATS%202025-26.pdf",
    GUJ_FEES: f"{GUJ}/PG%20MD%20MS%20FEES%202025-26.pdf",
    MERIT["GEN"]: f"{GUJ}/MERIT/mdms_gen_merit.pdf",
    MERIT["SEBC"]: f"{GUJ}/MERIT/mdms_se_merit.pdf",
    MERIT["SC"]: f"{GUJ}/MERIT/mdms_sc_merit.pdf",
    MERIT["ST"]: f"{GUJ}/MERIT/mdms_st_merit.pdf",
    MERIT["EWS"]: f"{GUJ}/MERIT/mdms_ew_merit.pdf",
    LAST_MERIT[1]: f"{GUJ}/R1/r1_last_merit_xyz1.pdf",
    LAST_MERIT[2]: f"{GUJ}/R2/r2_last_merit_22122025.pdf",
    LAST_MERIT[3]: f"{GUJ}/R3/r3_last_merit_1.pdf",
    LAST_MERIT[4]: f"{GUJ}/R4/r4_last_merit.pdf",
}
```

`pipeline/fetch.py`:
```python
import urllib.request

from pipeline.sources import RAW, SOURCES


def fetch(sources=SOURCES, raw=RAW):
    """Download missing files. Returns manual sources that are still missing."""
    missing = []
    for rel, url in sources.items():
        path = raw / rel
        if path.exists():
            continue
        if url is None:
            missing.append(rel)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=300) as resp:
            path.write_bytes(resp.read())
    return missing
```

`pipeline/pdftext.py`:
```python
import subprocess


def pdftotext(path):
    return subprocess.run(["pdftotext", "-layout", str(path), "-"],
                          check=True, capture_output=True, text=True).stdout
```

- [ ] **Step 5: Run tests**

Run: `.venv/bin/pytest tests/test_fetch.py -v`
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add requirements.txt pytest.ini pipeline tests
git commit -m "feat(pipeline): add sources, fetch and pdftotext helper"
```

---

### Task 2: Stream and degree normalisation

**Files:**
- Create: `pipeline/streams.py`
- Test: `tests/test_streams.py`

**Interfaces:**
- Produces: `stream_of(course: str) -> str` (canonical stream or `"Other"`), `degree_of(course: str) -> str` (`"MD"`, `"MS"`, `"MD/MS"`, `"Diploma"`, `"DNB"`, `"DNB Diploma"`).

- [ ] **Step 1: Write failing test** — `tests/test_streams.py`

```python
import pytest

from pipeline.streams import degree_of, stream_of


@pytest.mark.parametrize("course,stream", [
    ("M.D. (RADIO- DIAGNOSIS)", "Radio-Diagnosis"),
    ("Radio Diagnosis", "Radio-Diagnosis"),
    ("Dermatology ,Venereology & Leprosy", "Dermatology"),
    ("M.D. (DERM.,VENE. and LEPROSY)/ (DERMATOLOGY)", "Dermatology"),
    ("General Medicine (DNB)", "General Medicine"),
    ("Diploma in Anesthesiology (D.A.)", "Anaesthesiology"),
    ("M.D. (ANAESTHESIOLOGY )", "Anaesthesiology"),
    ("Diploma in Paediatrics (D.C.H.)", "Paediatrics"),
    ("(NBEMS) Paediatric Surgery (Direct 6 Years Course)", "Paediatric Surgery"),
    ("Otorhinolaryngology/ENT", "ENT"),
    ("Tuberculosis & Respiratory Medicine", "Respiratory Medicine"),
    ("Radiation oncology", "Radiation Oncology"),
    ("Immuno Haematology & Blood Transfusion", "Transfusion Medicine (IHBT)"),
    ("M.D. (COMMUNITY HEALTH and ADMN.)", "Hospital Administration"),
    ("M.D. (PREVENTIVE and SOCIAL MEDICINE)/ COMMUNITY MEDICINE", "Community Medicine"),
    ("Obstetrics & Gynaecology", "Obstetrics & Gynaecology"),
    ("Something New", "Other"),
])
def test_stream_of(course, stream):
    assert stream_of(course) == stream


@pytest.mark.parametrize("course,degree", [
    ("(NBEMS-DIPLOMA) PAEDIATRICS", "DNB Diploma"),
    ("(NBEMS) GENERAL MEDICINE", "DNB"),
    ("General Medicine (DNB)", "DNB"),
    ("DIPLOMA IN ANAESTHESIOLOGY", "Diploma"),
    ("Diploma in Paediatrics (D.C.H.)", "Diploma"),
    ("M.S. (ORTHOPAEDICS)", "MS"),
    ("M.D. (Obst. and Gynae)/MS (Obstetrics and Gynaecology)", "MD/MS"),
    ("M.D. (GENERAL MEDICINE)", "MD"),
    ("Anaesthesiology", "MD"),
])
def test_degree_of(course, degree):
    assert degree_of(course) == degree
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_streams.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'pipeline.streams'`

- [ ] **Step 3: Implement** — `pipeline/streams.py`

```python
import re

# Ordered: first matching key wins. Keys are matched against the course name
# upper-cased with all whitespace removed.
STREAMS = [
    ("PAEDIATRICSURGERY", "Paediatric Surgery"), ("RADIO-DIAG", "Radio-Diagnosis"),
    ("RADIODIAG", "Radio-Diagnosis"), ("DERM", "Dermatology"),
    ("GENERALMEDICINE", "General Medicine"), ("GENERALSURGERY", "General Surgery"),
    ("PAEDIATRIC", "Paediatrics"), ("CHILDHEALTH", "Paediatrics"), ("D.C.H", "Paediatrics"),
    ("ORTHO", "Orthopaedics"), ("GYN", "Obstetrics & Gynaecology"),
    ("OBSTETRIC", "Obstetrics & Gynaecology"), ("ANAES", "Anaesthesiology"),
    ("ANES", "Anaesthesiology"), ("OPHTHAL", "Ophthalmology"), ("E.N.T", "ENT"), ("OTO", "ENT"),
    ("PSYCH", "Psychiatry"), ("RESPIRATORY", "Respiratory Medicine"),
    ("PULMONARY", "Respiratory Medicine"), ("CHEST", "Respiratory Medicine"),
    ("EMERGENCY", "Emergency Medicine"), ("RADIOTHERAPY", "Radiation Oncology"),
    ("RADIO-THERAPY", "Radiation Oncology"), ("RADIATION", "Radiation Oncology"),
    ("PATHOLOGY", "Pathology"), ("MICROBIO", "Microbiology"), ("BACTERIO", "Microbiology"),
    ("PHARMAC", "Pharmacology"), ("PHYSIOLOGY", "Physiology"), ("BIOCHEM", "Biochemistry"),
    ("ANATOMY", "Anatomy"), ("FORENSIC", "Forensic Medicine"),
    ("COMMUNITYHEALTHANDADMN", "Hospital Administration"),
    ("HOSPITALADMIN", "Hospital Administration"), ("HEALTHADMIN", "Hospital Administration"),
    ("COMMUNITY", "Community Medicine"), ("PREVENTIVE", "Community Medicine"),
    ("PUBLICHEALTH", "Community Medicine"), ("EPIDEM", "Community Medicine"),
    ("FAMILYMEDICINE", "Family Medicine"), ("TRANSFUSION", "Transfusion Medicine (IHBT)"),
    ("NUCLEAR", "Nuclear Medicine"), ("PALLIATIVE", "Palliative Medicine"),
    ("GERIATRIC", "Geriatrics"), ("SPORTS", "Sports Medicine"), ("PHYSICALMED", "PMR"),
    ("PHY.MEDICINE", "PMR"), ("TRAUMATOLOGY", "Traumatology & Surgery"),
    ("NEUROSURGERY", "Neuro Surgery (6 yr)"), ("CARDIOVASCULAR", "CTVS (6 yr)"),
    ("PLASTIC", "Plastic Surgery (6 yr)"), ("DIABETOLOGY", "Diabetology"),
    ("TROPICAL", "Tropical Medicine"), ("AEROSPACE", "Aerospace Medicine"),
    ("LABORATORY", "Laboratory Medicine"),
]


def stream_of(course):
    key = re.sub(r"\s", "", course.upper())
    return next((name for k, name in STREAMS if k in key), "Other")


def degree_of(course):
    if "(NBEMS-DIPLOMA)" in course:
        return "DNB Diploma"
    if "(NBEMS)" in course or "(DNB)" in course:
        return "DNB"
    if re.match(r"(PG )?DIP", course, re.I):
        return "Diploma"
    if course.startswith("M.S"):
        return "MS"
    if "MS (" in course or course.startswith("MD/MS"):
        return "MD/MS"
    return "MD"
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/pytest tests/test_streams.py -v`
Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add pipeline/streams.py tests/test_streams.py
git commit -m "feat(pipeline): add stream and degree normalisation"
```

---

### Task 3: NBEMS result parser

**Files:**
- Create: `pipeline/parse_nbems.py`
- Test: `tests/test_parse_nbems.py`

**Interfaces:**
- Consumes: text from `pdftext.pdftotext`.
- Produces: `parse_results(text) -> list[dict]`, each `{"sno": int, "app": str, "roll": str, "score": int | None, "rank": int | None, "status": "OK" | "ABSENT" | "WITHHELD"}`.

- [ ] **Step 1: Write failing test** — `tests/test_parse_nbems.py`

```python
from pipeline.parse_nbems import parse_results

TEXT = """
                          NATIONAL BOARD OF EXAMINATIONS
    1             PG26120268                 26661000001                   331                   88859
  219038          PG26083665                 26661219410                   WITHHELD           WITHHELD
  273076          PG26215715                 26664248775                   ABSENT               ABSENT
  273088          PG26247319                 26664270202                     -14                265921
"""


def test_parse_results():
    rows = parse_results(TEXT)
    assert [r["sno"] for r in rows] == [1, 219038, 273076, 273088]
    assert rows[0] == {"sno": 1, "app": "PG26120268", "roll": "26661000001",
                       "score": 331, "rank": 88859, "status": "OK"}
    assert rows[1]["status"] == "WITHHELD" and rows[1]["score"] is None and rows[1]["rank"] is None
    assert rows[2]["status"] == "ABSENT"
    assert rows[3]["score"] == -14
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_parse_nbems.py -v`
Expected: FAIL, `ModuleNotFoundError`

- [ ] **Step 3: Implement** — `pipeline/parse_nbems.py`

```python
import re

ROW = re.compile(r"(\d+)\s+(PG\d{8})\s+(\d{11})\s+(-?\d+|ABSENT|WITHHELD)\s+(\d+|ABSENT|WITHHELD)")


def parse_results(text):
    rows = []
    for sno, app, roll, score, rank in ROW.findall(text):
        ok = score not in ("ABSENT", "WITHHELD")
        rows.append({"sno": int(sno), "app": app, "roll": roll,
                     "score": int(score) if ok else None,
                     "rank": int(rank) if ok else None,
                     "status": "OK" if ok else score})
    return rows
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/pytest tests/test_parse_nbems.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add pipeline/parse_nbems.py tests/test_parse_nbems.py
git commit -m "feat(pipeline): parse NBEMS result rows"
```

---

### Task 4: Gujarat merit list parser

**Files:**
- Create: `pipeline/parse_gujarat.py`
- Test: `tests/test_parse_gujarat_merit.py`

**Interfaces:**
- Produces: `parse_merit(text) -> list[tuple[int, int, float | None]]` = `(air, general_merit, category_merit)` in list order (AIR ascending). `category_merit` is `None` for rows with no category column.

- [ ] **Step 1: Write failing test** — `tests/test_parse_gujarat_merit.py`

```python
from pipeline.parse_gujarat import parse_merit

TEXT = """
 User ID Roll No       GEN       CAT        Uni.       Uni.Cat  All India      Score   NAME
   40377 25661005088   0001                 MS-0001                     17     683   F AGRAWAL HIRAK KESHAV             GOVT. MEDICAL COLLEGE BARODA
   44945 25661238018   1162.50   SE-241.5   SU-169.7   SE-039.5     19838.00     516   M BADMALIYA AJAYKUMAR MAHESHBHAI      P. D. U. GOVT. MEDICAL COLLEGE RAJKOT
   44488 25661224006   0057     SC-001.0    SU-0005   SC-001.0          895     629   M BADHIYA HITESHKUMAR PURABHAI     P. D. U. GOVT. MEDICAL COLLEGE RAJKOT
   40504 25661085097   0300                SPU-0001                    5321     581   M DSYLVA MIT PARIKSHAT             NOOTAN MEDICAL COLLEGE
"""


def test_parse_merit():
    assert parse_merit(TEXT) == [(17, 1, None), (19838, 1162, 241.5), (895, 57, 1.0), (5321, 300, None)]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_parse_gujarat_merit.py -v`
Expected: FAIL, `ModuleNotFoundError`

- [ ] **Step 3: Implement** — create `pipeline/parse_gujarat.py`

```python
import re

MERIT_ROW = re.compile(
    r"^\s*\d{5}\s+2566\d{7}\s+([\d.]+)\s+(?:(?:SE|SC|ST|EW)-([\d.]+)\s+)?\S+\s+"
    r"(?:(?:SE|SC|ST|EW)-[\d.]+\s+)?([\d.]+)\s+-?\d+\s")


def parse_merit(text):
    rows = []
    for line in text.splitlines():
        m = MERIT_ROW.match(line)
        if m:
            gen, cat, air = m.groups()
            rows.append((int(float(air)), int(float(gen)), float(cat) if cat else None))
    return rows
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/pytest tests/test_parse_gujarat_merit.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add pipeline/parse_gujarat.py tests/test_parse_gujarat_merit.py
git commit -m "feat(pipeline): parse Gujarat category merit lists"
```

---

### Task 5: Gujarat last-merit table parser

The last-merit PDFs have no ruled table. Values are placed by x position under a header row
`College OPEN EWS SC ST SE OPEN …` (Government / Institutional / In-service seat groups).
A course name line starts at x0 < 85, a row of numbers is followed by its college code line.

**Files:**
- Modify: `pipeline/parse_gujarat.py`
- Test: `tests/test_parse_gujarat_last.py`

**Interfaces:**
- Produces: `last_merit_rows(pages) -> list[dict]` where `pages` is a list of pages, each a list of pdfplumber-style word dicts `{"text", "x0", "x1", "top"}`. Each output row: `{"course": str, "code": str, "values": {"GQ_OPEN": float, ...}}` with column keys `f"{group}_{cat}"`, group in `GQ, INST, INSV`, cat in `OPEN, EWS, SC, ST, SE`. `read_last_merit(path) -> list[dict]` (same rows from a PDF path).

- [ ] **Step 1: Write failing test** — `tests/test_parse_gujarat_last.py`

```python
from pipeline.parse_gujarat import last_merit_rows


def w(text, x0, x1, top):
    return {"text": text, "x0": x0, "x1": x1, "top": top}


HEADER = [w("College", 84, 125, 100)] + [
    w(t, x1 - 25, x1, 100) for t, x1 in zip(
        "OPEN EWS SC ST SE OPEN EWS SC ST SE OPEN EWS SC ST SE".split(),
        [234, 278, 318, 358, 399, 447, 486, 510, 547, 584, 648, 684, 720, 756, 792])]

PAGE = HEADER + [
    w("Anaesthesiology", 78, 170, 128),
    w("*", 72, 79, 143), w("1102", 209, 234, 143), w("392", 259, 278, 143), w("396", 380, 399, 143),
    w("AMED", 90, 119, 149),
    w("99999", 202, 234, 169),
    w("BHUMED-MQ", 90, 155, 175),
]


def test_last_merit_rows():
    rows = last_merit_rows([PAGE])
    assert rows == [
        {"course": "Anaesthesiology", "code": "AMED", "values": {"GQ_OPEN": 1102.0, "GQ_EWS": 392.0, "GQ_SE": 396.0}},
        {"course": "Anaesthesiology", "code": "BHUMED-MQ", "values": {"GQ_OPEN": 99999.0}},
    ]


def test_page_without_header_ignored():
    assert last_merit_rows([[w("Anaesthesiology", 78, 170, 128)]]) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_parse_gujarat_last.py -v`
Expected: FAIL, `ImportError: cannot import name 'last_merit_rows'`

- [ ] **Step 3: Implement** — append to `pipeline/parse_gujarat.py`

```python
import pdfplumber

LAST_COLS = [f"{g}_{c}" for g in ("GQ", "INST", "INSV") for c in ("OPEN", "EWS", "SC", "ST", "SE")]
NUM = re.compile(r"[\d.]+")


def last_merit_rows(pages):
    out, course = [], None
    for words in pages:
        lines = {}
        for word in words:
            lines.setdefault(round(word["top"]), []).append(word)
        header = next((ws for ws in lines.values() if [x["text"] for x in ws][:2] == ["College", "OPEN"]), None)
        if not header:
            continue
        xs = [x["x1"] for x in header[1:]]
        pending = None
        for top in sorted(lines):
            ws = [x for x in lines[top] if x["text"] != "*"]
            if not ws or top <= header[0]["top"]:
                continue
            if all(NUM.fullmatch(x["text"]) for x in ws):
                pending = {LAST_COLS[min(range(len(xs)), key=lambda i: abs(xs[i] - x["x1"]))]: float(x["text"])
                           for x in ws}
            elif ws[0]["x0"] < 85:
                course, pending = " ".join(x["text"] for x in ws), None
            elif pending is not None:
                out.append({"course": course, "code": " ".join(x["text"] for x in ws), "values": pending})
                pending = None
    return out


def read_last_merit(path):
    with pdfplumber.open(path) as pdf:
        return last_merit_rows([page.extract_words() for page in pdf.pages])
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/pytest tests/test_parse_gujarat_last.py -v`
Expected: 2 passed

- [ ] **Step 5: Check against the real Round 4 PDF**

Run:
```bash
.venv/bin/python -c "
from pipeline.parse_gujarat import read_last_merit
rows = read_last_merit('data/raw/gujarat/r4_last_merit.pdf')
print(len(rows)); print([r for r in rows if r['code'] == 'AMED' and r['course'] == 'Anaesthesiology'])"
```
Expected: about 866 rows; the AMED row has `GQ_OPEN: 1102.0`, `GQ_EWS: 392.0`, `GQ_SE: 396.0`.

- [ ] **Step 6: Commit**

```bash
git add pipeline/parse_gujarat.py tests/test_parse_gujarat_last.py
git commit -m "feat(pipeline): parse Gujarat last-merit tables by word position"
```

---

### Task 6: Gujarat college names, types, fees and seats

**Files:**
- Modify: `pipeline/parse_gujarat.py`
- Create: `pipeline/colleges.py`
- Test: `tests/test_parse_gujarat_meta.py`

**Interfaces:**
- Produces:
  - `parse_names(text, codes: set[str]) -> dict[str, str]` — code → full name, from the institute-wise admitted list.
  - `parse_fees(text) -> list[tuple[str, str, int | None, int | None]]` — `(college_header, branch, fee_gq, fee_mq)`.
  - `parse_seats(text) -> list[tuple[str, str, int, int]]` — `(college_header, branch, gq, mq)`.
  - `norm(s) -> str` — lowercase alphanumerics only.
  - `branch_key(s) -> str` — `norm` after dropping a leading `MD-`/`MS-` and a trailing `(DNB)`.
  - `match_college(header: str, names: dict[str, str]) -> str | None` — code whose name's first 30 normalised chars occur in the header.
  - `colleges.type_of(code) -> str` — `"Govt"`, `"Municipal (Govt)"`, `"GMERS (Govt society)"` or `"Private"`.

- [ ] **Step 1: Write failing test** — `tests/test_parse_gujarat_meta.py`

```python
from pipeline.colleges import type_of
from pipeline.parse_gujarat import branch_key, match_college, parse_fees, parse_names, parse_seats

INST = """
001     AMED         B. J. Medical college, Ahmedabad
Anaesthesiology
1     F HETA KIRITBHAI SOMAIYA                782       EW 235
012     NAMOMED
                 Narendra Modi Medical College, Ahmedabad
123   PATEL FENIL                             1561
"""

FEES = """
                   Branch
                                                          B. J. Medical college, Ahmedabad
                                                  TUTION FEE GQ TUTION FEE MQ TUTION FEE NQ
MD-Anaesthesiology                                        130800 -                  -
                                                  Parul Institute Of Medical Sciences & Research, Post.
                      Branch                        Limda, Dist. Parul Institute Of Medical Sciences &
                                                          Research, Post. Limda, Dist. Vadodara
                                                  TUTION FEE GQ TUTION FEE MQ TUTION FEE NQ
MD-Anaesthesiology                                        1000000             1500000           1500000
"""

SEATS = """
                                                                B. J. Medical college, Ahmedabad
Branch                                                SANCTION_SEAT CURR_YR_SEAT AIQ GQ MQ NRI TOTAL
MD-Anaesthesiology                                               65           65 32 33   0   0    65
"""


def test_parse_names_only_known_codes():
    names = parse_names(INST, {"AMED", "NAMOMED"})
    assert names == {"AMED": "B. J. Medical college, Ahmedabad",
                     "NAMOMED": "Narendra Modi Medical College, Ahmedabad"}


def test_parse_fees():
    rows = parse_fees(FEES)
    assert rows[0][1:] == ("MD-Anaesthesiology", 130800, None)
    assert rows[1][1:] == ("MD-Anaesthesiology", 1000000, 1500000)
    assert "Parul Institute" in rows[1][0]


def test_parse_seats():
    assert parse_seats(SEATS) == [("B. J. Medical college, Ahmedabad", "MD-Anaesthesiology", 33, 0)]


def test_match_college_and_branch_key():
    names = {"AMED": "B. J. Medical college, Ahmedabad",
             "PRMED": "Parul Institute Of Medical Sciences & Research, Post. Limda, Dist. Vadodara"}
    assert match_college(parse_fees(FEES)[1][0], names) == "PRMED"
    assert match_college("Unknown College", names) is None
    assert branch_key("MD-Dermatology Venereology & Leprosy") == branch_key("Dermatology ,Venereology & Leprosy")
    assert branch_key("General Medicine (DNB)") == branch_key("MD-General Medicine")


def test_type_of():
    assert type_of("AMED") == "Govt"
    assert type_of("SMC") == "Municipal (Govt)"
    assert type_of("SOLMED") == "GMERS (Govt society)"
    assert type_of("PRMED") == "Private"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_parse_gujarat_meta.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'pipeline.colleges'`

- [ ] **Step 3: Implement**

`pipeline/colleges.py`:
```python
GOVT = {"AMED", "BMED", "SMED", "RMED", "JMED", "BHMED", "IKDMED"}
MUNICIPAL = {"NHL", "SMC", "NAMOMED"}
GMERS = {"GOTMED", "SOLMED", "GMED", "PATMED", "VALMED", "HIMMED", "JUMED", "VADMED", "PORMED", "MORMED"}


def type_of(code):
    if code in GOVT:
        return "Govt"
    if code in MUNICIPAL:
        return "Municipal (Govt)"
    if code in GMERS:
        return "GMERS (Govt society)"
    return "Private"
```

Append to `pipeline/parse_gujarat.py`:
```python
CODE_LINE = re.compile(r"^\s*\d{3}\s+([A-Z]+)\s*(.*?)\s*$")
FEE_ROW = re.compile(r"^(\S.*?)\s{2,}(\d+|-)\s+(\d+|-)\s+(\d+|-)$")
SEAT_ROW = re.compile(r"^(\S.*?)\s{2,}(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$")


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def branch_key(s):
    return norm(re.sub(r"\s*\(DNB\)\s*$", "", re.sub(r"^(MD|MS)-", "", s.strip())))


def parse_names(text, codes):
    names, lines = {}, text.splitlines()
    for i, line in enumerate(lines):
        m = CODE_LINE.match(line)
        if not m or m.group(1) not in codes:
            continue
        name = m.group(2) or next((x.strip() for x in lines[i + 1:] if x.strip()), "")
        if len(name) > len(names.get(m.group(1), "")):
            names[m.group(1)] = name
    return names


def _college_tables(text, row_re, header_marker):
    """Yield (college_header, match) for each table row. The header is the text seen
    since the previous row, up to the column-header line."""
    buffer, header = [], ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = row_re.match(line)
        if m:
            buffer = []
            yield header, m
        elif header_marker in line:
            header = re.sub(r"\s+", " ", " ".join(buffer).replace("Branch", " ")).strip()
            buffer = []
        else:
            buffer.append(line)


def parse_fees(text):
    num = lambda v: int(v) if v.isdigit() else None
    return [(h, m.group(1), num(m.group(2)), num(m.group(3))) for h, m in _college_tables(text, FEE_ROW, "TUTION FEE")]


def parse_seats(text):
    return [(h, m.group(1), int(m.group(5)), int(m.group(6))) for h, m in _college_tables(text, SEAT_ROW, "SANCTION_SEAT")]


def match_college(header, names):
    h = norm(header)
    return next((code for code, name in names.items() if norm(name)[:30] in h), None)
```

Note for `parse_seats`: the college name sits on the line *above* the `Branch SANCTION_SEAT …` header line, so the header line itself carries the marker and the buffer holds the name — same flow as fees.

- [ ] **Step 4: Run tests**

Run: `.venv/bin/pytest tests/test_parse_gujarat_meta.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add pipeline/colleges.py pipeline/parse_gujarat.py tests/test_parse_gujarat_meta.py
git commit -m "feat(pipeline): parse Gujarat college names, fees, seats and types"
```

---

### Task 7: MCC allotment parser

**Files:**
- Create: `pipeline/parse_mcc.py`
- Test: `tests/test_parse_mcc.py`

**Interfaces:**
- Produces:
  - `round3_allotments(rows) -> list[dict]` — from Round 3 table rows (16 or 17 cells). One dict per round with an allotment: `{"round": "2024 R1", "rank": int, "quota": str, "inst": str, "course": str, "cat": str, "cand": str}`. `cat` is the allotted category (known only for R3, `""` otherwise); `cand` is the candidate category (`"-"` if unknown).
  - `stray_allotments(rows) -> list[dict]` — same shape from the 8-cell stray table, `round = "2025 Stray"`, quota mapped to 2-letter code.
  - `gujarat_records(allotments) -> list[dict]` — Gujarat colleges only, quotas `AI`/`PS`/`AD` only. Each: `{"college", "stream", "course", "degree", "quota", "sector", "rounds": [str], "last": {"GEN": int|None, "EWS", "SEBC", "SC", "ST"}}`.
  - `read_tables(path) -> list[list[str]]` — all numeric-first-cell table rows from a PDF, cells newline-joined to spaces.

- [ ] **Step 1: Write failing test** — `tests/test_parse_mcc.py`

```python
from pipeline.parse_mcc import gujarat_records, round3_allotments, stray_allotments

BJ = "B. J. MEDICAL COLLEGE,Asarwa, Ahmedabad, Gujarat, 380016"
R3_ROWS = [
    # rank q1 i1 c1 rem1 q2 i2 c2 rem2 q3 i3 c3 cat_allot cat_cand opt remarks
    ["9000", "AI", "B. J. MEDICAL COLLEGE", "M.S. (GENERAL SURGERY)", "Reported", "-", "-", "-", "-",
     "-", "-", "-", "-", "-", "-", "Did not opt"],
    ["12000", "-", "-", "-", "-", "-", "-", "-", "-",
     "AI", BJ, "M.S. (GENERAL SURGERY)", "OBC", "OBC", "2", "Fresh Allotted"],
    ["15000", "-", "-", "-", "-", "-", "-", "-", "-",
     "AI", BJ, "M.S. (GENERAL SURGERY)", "SC", "SC", "3", "Fresh Allotted"],
    ["20000", "PS", "KMC MANIPAL", "M.D. (PAEDIATRICS)", "Reported", "-", "-", "-", "-",
     "-", "-", "-", "-", "-", "-", "Did not opt"],
]
STRAY_ROWS = [["1", "30000", "All India", BJ, "M.S. (GENERAL SURGERY)", "Open", "General", "Allotted"],
              ["2", "40000", "Armed Forces Medical", BJ, "M.S. (GENERAL SURGERY)", "Open", "General", "Allotted"]]


def test_round3_allotments():
    a = round3_allotments(R3_ROWS)
    assert a[0] == {"round": "2024 R1", "rank": 9000, "quota": "AI", "inst": "B. J. MEDICAL COLLEGE",
                    "course": "M.S. (GENERAL SURGERY)", "cat": "", "cand": "-"}
    assert a[1]["round"] == "2024 R3" and a[1]["cat"] == "OBC"


def test_seventeen_cell_rows_drop_empty_column():
    row = R3_ROWS[1][:10] + [None] + R3_ROWS[1][10:]
    assert round3_allotments([row])[0]["inst"] == BJ


def test_gujarat_records_last_rank_per_category():
    recs = gujarat_records(round3_allotments(R3_ROWS) + stray_allotments(STRAY_ROWS))
    assert len(recs) == 1  # KMC Manipal is not in Gujarat; Armed Forces quota excluded
    r = recs[0]
    assert r["quota"] == "AI" and r["sector"] == "Govt" and r["stream"] == "General Surgery"
    assert r["last"] == {"GEN": 30000, "EWS": 30000, "SEBC": 30000, "SC": 30000, "ST": 30000}


def test_reserved_seats_only_count_for_their_category():
    recs = gujarat_records(round3_allotments(R3_ROWS))
    assert recs[0]["last"] == {"GEN": None, "EWS": None, "SEBC": 12000, "SC": 15000, "ST": None}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_parse_mcc.py -v`
Expected: FAIL, `ModuleNotFoundError`

- [ ] **Step 3: Implement** — `pipeline/parse_mcc.py`

```python
import re
from multiprocessing import Pool

import pdfplumber

from pipeline.streams import degree_of, stream_of

QUOTA_CODE = {"All India": "AI", "DNB Quota": "AD", "Self-Financed Merit Seat": "PS", "Non-Resident Indian": "NR",
              "Delhi University Quota": "DU", "Armed Forces Medical": "AF", "IP University Quota": "IP",
              "Muslim Minority Quota": "MM", "Aligarh Muslim University": "AM", "Banaras Hindu University": "BH",
              "Jain Minority Quota": "JM"}
QUOTAS = {"AI": ("All India 50%", "Govt"), "PS": ("Deemed", "Private (Deemed)"), "AD": ("DNB", "DNB Hospital")}
# UI category -> (allotted seat category, candidate category) that the candidate can compete for
MCC_CAT = {"GEN": "General", "EWS": "EWS", "SEBC": "OBC", "SC": "SC", "ST": "ST"}
STATE = re.compile(r",\s*([A-Za-z .()&]+?)\s*,?\s*(\d{6})\s*$")


def round3_allotments(rows):
    out = []
    for r in rows:
        r = list(r)
        if len(r) == 17:
            del r[10]
        rank, cand = int(r[0]), r[13]
        for n, (q, i, c) in enumerate([(1, 2, 3), (5, 6, 7), (9, 10, 11)], 1):
            if r[q] in ("-", "") or not r[i] or not r[c] or r[i] == "-":
                continue
            out.append({"round": f"2024 R{n}", "rank": rank, "quota": r[q], "inst": r[i], "course": r[c],
                        "cat": r[12] if n == 3 else "", "cand": cand})
    return out


def stray_allotments(rows):
    return [{"round": "2025 Stray", "rank": int(r[1]), "quota": QUOTA_CODE.get(r[2], r[2]), "inst": r[3],
             "course": r[4], "cat": r[5], "cand": r[6]} for r in rows if r[3] and r[4]]


def _key(inst):
    return re.sub(r"[^A-Z0-9 ]", "", re.sub(r"\s+", " ", inst.split(",")[0].upper())).strip()


def _eligible(a, category):
    if a["quota"] == "PS":  # deemed seats have no reservation
        return True
    own = MCC_CAT[category]
    return a["cat"] in ("Open", own) or a["cand"] in ("General", own)


def gujarat_records(allotments):
    states, names = {}, {}
    for a in allotments:
        k = _key(a["inst"])
        m = STATE.search(a["inst"])
        if m:
            states.setdefault(k, m.group(1).strip())
        if len(a["inst"]) > len(names.get(k, "")):
            names[k] = a["inst"]
    groups = {}
    for a in allotments:
        k = _key(a["inst"])
        if a["quota"] in QUOTAS and states.get(k) == "Gujarat":
            groups.setdefault((k, a["course"], a["quota"]), []).append(a)
    records = []
    for (k, course, quota), items in groups.items():
        last = {}
        for cat in MCC_CAT:
            ranks = [a["rank"] for a in items if _eligible(a, cat)]
            last[cat] = max(ranks) if ranks else None
        records.append({"college": names[k].split(",")[0].strip().title(), "stream": stream_of(course),
                        "course": course, "degree": degree_of(course), "quota": QUOTAS[quota][0],
                        "sector": QUOTAS[quota][1], "rounds": sorted({a["round"] for a in items}), "last": last})
    return records


def _page_rows(args):
    path, start, stop = args
    out = []
    with pdfplumber.open(path) as pdf:
        for i in range(start, stop):
            for r in pdf.pages[i].extract_table() or []:
                if r and (r[0] or "").strip().isdigit():
                    out.append([(c or "").replace("\n", " ").strip() if c is not None else None for c in r])
    return out


def read_tables(path, step=50):
    with pdfplumber.open(path) as pdf:
        n = len(pdf.pages)
    with Pool(8) as pool:
        chunks = pool.map(_page_rows, [(path, a, min(a + step, n)) for a in range(0, n, step)])
    return [r for chunk in chunks for r in chunk]
```

Note: `read_tables` keeps `None` cells so the 17-cell Round 3 rows can drop their empty column in `round3_allotments`.

- [ ] **Step 4: Run tests**

Run: `.venv/bin/pytest tests/test_parse_mcc.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add pipeline/parse_mcc.py tests/test_parse_mcc.py
git commit -m "feat(pipeline): parse MCC allotments into Gujarat records"
```

---

### Task 8: Build, validate and write JSON

**Files:**
- Create: `pipeline/build.py`
- Test: `tests/test_build.py`, `tests/test_built_data.py`

**Interfaces:**
- Consumes: everything from Tasks 1–7.
- Produces (files in `web/data/`):
  - `results.json`: `{"rows": {app: [roll, score|null, rank|null, status]}, "stats": {"appeared": int, "maxRank": int, "hist": {score: count}}}`
  - `merit_map.json`: `{"GEN": [[air, merit], …], "EWS": …, "SEBC": …, "SC": …, "ST": …}` — GEN from the General list (general merit), others from their own list (category merit); AIR ascending.
  - `gujarat.json`: list of `{"code", "college", "type", "course", "stream", "degree", "seat": "GQ"|"MQ", "fee": int|null, "seats": int|null, "last": {"1": {"OPEN": v, "EWS": v, "SC": v, "ST": v, "SEBC": v}, …}}`
  - `mcc.json`: list from `gujarat_records`.
  - `meta.json`: `{"built": iso timestamp, "sources": [rel paths]}`
- Functions: `gujarat_json(last_by_round, names, fees, seats) -> list[dict]`, `merit_json(merit_by_cat) -> dict`, `validate(results, merit, gujarat) -> list[str]` (problems; empty = OK), `main()`.

- [ ] **Step 1: Write failing test** — `tests/test_build.py`

```python
from pipeline.build import gujarat_json, merit_json, validate


def test_gujarat_json_merges_rounds_and_drops_pwd_nri():
    last = {
        1: [{"course": "Dermatology ,Venereology & Leprosy", "code": "SMC", "values": {"GQ_SE": 132.0}},
            {"course": "PWD", "code": "SMC", "values": {"GQ_OPEN": 5.0}},
            {"course": "Anaesthesiology", "code": "SMC-NQ", "values": {"GQ_OPEN": 99999.0}}],
        2: [{"course": "Dermatology Venereology & Leprosy", "code": "SMC", "values": {"GQ_SE": 156.0, "INST_OPEN": 3.0}}],
    }
    names = {"SMC": "Surat Municipal Institute of Medical Education & Research (SMIMER), Surat"}
    recs = gujarat_json(last, names, fees={}, seats={})
    assert len(recs) == 1
    r = recs[0]
    assert r["code"] == "SMC" and r["seat"] == "GQ" and r["type"] == "Municipal (Govt)"
    assert r["stream"] == "Dermatology"
    assert r["last"] == {"1": {"SEBC": 132.0}, "2": {"SEBC": 156.0}}


def test_dnb_course_stays_separate_from_md():
    last = {1: [{"course": "General Medicine", "code": "SMC", "values": {"GQ_OPEN": 700.0}},
                {"course": "General Medicine (DNB)", "code": "SMC", "values": {"GQ_OPEN": 900.0}}]}
    recs = gujarat_json(last, {"SMC": "SMIMER"}, fees={}, seats={})
    assert sorted(r["degree"] for r in recs) == ["DNB", "MD"]


def test_merit_json_uses_general_list_for_gen():
    merit = {"GEN": [(17, 1, None), (8824, 510, None)], "SEBC": [(133, 9, 1.0), (8723, 506, 98.0)]}
    assert merit_json(merit) == {"GEN": [[17, 1], [8824, 510]], "SEBC": [[133, 1.0], [8723, 98.0]]}


def test_validate_reports_problems():
    problems = validate(results=[{"app": "A", "sno": 1}, {"app": "A", "sno": 2}],
                        merit={"GEN": [[10, 5], [9, 6]]}, gujarat=[{"code": "X", "college": "X"}],
                        expected_rows=3)
    assert any("row count" in p for p in problems)
    assert any("duplicate" in p for p in problems)
    assert any("GEN" in p for p in problems)
    assert any("name" in p for p in problems)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_build.py -v`
Expected: FAIL, `ModuleNotFoundError`

- [ ] **Step 3: Implement** — `pipeline/build.py`

```python
import json
from datetime import datetime, timezone

from pipeline import sources
from pipeline.colleges import type_of
from pipeline.fetch import fetch
from pipeline.parse_gujarat import (branch_key, match_college, norm, parse_fees, parse_merit, parse_names,
                                    parse_seats, read_last_merit)
from pipeline.parse_mcc import gujarat_records, read_tables, round3_allotments, stray_allotments
from pipeline.parse_nbems import parse_results
from pipeline.pdftext import pdftotext
from pipeline.streams import degree_of, stream_of

GUJ_CAT = {"OPEN": "OPEN", "EWS": "EWS", "SC": "SC", "ST": "ST", "SE": "SEBC"}
NBEMS_ROWS = 273096


def _clean_course(course):
    return course.replace(" ,", ", ").replace("Dermatology, Venereology", "Dermatology Venereology")


def gujarat_json(last_by_round, names, fees, seats):
    """fees/seats: {(code, branch_key): (gq, mq)}."""
    recs = {}
    for rnd, rows in sorted(last_by_round.items()):
        for row in rows:
            if row["course"].startswith("PWD") or row["code"].endswith("-NQ"):
                continue
            code, _, suffix = row["code"].partition("-")
            seat = "MQ" if suffix == "MQ" else "GQ"
            course = _clean_course(row["course"])
            # record key keeps "(DNB)" distinct from MD; fee/seat lookup ignores it
            key = (code, norm(course), seat)
            vals = {GUJ_CAT[k[3:]]: v for k, v in row["values"].items() if k.startswith("GQ_")}
            if key not in recs:
                fee, seat_count = fees.get((code, branch_key(course))), seats.get((code, branch_key(course)))
                i = 0 if seat == "GQ" else 1
                recs[key] = {"code": code, "college": names.get(code, code), "type": type_of(code),
                             "course": course, "stream": stream_of(course), "degree": degree_of(course),
                             "seat": seat, "fee": fee[i] if fee else None,
                             "seats": seat_count[i] if seat_count else None, "last": {}}
            recs[key]["last"].setdefault(str(rnd), vals)
    return list(recs.values())


def merit_json(merit_by_cat):
    return {cat: [[air, gen if cat == "GEN" else c] for air, gen, c in rows]
            for cat, rows in merit_by_cat.items()}


def validate(results, merit, gujarat, expected_rows=NBEMS_ROWS):
    problems = []
    if len(results) != expected_rows:
        problems.append(f"NBEMS row count {len(results)} != {expected_rows}")
    if len({r["app"] for r in results}) != len(results):
        problems.append("NBEMS duplicate application numbers")
    for cat, pts in merit.items():
        if any(b[0] < a[0] or b[1] < a[1] for a, b in zip(pts, pts[1:])):
            problems.append(f"merit map {cat} not monotonic")
    for r in gujarat:
        if r["college"] == r["code"]:
            problems.append(f"no name for college code {r['code']}")
    return problems


def _spot_checks(merit, gujarat):
    problems = []
    amed = [r for r in gujarat if r["code"] == "AMED" and r["course"] == "Anaesthesiology" and r["seat"] == "GQ"]
    if not amed or amed[0]["last"].get("4", {}).get("OPEN") != 1102:
        problems.append("spot check AMED Anaesthesiology R4 OPEN != 1102")
    if [8723, 98.0] not in merit.get("SEBC", []):
        problems.append("spot check SEBC merit (8723 -> 98) missing")
    return problems


def _write(name, obj):
    sources.OUT.mkdir(parents=True, exist_ok=True)
    (sources.OUT / name).write_text(json.dumps(obj, separators=(",", ":")))


def main():
    missing = fetch()
    if missing:
        raise SystemExit(f"Download manually into data/raw/: {missing}")
    raw = lambda rel: sources.RAW / rel

    results = parse_results(pdftotext(raw(sources.NBEMS)))
    merit = merit_json({cat: parse_merit(pdftotext(raw(rel))) for cat, rel in sources.MERIT.items()})
    last = {rnd: read_last_merit(raw(rel)) for rnd, rel in sources.LAST_MERIT.items()}
    codes = {row["code"].partition("-")[0] for rows in last.values() for row in rows}
    names = parse_names(pdftotext(raw(sources.GUJ_INST)), codes)

    def by_college(rows):
        out = {}
        for header, branch, gq, mq in rows:
            code = match_college(header, names)
            if code:
                out.setdefault((code, branch_key(branch)), (gq, mq))
        return out

    fees = by_college(parse_fees(pdftotext(raw(sources.GUJ_FEES))))
    seats = by_college(parse_seats(pdftotext(raw(sources.GUJ_SEATS))))
    gujarat = gujarat_json(last, names, fees, seats)
    mcc = gujarat_records(round3_allotments(read_tables(raw(sources.MCC_R3)))
                          + stray_allotments(read_tables(raw(sources.MCC_STRAY))))

    problems = validate(results, merit, gujarat) + _spot_checks(merit, gujarat)
    if problems:
        raise SystemExit("Validation failed:\n" + "\n".join(problems))

    scored = [r for r in results if r["status"] == "OK"]
    hist = {}
    for r in scored:
        hist[r["score"]] = hist.get(r["score"], 0) + 1
    _write("results.json", {"rows": {r["app"]: [r["roll"], r["score"], r["rank"], r["status"]] for r in results},
                            "stats": {"appeared": len(scored), "maxRank": max(r["rank"] for r in scored),
                                      "hist": hist}})
    _write("merit_map.json", merit)
    _write("gujarat.json", gujarat)
    _write("mcc.json", mcc)
    _write("meta.json", {"built": datetime.now(timezone.utc).isoformat(), "sources": list(sources.SOURCES)})
    print(f"results {len(results)}, gujarat {len(gujarat)}, mcc {len(mcc)}, "
          f"fees matched {sum(r['fee'] is not None for r in gujarat)}/{len(gujarat)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run unit tests**

Run: `.venv/bin/pytest tests/test_build.py -v`
Expected: 4 passed

- [ ] **Step 5: Run the full build**

Run: `.venv/bin/python -m pipeline.build`
Expected (takes a few minutes): prints `results 273096, gujarat ~7xx, mcc ~2xx, fees matched …`, no "Validation failed".

- [ ] **Step 6: Write data check** — `tests/test_built_data.py`

```python
import json

import pytest

from pipeline.sources import OUT

pytestmark = pytest.mark.skipif(not (OUT / "gujarat.json").exists(), reason="run pipeline.build first")


def load(name):
    return json.loads((OUT / name).read_text())


def test_candidate_row():
    assert load("results.json")["rows"]["PG11111111"] == ["<roll>", 512, 8839, "OK"]


def test_known_last_merits():
    guj = load("gujarat.json")
    find = lambda code, stream: [r for r in guj if r["code"] == code and r["stream"] == stream
                                 and r["seat"] == "GQ" and r["degree"] == "MD"]
    assert find("SMC", "Dermatology")[0]["last"]["1"]["SEBC"] == 132
    bj = find("AMED", "Radio-Diagnosis")[0]["last"]["1"]
    assert bj["OPEN"] == 28 and bj["SEBC"] == 14
```

- [ ] **Step 7: Run it**

Run: `.venv/bin/pytest tests/test_built_data.py -v`
Expected: 2 passed

- [ ] **Step 8: Commit**

```bash
git add pipeline/build.py tests/test_build.py tests/test_built_data.py
git commit -m "feat(pipeline): build, validate and write web data"
```

---

### Task 9: Engine — lookup and result stats

**Files:**
- Create: `web/package.json`, `web/engine.js`, `web/engine.test.js`

**Interfaces:**
- Consumes: `results.json` shape from Task 8.
- Produces (exports of `web/engine.js`):
  - `normalizeAppNo(s: string) -> string` — trims, removes inner spaces, upper-cases.
  - `lookup(appNo, results) -> {appNo, roll, score, rank, status} | null`
  - `resultStats(candidate, stats) -> {status, percentileLE, percentileLT, percentileMid, percentileRank, topPercent, ahead, sameScore} | {status}` — only `{status}` when not `"OK"`.

- [ ] **Step 1: Write failing test** — `web/package.json` and `web/engine.test.js`

`web/package.json`:
```json
{ "type": "module" }
```

`web/engine.test.js`:
```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { lookup, normalizeAppNo, resultStats } from "./engine.js";

const results = {
  rows: { PG1: ["R1", 300, 2, "OK"], PG2: ["R2", 200, 3, "OK"], PG3: ["R3", 300, 1, "OK"], PG4: ["R4", null, null, "ABSENT"] },
  stats: { appeared: 3, maxRank: 3, hist: { 300: 2, 200: 1 } },
};

test("normalizeAppNo trims spaces and upper-cases", () => {
  assert.equal(normalizeAppNo("  pg 11111111 "), "PG11111111");
});

test("lookup finds candidate or returns null", () => {
  assert.deepEqual(lookup(" pg1", results), { appNo: "PG1", roll: "R1", score: 300, rank: 2, status: "OK" });
  assert.equal(lookup("PG999", results), null);
});

test("resultStats computes percentiles", () => {
  const s = resultStats(lookup("PG1", results), results.stats);
  assert.equal(s.status, "OK");
  assert.equal(s.percentileLE, 100);
  assert.ok(Math.abs(s.percentileLT - 100 / 3) < 1e-9);
  assert.ok(Math.abs(s.percentileMid - 200 / 3) < 1e-9);
  assert.equal(s.percentileRank, 50);
  assert.ok(Math.abs(s.topPercent - 200 / 3) < 1e-9);
  assert.equal(s.ahead, 0);
  assert.equal(s.sameScore, 2);
});

test("resultStats for absent candidate returns only status", () => {
  assert.deepEqual(resultStats(lookup("PG4", results), results.stats), { status: "ABSENT" });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test web/engine.test.js`
Expected: FAIL, `Cannot find module …/engine.js`

- [ ] **Step 3: Implement** — `web/engine.js`

```js
// Pure prediction logic. No DOM, no fetch: callers pass loaded data in.

export function normalizeAppNo(s) {
  return s.replace(/\s+/g, "").toUpperCase();
}

export function lookup(appNo, results) {
  const key = normalizeAppNo(appNo);
  const row = results.rows[key];
  if (!row) return null;
  const [roll, score, rank, status] = row;
  return { appNo: key, roll, score, rank, status };
}

export function resultStats(candidate, stats) {
  if (candidate.status !== "OK") return { status: candidate.status };
  const n = stats.appeared;
  let le = 0;
  for (const [score, count] of Object.entries(stats.hist)) if (Number(score) <= candidate.score) le += count;
  const same = stats.hist[candidate.score];
  const lt = le - same;
  return {
    status: "OK",
    percentileLE: (le / n) * 100,
    percentileLT: (lt / n) * 100,
    percentileMid: ((lt + same / 2) / n) * 100,
    percentileRank: ((stats.maxRank - candidate.rank) / (stats.maxRank - 1)) * 100,
    topPercent: ((n - lt) / n) * 100,
    ahead: n - le,
    sameScore: same,
  };
}
```

- [ ] **Step 4: Run tests**

Run: `node --test web/engine.test.js`
Expected: 4 pass

- [ ] **Step 5: Commit**

```bash
git add web/package.json web/engine.js web/engine.test.js
git commit -m "feat(engine): candidate lookup and result stats"
```

---

### Task 10: Engine — merit estimate

**Files:**
- Modify: `web/engine.js`, `web/engine.test.js`

**Interfaces:**
- Consumes: `merit_map.json` shape (Task 8).
- Produces: `estimateMerit(rank, category, meritMap) -> {general: number, category: number | null, extrapolated: boolean}`. `category` is `null` for `GEN`.

- [ ] **Step 1: Write failing tests** — append to `web/engine.test.js`

```js
import { estimateMerit } from "./engine.js";

const meritMap = {
  GEN: [[17, 1], [8824, 510], [8880, 511], [9000, 520]],
  SEBC: [[133, 1], [8723, 98], [8916, 99]],
};

test("estimateMerit interpolates between 2025 points", () => {
  assert.deepEqual(estimateMerit(8839, "SEBC", meritMap), { general: 510, category: 99, extrapolated: false });
});

test("estimateMerit for GEN has no category merit", () => {
  assert.deepEqual(estimateMerit(8839, "GEN", meritMap), { general: 510, category: null, extrapolated: false });
});

test("estimateMerit beyond list range extrapolates without NaN", () => {
  const m = estimateMerit(20000, "SEBC", meritMap);
  assert.equal(m.extrapolated, true);
  assert.ok(Number.isFinite(m.general) && Number.isFinite(m.category));
  assert.ok(m.category > 99);
});

test("estimateMerit never returns merit below 1", () => {
  assert.equal(estimateMerit(1, "GEN", meritMap).general, 1);
});
```

- [ ] **Step 2: Run to verify failure**

Run: `node --test web/engine.test.js`
Expected: FAIL, `estimateMerit` is not exported

- [ ] **Step 3: Implement** — append to `web/engine.js`

```js
// points: [[air, merit], ...] sorted by air. Returns [merit, extrapolated].
function interpolate(points, rank) {
  const first = points[0], last = points[points.length - 1];
  if (rank <= first[0]) return [Math.max(1, Math.round((first[1] * rank) / first[0])), false];
  if (rank > last[0]) return [Math.round((last[1] * rank) / last[0]), true];
  for (let i = 1; i < points.length; i++) {
    const [a1, m1] = points[i - 1], [a2, m2] = points[i];
    if (rank <= a2) return [Math.round(m1 + ((rank - a1) / (a2 - a1)) * (m2 - m1)), false];
  }
}

export function estimateMerit(rank, category, meritMap) {
  const [general, extraG] = interpolate(meritMap.GEN, rank);
  if (category === "GEN") return { general, category: null, extrapolated: extraG };
  const [cat, extraC] = interpolate(meritMap[category], rank);
  return { general, category: cat, extrapolated: extraG || extraC };
}
```

- [ ] **Step 4: Run tests**

Run: `node --test web/engine.test.js`
Expected: 8 pass

- [ ] **Step 5: Commit**

```bash
git add web/engine.js web/engine.test.js
git commit -m "feat(engine): estimate Gujarat merit from AIR"
```

---

### Task 11: Engine — Gujarat and MCC options

**Files:**
- Modify: `web/engine.js`, `web/engine.test.js`

**Interfaces:**
- Consumes: `gujarat.json`, `mcc.json` shapes (Task 8), `estimateMerit` output (Task 10).
- Produces:
  - `label(ratio) -> "High" | "Good" | "Borderline" | "Low"`
  - `gujaratOptions(merit, category, records) -> Option[]`
  - `mccOptions(rank, category, records) -> Option[]`
  - `Option = {stream, course, degree, college, type, route, chance, ratio, earliestRound: number|null, fee: number|null, reason}`; `chance` may also be `"Unknown"` when no usable data.

- [ ] **Step 1: Write failing tests** — append to `web/engine.test.js`

```js
import { gujaratOptions, label, mccOptions } from "./engine.js";

const merit = { general: 510, category: 99, extrapolated: false };
const guj = (last, extra = {}) => ({ code: "X", college: "College X", type: "Govt", course: "Dermatology",
  stream: "Dermatology", degree: "MD", seat: "GQ", fee: 130800, seats: 2, last, ...extra });

test("label thresholds", () => {
  assert.deepEqual([1.15, 1, 0.9, 0.89].map(label), ["High", "Good", "Borderline", "Low"]);
});

test("SEBC candidate reaches seat via SEBC merit in round 1", () => {
  const [o] = gujaratOptions(merit, "SEBC", [guj({ 1: { OPEN: 100, SEBC: 132 }, 2: { SEBC: 156 } })]);
  assert.equal(o.chance, "High");
  assert.equal(o.earliestRound, 1);
  assert.equal(o.route, "Gujarat State - Govt Quota");
  assert.match(o.reason, /SEBC merit 156/);
});

test("far-away seat is Low", () => {
  const [o] = gujaratOptions(merit, "SEBC", [guj({ 1: { OPEN: 28, SEBC: 14 }, 4: { OPEN: 70, SEBC: 20 } })]);
  assert.equal(o.chance, "Low");
  assert.equal(o.earliestRound, null);
});

test("GEN candidate is never matched on a category column", () => {
  const [o] = gujaratOptions({ general: 510, category: null }, "GEN", [guj({ 1: { OPEN: 100, SEBC: 9999 } })]);
  assert.equal(o.chance, "Low");
});

test("management quota uses OPEN only", () => {
  const [o] = gujaratOptions(merit, "SEBC", [guj({ 1: { OPEN: 600, SEBC: 5 } }, { seat: "MQ", type: "Private" })]);
  assert.equal(o.chance, "High");
  assert.equal(o.route, "Gujarat State - Management Quota");
});

test("vacant seat (99999) is reachable", () => {
  const [o] = gujaratOptions(merit, "SEBC", [guj({ 3: { OPEN: 99999 } })]);
  assert.equal(o.chance, "High");
  assert.equal(o.earliestRound, 3);
  assert.match(o.reason, /vacant/);
});

test("rounds missing the candidate's column give Unknown, not NaN", () => {
  const [o] = gujaratOptions(merit, "ST", [guj({ 1: { SEBC: 50 } })]);
  assert.equal(o.chance, "Unknown");
  assert.equal(o.ratio, null);
});

test("mccOptions uses last rank for the candidate's category", () => {
  const rec = { college: "B. J. Medical College", stream: "General Surgery", course: "M.S. (GENERAL SURGERY)",
    degree: "MS", quota: "All India 50%", sector: "Govt", rounds: ["2024 R3"],
    last: { GEN: 8000, EWS: null, SEBC: 10500, SC: 20000, ST: null } };
  const [o] = mccOptions(8839, "SEBC", [rec]);
  assert.equal(o.chance, "High");
  assert.equal(o.route, "MCC - All India 50%");
  assert.match(o.reason, /10500/);
  assert.equal(mccOptions(8839, "ST", [rec])[0].chance, "Unknown");
});
```

- [ ] **Step 2: Run to verify failure**

Run: `node --test web/engine.test.js`
Expected: FAIL, `gujaratOptions` is not exported

- [ ] **Step 3: Implement** — append to `web/engine.js`

```js
export const VACANT = 99999;

export function label(ratio) {
  if (ratio >= 1.15) return "High";
  if (ratio >= 1) return "Good";
  if (ratio >= 0.9) return "Borderline";
  return "Low";
}

export function gujaratOptions(merit, category, records) {
  return records.map((rec) => {
    let best = null, earliest = null;
    for (const [round, vals] of Object.entries(rec.last)) {
      const tries = [["Open", vals.OPEN, merit.general]];
      if (rec.seat === "GQ" && category !== "GEN") tries.push([category, vals[category], merit.category]);
      for (const [lab, value, mine] of tries) {
        if (value == null || mine == null) continue;
        const ratio = value === VACANT ? Infinity : value / mine;
        if (ratio >= 1 && earliest === null) earliest = Number(round);
        if (!best || ratio > best.ratio) best = { ratio, round, lab, value, mine };
      }
    }
    const reason = !best ? "No 2025 data for your category"
      : best.value === VACANT ? `Round ${best.round} 2025: seat went vacant`
      : `Round ${best.round} 2025 last ${best.lab} merit ${best.value}; your ${best.lab} merit ~${best.mine}`;
    return {
      stream: rec.stream, course: rec.course, degree: rec.degree, college: rec.college, type: rec.type,
      route: rec.seat === "GQ" ? "Gujarat State - Govt Quota" : "Gujarat State - Management Quota",
      chance: best ? label(best.ratio) : "Unknown", ratio: best ? best.ratio : null,
      earliestRound: earliest, fee: rec.fee, reason,
    };
  });
}

export function mccOptions(rank, category, records) {
  return records.map((rec) => {
    const last = rec.last[category];
    const ratio = last == null ? null : last / rank;
    return {
      stream: rec.stream, course: rec.course, degree: rec.degree, college: rec.college, type: rec.sector,
      route: `MCC - ${rec.quota}`, chance: ratio == null ? "Unknown" : label(ratio), ratio,
      earliestRound: null, fee: null,
      reason: last == null ? "No MCC allotment data for your category"
        : `MCC last AIR allotted to your category ${last} (${rec.rounds.join(", ")}); your AIR ${rank}`,
    };
  });
}
```

Note: the reason uses the *best* round (highest ratio), so for the round-1-reachable SEBC example the reason quotes round 2 (`156`) — that is intended: it shows the most generous cutoff seen. `earliestRound` separately says when it first became reachable.

- [ ] **Step 4: Run tests**

Run: `node --test web/engine.test.js`
Expected: 16 pass

- [ ] **Step 5: Commit**

```bash
git add web/engine.js web/engine.test.js
git commit -m "feat(engine): Gujarat state and MCC options with chance labels"
```

---

### Task 12: Engine — insights, predict and data check

**Files:**
- Modify: `web/engine.js`, `web/engine.test.js`
- Create: `web/engine.data.test.js`

**Interfaces:**
- Consumes: Tasks 10–11.
- Produces:
  - `insights(options) -> Array<{stream, reachable, govtReachable, privateReachable, topGovt: string[], closestMiss: string|null, feeMin: number|null, feeMax: number|null}>` sorted by `govtReachable` desc. "Reachable" = High/Good/Borderline. Govt types: `Govt`, `Municipal (Govt)`, `GMERS (Govt society)`. `topGovt`: up to 3 reachable Govt-type colleges with the *lowest* ratio (most competitive first). `closestMiss`: reason of the highest-ratio Low Govt-type option when no Govt-type option is reachable.
  - `predict({rank, category, domicile}, data) -> {merit, options, insights}` where `data = {meritMap, gujarat, mcc}`. Options sorted: Govt types first, then Private, then others; within that High, Good, Borderline, Low, Unknown.
  - `GOVT_TYPES` (Set).

- [ ] **Step 1: Write failing tests** — append to `web/engine.test.js`

```js
import { insights, predict } from "./engine.js";

test("predict without Gujarat domicile has no state quota options", () => {
  const data = { meritMap, gujarat: [guj({ 1: { OPEN: 600 } })], mcc: [] };
  const withDom = predict({ rank: 8839, category: "SEBC", domicile: true }, data);
  const noDom = predict({ rank: 8839, category: "SEBC", domicile: false }, data);
  assert.equal(withDom.options.length, 1);
  assert.equal(noDom.options.length, 0);
  assert.deepEqual(noDom.merit, { general: 510, category: 99, extrapolated: false });
});

test("insights summarise reachable options per stream", () => {
  const opts = [
    { stream: "Dermatology", college: "A", type: "Govt", chance: "Low", ratio: 0.3, fee: 1, reason: "far" },
    { stream: "Dermatology", college: "B", type: "Private", chance: "High", ratio: 3, fee: 3000000, reason: "" },
    { stream: "Pathology", college: "C", type: "Govt", chance: "High", ratio: 5, fee: 130800, reason: "" },
    { stream: "Pathology", college: "D", type: "Govt", chance: "Good", ratio: 1.05, fee: 130800, reason: "" },
  ];
  const [path, derm] = insights(opts);
  assert.equal(path.stream, "Pathology");
  assert.deepEqual(path.topGovt, ["D", "C"]);
  assert.equal(derm.govtReachable, 0);
  assert.equal(derm.privateReachable, 1);
  assert.equal(derm.closestMiss, "A: far");
  assert.equal(derm.feeMin, 3000000);
});
```

`web/engine.data.test.js`:
```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { lookup, predict } from "./engine.js";

const dir = new URL("./data/", import.meta.url);
const load = (f) => JSON.parse(readFileSync(new URL(f, dir)));
const built = existsSync(new URL("gujarat.json", dir));

test("PG11111111 SEBC Gujarat matches the manual report", { skip: !built && "run pipeline.build first" }, () => {
  const cand = lookup("PG11111111", load("results.json"));
  const data = { meritMap: load("merit_map.json"), gujarat: load("gujarat.json"), mcc: load("mcc.json") };
  const { merit, options } = predict({ rank: cand.rank, category: "SEBC", domicile: true }, data);
  assert.deepEqual(merit, { general: 510, category: 99, extrapolated: false });
  const find = (college, stream) => options.find((o) => o.college.startsWith(college) && o.stream === stream
    && o.route === "Gujarat State - Govt Quota" && o.degree === "MD");
  const smimer = find("Surat Municipal", "Dermatology");
  assert.equal(smimer.chance, "High");
  assert.equal(smimer.earliestRound, 1);
  assert.equal(find("B. J. Medical", "Radio-Diagnosis").chance, "Low");
});
```

- [ ] **Step 2: Run to verify failure**

Run: `node --test web/engine.test.js`
Expected: FAIL, `insights` is not exported

- [ ] **Step 3: Implement** — append to `web/engine.js`

```js
export const GOVT_TYPES = new Set(["Govt", "Municipal (Govt)", "GMERS (Govt society)"]);
const REACHABLE = new Set(["High", "Good", "Borderline"]);
const CHANCE_ORDER = { High: 0, Good: 1, Borderline: 2, Low: 3, Unknown: 4 };
const typeOrder = (t) => (GOVT_TYPES.has(t) ? 0 : t === "Private" ? 1 : 2);

export function insights(options) {
  const byStream = new Map();
  for (const o of options) {
    if (!byStream.has(o.stream)) byStream.set(o.stream, []);
    byStream.get(o.stream).push(o);
  }
  const out = [];
  for (const [stream, opts] of byStream) {
    const reach = opts.filter((o) => REACHABLE.has(o.chance));
    const govt = reach.filter((o) => GOVT_TYPES.has(o.type)).sort((a, b) => a.ratio - b.ratio);
    const govtLow = opts.filter((o) => GOVT_TYPES.has(o.type) && o.chance === "Low").sort((a, b) => b.ratio - a.ratio);
    const fees = reach.map((o) => o.fee).filter((f) => f != null);
    out.push({
      stream, reachable: reach.length, govtReachable: govt.length,
      privateReachable: reach.filter((o) => !GOVT_TYPES.has(o.type)).length,
      topGovt: govt.slice(0, 3).map((o) => o.college),
      closestMiss: govt.length === 0 && govtLow.length ? `${govtLow[0].college}: ${govtLow[0].reason}` : null,
      feeMin: fees.length ? Math.min(...fees) : null, feeMax: fees.length ? Math.max(...fees) : null,
    });
  }
  return out.sort((a, b) => b.govtReachable - a.govtReachable);
}

export function predict({ rank, category, domicile }, data) {
  const merit = estimateMerit(rank, category, data.meritMap);
  const options = [
    ...(domicile ? gujaratOptions(merit, category, data.gujarat) : []),
    ...mccOptions(rank, category, data.mcc),
  ].sort((a, b) => typeOrder(a.type) - typeOrder(b.type) || CHANCE_ORDER[a.chance] - CHANCE_ORDER[b.chance]);
  return { merit, options, insights: insights(options) };
}
```

- [ ] **Step 4: Run tests**

Run: `node --test web/engine.test.js web/engine.data.test.js`
Expected: 18 pass (unit) + 1 pass (data test, requires Task 8 build)

- [ ] **Step 5: Commit**

```bash
git add web/engine.js web/engine.test.js web/engine.data.test.js
git commit -m "feat(engine): insights and predict entry point"
```

---

### Task 13: UI

**Files:**
- Create: `web/index.html`, `web/styles.css`, `web/app.js`

**Interfaces:**
- Consumes: `lookup`, `resultStats`, `predict`, `GOVT_TYPES` from `web/engine.js`; JSON from `web/data/`.

- [ ] **Step 1: Write `web/index.html`**

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>NEET-PG Gujarat Admission Predictor</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <main>
    <h1>NEET-PG 2026 · Gujarat Admission Predictor</h1>
    <p id="loading">Loading data…</p>

    <form id="form" hidden>
      <label>Application number <input id="app" required placeholder="PG11111111" autocomplete="off"></label>
      <label>Category
        <select id="category">
          <option value="GEN">General</option><option value="EWS">EWS</option>
          <option value="SEBC">SEBC / OBC</option><option value="SC">SC</option><option value="ST">ST</option>
        </select>
      </label>
      <label class="check"><input type="checkbox" id="domicile" checked> Gujarat domicile</label>
      <button type="submit">Show result</button>
    </form>
    <p id="error" class="error" role="alert"></p>

    <section id="result" hidden></section>
    <button id="predict" hidden>Predict my Gujarat options</button>

    <section id="prediction" hidden>
      <div id="merit"></div>
      <h2>Insights</h2>
      <div id="insights"></div>
      <h2>All options</h2>
      <div class="filters">
        <select id="f-stream"><option value="">All streams</option></select>
        <select id="f-type"><option value="">All college types</option></select>
        <select id="f-route"><option value="">All routes</option></select>
        <select id="f-chance">
          <option value="reach">High / Good / Borderline</option><option value="">All chances</option>
          <option value="High">High</option><option value="Good">Good</option>
          <option value="Borderline">Borderline</option><option value="Low">Low</option>
        </select>
        <button id="csv" type="button">Download CSV</button>
      </div>
      <p id="count"></p>
      <table id="table"><thead></thead><tbody></tbody></table>
      <details class="legend"><summary>What do High / Good / Borderline / Low mean?</summary>
        <p><b>High</b>: last 2025 admit was at least 15% past your position. <b>Good</b>: last admit at or a little past you.
          <b>Borderline</b>: last admit within 10% ahead of you. <b>Low</b>: seat closed well before your position.</p>
      </details>
      <p class="disclaimer">Estimates from Gujarat 2025-26 state cutoffs and MCC 2024/2025 cutoffs. Not a guarantee.
        Check your real merit number in the official 2026 Gujarat merit list.</p>
    </section>
  </main>
  <script type="module" src="app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Write `web/styles.css`**

```css
body { font-family: system-ui, sans-serif; margin: 0; background: #f6f7f9; color: #1d2330; }
main { max-width: 1100px; margin: 0 auto; padding: 1.5rem; }
h1 { font-size: 1.4rem; }
form, .filters { display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: end; }
label { display: flex; flex-direction: column; font-size: 0.85rem; gap: 0.25rem; }
label.check { flex-direction: row; align-items: center; }
input, select, button { font: inherit; padding: 0.45rem 0.6rem; }
button { background: #2457d6; color: #fff; border: 0; border-radius: 6px; cursor: pointer; }
section { background: #fff; border-radius: 8px; padding: 1rem 1.25rem; margin: 1rem 0; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 0.75rem; }
.card { background: #f0f3fa; border-radius: 6px; padding: 0.6rem 0.8rem; }
.card b { display: block; font-size: 1.2rem; }
.error { color: #b3261e; }
table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
th, td { text-align: left; padding: 0.4rem; border-bottom: 1px solid #e3e6ec; vertical-align: top; }
.High { color: #137333; font-weight: 600; } .Good { color: #1a73e8; font-weight: 600; }
.Borderline { color: #b06000; font-weight: 600; } .Low, .Unknown { color: #80868b; }
.disclaimer { font-size: 0.8rem; color: #5f6368; }
```

- [ ] **Step 3: Write `web/app.js`**

```js
import { GOVT_TYPES, lookup, predict, resultStats } from "./engine.js";

const $ = (id) => document.getElementById(id);
const COLS = [["stream", "Stream"], ["course", "Course"], ["college", "College"], ["type", "Type"], ["route", "Route"],
  ["chance", "Chance"], ["earliestRound", "Earliest round"], ["fee", "Fee / yr"], ["reason", "Reason"]];
const fmt = (n, d = 2) => n.toLocaleString("en-IN", { maximumFractionDigits: d });
const fee = (f) => (f == null ? "" : `₹${fmt(f / 1e5, 1)} L`);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

let data, candidate, options = [];

async function load() {
  const get = (f) => fetch(`data/${f}`).then((r) => { if (!r.ok) throw new Error(f); return r.json(); });
  const [results, meritMap, gujarat, mcc] = await Promise.all(
    ["results.json", "merit_map.json", "gujarat.json", "mcc.json"].map(get));
  data = { results, meritMap, gujarat, mcc };
  $("loading").hidden = true;
  $("form").hidden = false;
}

function showResult(e) {
  e.preventDefault();
  $("error").textContent = "";
  $("prediction").hidden = true;
  candidate = lookup($("app").value, data.results);
  if (!candidate) {
    $("result").hidden = $("predict").hidden = true;
    $("error").textContent = "Application number not found in the NEET-PG 2026 result.";
    return;
  }
  const s = resultStats(candidate, data.results.stats);
  const card = (k, v) => `<div class="card">${k}<b>${v}</b></div>`;
  $("result").innerHTML = `<h2>${esc(candidate.appNo)} · Roll ${esc(candidate.roll)}</h2>` + (s.status !== "OK"
    ? `<p>Status: <b>${esc(s.status)}</b>. No prediction available.</p>`
    : `<div class="cards">${[
        card("Score (out of 720)", candidate.score), card("All India Rank", fmt(candidate.rank, 0)),
        card("Percentile (≤ score)", fmt(s.percentileLE, 4)), card("Percentile (< score)", fmt(s.percentileLT, 4)),
        card("Percentile (mid-rank)", fmt(s.percentileMid, 4)), card("Percentile (from rank)", fmt(s.percentileRank, 4)),
        card("Top %", fmt(s.topPercent, 3)), card("Candidates ahead", fmt(s.ahead, 0)),
        card("Same score", fmt(s.sameScore, 0))].join("")}</div>`);
  $("result").hidden = false;
  $("predict").hidden = s.status !== "OK";
}

function showPrediction() {
  const category = $("category").value, domicile = $("domicile").checked;
  const p = predict({ rank: candidate.rank, category, domicile }, data);
  options = p.options;
  const m = p.merit;
  $("merit").innerHTML = `<h2>Predicted Gujarat merit</h2><p>General merit <b>~${m.general}</b>` +
    (m.category != null ? ` · ${category} merit <b>~${m.category}</b>` : "") +
    `</p><p class="disclaimer">AIR ${fmt(candidate.rank, 0)} placed between the candidates around it in the 2025 Gujarat merit lists.` +
    (m.extrapolated ? " Your rank is beyond the 2025 list, so this is extrapolated and less reliable." : "") +
    (domicile ? "" : " Without Gujarat domicile only MCC seats in Gujarat colleges are shown.") + "</p>";
  $("insights").innerHTML = `<table><thead><tr><th>Stream</th><th>Govt options</th><th>Private/other</th>
    <th>Best Govt options</th><th>Fee range</th></tr></thead><tbody>${p.insights.map((i) => `<tr>
    <td>${esc(i.stream)}</td><td>${i.govtReachable}</td><td>${i.privateReachable}</td>
    <td>${esc(i.topGovt.join("; ") || (i.closestMiss ? `None. Closest: ${i.closestMiss}` : "None"))}</td>
    <td>${i.feeMin == null ? "" : `${fee(i.feeMin)} – ${fee(i.feeMax)}`}</td></tr>`).join("")}</tbody></table>`;
  fillFilter("f-stream", options.map((o) => o.stream));
  fillFilter("f-type", options.map((o) => o.type));
  fillFilter("f-route", options.map((o) => o.route));
  $("prediction").hidden = false;
  renderTable();
}

function fillFilter(id, values) {
  const sel = $(id), first = sel.options[0];
  sel.replaceChildren(first, ...[...new Set(values)].sort().map((v) => new Option(v, v)));
}

function filtered() {
  const [st, ty, ro, ch] = ["f-stream", "f-type", "f-route", "f-chance"].map((id) => $(id).value);
  return options.filter((o) => (!st || o.stream === st) && (!ty || o.type === ty) && (!ro || o.route === ro)
    && (!ch || (ch === "reach" ? ["High", "Good", "Borderline"].includes(o.chance) : o.chance === ch)));
}

function renderTable() {
  const rows = filtered();
  $("count").textContent = `${rows.length} options (${rows.filter((o) => GOVT_TYPES.has(o.type)).length} Govt-type)`;
  $("table").tHead.innerHTML = `<tr>${COLS.map(([, h]) => `<th>${h}</th>`).join("")}</tr>`;
  $("table").tBodies[0].innerHTML = rows.map((o) => `<tr>${COLS.map(([k]) => `<td${k === "chance" ? ` class="${o.chance}"` : ""}>${
    esc(k === "fee" ? fee(o.fee) : k === "earliestRound" ? (o.earliestRound ? `Round ${o.earliestRound}` : "") : o[k])}</td>`).join("")}</tr>`).join("");
}

function downloadCsv() {
  const cell = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const csv = [COLS.map(([, h]) => cell(h)).join(","), ...filtered().map((o) => COLS.map(([k]) => cell(o[k])).join(","))].join("\n");
  const a = Object.assign(document.createElement("a"), {
    href: URL.createObjectURL(new Blob([csv], { type: "text/csv" })), download: `${candidate.appNo}-gujarat-options.csv` });
  a.click();
  URL.revokeObjectURL(a.href);
}

$("form").addEventListener("submit", showResult);
$("predict").addEventListener("click", showPrediction);
["f-stream", "f-type", "f-route", "f-chance"].forEach((id) => $(id).addEventListener("change", renderTable));
$("csv").addEventListener("click", downloadCsv);
load().catch((err) => { $("loading").textContent = `Could not load data (${err.message}). Run: python -m pipeline.build`; });
```

- [ ] **Step 4: Manual check**

Run: `cd web && python3 -m http.server 8000` then open `http://localhost:8000`.
Check, in order:
1. Loading message disappears; form shows.
2. Enter ` pg11111111 ` → result card: score 512, AIR 8,839, percentile (≤ score) 96.6856, candidates ahead 8,815.
3. Enter `PG99999999` → "Application number not found".
4. Enter `PG26083665` (withheld) → status WITHHELD, no Predict button.
5. PG11111111, SEBC, domicile on → Predict → General merit ~510, SEBC merit ~99. Insights table lists streams. Filter stream = Dermatology → SMIMER Surat High, Round 1.
6. Untick domicile → Predict → only `MCC - …` routes.
7. Download CSV → file opens in Excel with the filtered rows.

- [ ] **Step 5: Commit**

```bash
git add web/index.html web/styles.css web/app.js
git commit -m "feat(web): result lookup and Gujarat prediction UI"
```

---

### Task 14: README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace the "Status" paragraph and add a "Run" section** in `README.md`

```markdown
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
are published), delete the old file from `data/raw/`, and rerun `python -m pipeline.build`.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add run and data update instructions"
```
