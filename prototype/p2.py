import re, sys, pandas as pd
t = open(sys.argv[1] + "/r.txt").read()
rows = re.findall(r"(\d+)\s+(PG\d{8})\s+(\d{11})\s+(-?\d+|ABSENT|WITHHELD)\s+(\d+|ABSENT|WITHHELD)", t)
df = pd.DataFrame(rows, columns=["S.No.", "Application Sequence Number", "Roll Number", "Total Score (Out of 720)", "NEET-PG 2026 Rank"])
df["S.No."] = df["S.No."].astype(int)
assert len(df) == 273096 and df["S.No."].is_unique
sc = pd.to_numeric(df["Total Score (Out of 720)"], errors="coerce")
rk = pd.to_numeric(df["NEET-PG 2026 Rank"], errors="coerce")
n = sc.notna().sum()
le = sc.rank(method="max")          # count scoring <= X
lt = sc.rank(method="min") - 1      # count scoring < X
eq = le - lt
df["Percentile (<= score, NBEMS style)"] = le / n * 100
df["Percentile (< score, strictly below)"] = lt / n * 100
df["Percentile (mid-rank)"] = (lt + eq / 2) / n * 100
df["Percentile (from official rank)"] = (rk.max() - rk) / (rk.max() - 1) * 100
df["Top % (candidates at or above)"] = (n - lt) / n * 100
df["Candidates with same score"] = eq
df["Candidates ahead (higher score)"] = n - le
for c in df.columns[5:10]:
    df[c] = df[c].round(6)
print("scored", n, "max rank", rk.max())

pts = [99.9, 99.5, 99, 98, 97, 95, 90, 85, 80, 75, 70, 60, 50, 45, 40, 30, 25, 20, 10, 5, 1]
s = sc.dropna()
cut = pd.DataFrame({"Percentile": pts})
cut["Min score to be at/above this percentile"] = [s[le.dropna() / n * 100 >= p].min() for p in pts]
cut["Candidates at/above"] = [int((s >= v).sum()) for v in cut.iloc[:, 1]]
cut["Note"] = cut["Percentile"].map({50: "General/EWS qualifying (50th)", 45: "General-PwBD qualifying (45th)", 40: "SC/ST/OBC incl. PwBD qualifying (40th)"}).fillna("")
summ = pd.DataFrame({"Metric": ["Total candidates", "Appeared (scored)", "Absent", "Withheld", "Max score", "Min score", "Mean score", "Median score", "Std dev"],
    "Value": [len(df), n, (df.iloc[:, 3] == "ABSENT").sum(), (df.iloc[:, 3] == "WITHHELD").sum(), s.max(), s.min(), round(s.mean(), 2), s.median(), round(s.std(), 2)]})
dist = s.value_counts().sort_index(ascending=False).rename_axis("Score").reset_index(name="Candidates")
dist["Percentile (<= score)"] = (dist["Candidates"][::-1].cumsum()[::-1] / n * 100).round(6)

out = "/Users/vedantparikh/Downloads/NEET-PG 2026 Result with Percentile.xlsx"
with pd.ExcelWriter(out) as w:
    df.to_excel(w, sheet_name="Result", index=False)
    cut.to_excel(w, sheet_name="Percentile Cutoffs", index=False)
    dist.to_excel(w, sheet_name="Score Distribution", index=False)
    summ.to_excel(w, sheet_name="Summary", index=False)
print(cut.to_string()); print(summ.to_string()); print(df.iloc[[0, 5586, 219037]].T.to_string())
