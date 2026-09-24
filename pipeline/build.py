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
