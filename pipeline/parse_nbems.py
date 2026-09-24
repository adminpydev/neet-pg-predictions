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
