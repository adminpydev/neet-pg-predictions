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
PIN = re.compile(r"(?<!\d)\d{6}(?!\d)")
# ponytail: cities seen in Gujarat MCC addresses; used only to make display names unambiguous
CITY = re.compile(r"\b(Ahmedabad|Surat|Vadodara|Baroda|Rajkot|Bhavnagar|Jamnagar|Gandhinagar|Junagadh|Valsad|"
                  r"Navsari|Porbandar|Patan|Morbi|Hiimmatnagar|Himmatnagar|Vadnagar|Rajpipla|Vyara|Mehsana|"
                  r"Deesa|Jamkhambhaliya|Upleta|Surendranagar|Vapi|Halol)\b", re.I)
ACRONYMS = {"GMERS", "SBKS", "HCG", "ESIC", "MRI", "IVF", "BAPS", "SGVP", "IKDRC", "ITS", "DNB", "AIIMS"}


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


def _norm(s):
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def _first(inst):
    return inst.split(",")[0].strip()


def _institutes(allotments):
    """Map each distinct institute text to an institute key, or None when it can't be pinned down.

    Texts with a PIN code are keyed by (first segment, PIN). A short text (Round 1/2 cells often carry
    no address) joins an institute only if it is a prefix of exactly one addressed institute in any
    state; otherwise it stands alone if it names Gujarat, else it is dropped (state unknown)."""
    texts = {a["inst"] for a in allotments}
    full = {}
    for t in texts:
        pins = PIN.findall(t)
        if pins:
            full.setdefault((_norm(_first(t)), pins[-1]), []).append(_norm(t))
    keys = {}
    for t in texts:
        pins = PIN.findall(t)
        if pins:
            keys[t] = (_norm(_first(t)), pins[-1])
            continue
        n = _norm(t)
        hits = {k for k, norms in full.items() if any(f.startswith(n) for f in norms)}
        keys[t] = hits.pop() if len(hits) == 1 else (n, "") if not hits and "GUJARAT" in n else None
    return keys


def _display(texts):
    """Readable name: first segment plus city, keeping acronyms (GMERS, SBKS, HCG) upper-case."""
    t = max(texts, key=len)
    name = re.sub(r"\b[A-Z]{3,}\b", lambda m: m[0] if m[0] in ACRONYMS else m[0].capitalize(), _first(t))
    city = CITY.search(t, len(_first(t)))
    if city and city[0].lower() not in name.lower():
        name += ", " + city[0].capitalize()
    return name


def _eligible(a, category):
    if a["quota"] == "PS":  # deemed seats have no reservation
        return True
    own = MCC_CAT[category]
    return a["cat"] in ("Open", own) or a["cand"] in ("General", own)


def _last(rows):
    rows = list(rows)
    out = {}
    for cat in MCC_CAT:
        ranks = [a["rank"] for a in rows if _eligible(a, cat)]
        out[cat] = max(ranks) if ranks else None
    return out


def gujarat_records(allotments):
    """One record per Gujarat institute x course x quota. `last` is the 2024 R1-R3 last eligible rank per
    category; `strayLast` the 2025 stray-round one (shown alongside, used only when `last` is missing)."""
    allotments = [a for a in allotments if a["quota"] in QUOTAS]
    keys = _institutes(allotments)
    texts = {}
    for t, k in keys.items():
        texts.setdefault(k, []).append(t)
    gujarat = {k for k, ts in texts.items() if k and any("gujarat" in t.lower() for t in ts)}
    groups = {}
    for a in allotments:
        k = keys[a["inst"]]
        if k in gujarat:
            groups.setdefault((k, a["course"], a["quota"]), []).append(a)
    records = []
    for (k, course, quota), items in groups.items():
        stray = [a["round"] == "2025 Stray" for a in items]
        records.append({"college": _display(texts[k]), "stream": stream_of(course), "course": course,
                        "degree": degree_of(course), "quota": QUOTAS[quota][0], "sector": QUOTAS[quota][1],
                        "rounds": sorted({a["round"] for a in items}),
                        "last": _last(a for a, s in zip(items, stray) if not s),
                        "strayLast": _last(a for a, s in zip(items, stray) if s)})
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
