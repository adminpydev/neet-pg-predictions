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
