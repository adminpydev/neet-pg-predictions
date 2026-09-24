import pdfplumber, pandas as pd, re
COLS = [f"{g}_{c}" for g in ("GQ", "INST", "INSV") for c in ("OPEN", "EWS", "SC", "ST", "SE")]
out = []
for rnd, f in [(1, "r1_last_merit_xyz1"), (2, "r2_last_merit_22122025"), (3, "r3_last_merit_1"), (4, "r4_last_merit")]:
    course = None
    with pdfplumber.open(f + ".pdf") as p:
        for pg in p.pages:
            rows = {}
            for w in pg.extract_words(): rows.setdefault(round(w["top"]), []).append(w)
            hdr = next((ws for ws in rows.values() if [w["text"] for w in ws][:2] == ["College", "OPEN"]), None)
            if not hdr: continue
            xs = [w["x1"] for w in hdr[1:]]
            pending = None
            for t in sorted(rows):
                ws = [w for w in rows[t] if w["text"] != "*"]
                if not ws or ws is hdr or t <= hdr[0]["top"]: continue
                nums = [w for w in ws if re.fullmatch(r"[\d.]+", w["text"])]
                if nums and len(nums) == len(ws):
                    pending = {COLS[min(range(15), key=lambda i: abs(xs[i] - w["x1"]))]: float(w["text"]) for w in nums}
                elif ws[0]["x0"] < 85:
                    course = " ".join(w["text"] for w in ws); pending = None
                elif pending is not None:
                    out.append({"Round": rnd, "Course": course, "Code": " ".join(w["text"] for w in ws), **pending}); pending = None
df = pd.DataFrame(out); df.to_pickle("glast.pkl")
print(len(df), df.groupby("Round").size().to_dict()); print(df.Course.nunique(), sorted(df.Code.unique()))
print(df[df.Round == 4].head(8).to_string())
