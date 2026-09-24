import re, pandas as pd
exec(open("final.py").read().split("out = ")[0])   # reuse Gj, C, stream_of
G_, E_ = G, E
def reason_state(r):
    first = r["Earliest round reachable"]
    ks = [int(first[-1])] if first != "-" else [1, 2, 3, 4]
    best = None
    for k in ks:
        for lab, v, me in (("Open", r[f"R{k} OPEN last merit"], G_), ("SEBC", r[f"R{k} SEBC last merit"], E_)):
            if v == "Vacant": return f"Round {k} 2025: seat went vacant (open to any eligible)"
            if pd.notna(v) and (best is None or v / me > best[0]): best = (v / me, k, lab, v, me)
    if not best: return ""
    _, k, lab, v, me = best
    return (f"Round {k} 2025 last {lab} merit {v:g} >= your ~{me}" if v >= me else f"best 2025 last {lab} merit {v:g} (Round {k}), just short of your ~{me}")
Gj["Reason"] = Gj.apply(reason_state, axis=1)
fee = lambda f: f"Rs {f/1e5:.1f} lakh/yr" if pd.notna(f) else "fee n/a"
st = Gj[Gj["Chance (OBC/SEBC)"] != "Low"].copy()
st = pd.DataFrame({"Stream": st.Course.map(stream_of), "Course": st.Course, "College": st.College, "Type": st.Type,
    "Route": "Gujarat State - " + st.Seat, "Chance": st["Chance (OBC/SEBC)"], "Earliest round": st["Earliest round reachable"],
    "Fee": st["Annual tuition fee (Rs)"].map(fee), "Reason": st.Reason})
m = C[(C.State == "Gujarat") & C["Chance (OBC)"].isin(["High", "Good", "Borderline"])].copy()
m = pd.DataFrame({"Stream": m.Stream, "Course": m.Stream + " (" + m.Degree + ")", "College": m.Institute.str.title(), "Type": m.Sector,
    "Route": "MCC - " + m.Quota, "Chance": m["Chance (OBC)"], "Earliest round": m.Rounds.fillna("2025 Stray"), "Fee": "see college",
    "Reason": "Last OBC-eligible AIR allotted " + m["Rank used for chance"].astype(int).astype(str) + " (MCC 2024/2025) vs your AIR 8839"})
A = pd.concat([st, m])
A["t"] = A.Type.map({"Govt": 0, "Municipal (Govt)": 1, "GMERS (Govt society)": 2, "DNB Hospital": 4, "Private (Deemed)": 5}).fillna(3)
A["c"] = A.Chance.map({"High": 0, "Good": 1, "Borderline": 2})
A = A.sort_values(["Stream", "t", "c", "College"]).drop(columns=["t", "c"])
A.to_pickle("gall.pkl")
with pd.ExcelWriter("/Users/vedantparikh/Downloads/PG11111111 Admission Possibilities (OBC, Gujarat).xlsx", mode="a", engine="openpyxl", if_sheet_exists="replace") as w:
    A.to_excel(w, sheet_name="Gujarat All Possibilities", index=False)
print(len(A), A.Route.value_counts().to_dict())
