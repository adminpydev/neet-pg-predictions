import re, pandas as pd
RANK, APP, SCORE = 8839, "PG11111111", 512
r = pd.read_pickle("r3.pkl"); s = pd.read_pickle("stray.pkl")
r.columns = "rank q1 i1 c1 rem1 q2 i2 c2 rem2 q3 i3 c3 cat_allot cat_cand opt remarks".split()
s.columns = "sno rank quota inst course cat_allot cat_cand remarks".split()
QN = {"All India": "AI", "DNB Quota": "AD", "Self-Financed Merit Seat": "PS", "Non-Resident Indian": "NR", "Delhi University Quota": "DU",
      "Armed Forces Medical": "AF", "IP University Quota": "IP", "Muslim Minority Quota": "MM", "Aligarh Muslim University": "AM",
      "Banaras Hindu University": "BH", "Jain Minority Quota": "JM"}
QUOTA = {"AI": "All India 50%", "AD": "DNB", "PS": "Deemed (Self-financed merit)", "NR": "NRI", "DU": "Delhi University", "IP": "IP University",
         "AF": "Armed Forces", "AM": "AMU", "BH": "BHU", "JM": "Jain Minority", "MM": "Muslim Minority"}
SECTOR = {"AI": "Govt", "DU": "Govt", "IP": "Govt", "AF": "Govt", "AM": "Govt", "BH": "Govt",
          "PS": "Private (Deemed)", "NR": "Private (Deemed)", "JM": "Private (Deemed)", "MM": "Private (Deemed)", "AD": "DNB Hospital"}
STREAMS = [("PAEDIATRICSURGERY", "Paediatric Surgery"), ("RADIO-DIAG", "Radio-Diagnosis"), ("RADIODIAG", "Radio-Diagnosis"),
    ("DERM", "Dermatology"), ("GENERALMEDICINE", "General Medicine"), ("GENERALSURGERY", "General Surgery"),
    ("PAEDIATRIC", "Paediatrics"), ("CHILDHEALTH", "Paediatrics"), ("ORTHO", "Orthopaedics"), ("GYNAE", "Obstetrics & Gynaecology"),
    ("OBSTETRIC", "Obstetrics & Gynaecology"), ("ANAES", "Anaesthesiology"), ("OPHTHAL", "Ophthalmology"), ("E.N.T", "ENT"),
    ("OTO", "ENT"), ("PSYCH", "Psychiatry"), ("RESPIRATORY", "Respiratory Medicine"), ("PULMONARY", "Respiratory Medicine"),
    ("CHEST", "Respiratory Medicine"), ("EMERGENCY", "Emergency Medicine"), ("RADIOTHERAPY", "Radiation Oncology"),
    ("RADIO-THERAPY", "Radiation Oncology"), ("RADIATIONONCOLOGY", "Radiation Oncology"), ("RADIATIONMEDICINE", "Radiation Oncology"),
    ("PATHOLOGY", "Pathology"), ("MICROBIO", "Microbiology"), ("BACTERIO", "Microbiology"), ("PHARMAC", "Pharmacology"),
    ("PHYSIOLOGY", "Physiology"), ("BIOCHEM", "Biochemistry"), ("ANATOMY", "Anatomy"), ("FORENSIC", "Forensic Medicine"),
    ("COMMUNITYHEALTHANDADMN", "Hospital Administration"), ("HOSPITALADMIN", "Hospital Administration"), ("HEALTHADMIN", "Hospital Administration"),
    ("COMMUNITY", "Community Medicine"), ("PREVENTIVE", "Community Medicine"), ("PUBLICHEALTH", "Community Medicine"),
    ("EPIDEM", "Community Medicine"), ("FAMILYMEDICINE", "Family Medicine"), ("TRANSFUSION", "Transfusion Medicine (IHBT)"),
    ("NUCLEAR", "Nuclear Medicine"), ("PALLIATIVE", "Palliative Medicine"), ("GERIATRIC", "Geriatrics"), ("SPORTS", "Sports Medicine"),
    ("PHYSICALMED", "PMR"), ("PHY.MEDICINE", "PMR"), ("TRAUMATOLOGY", "Traumatology & Surgery"), ("NEUROSURGERY", "Neuro Surgery (6 yr)"),
    ("CARDIOVASCULAR", "CTVS (6 yr)"), ("PLASTIC", "Plastic Surgery (6 yr)"), ("DIABETOLOGY", "Diabetology"), ("TROPICAL", "Tropical Medicine"),
    ("AEROSPACE", "Aerospace Medicine"), ("LABORATORY", "Laboratory Medicine")]
def stream(c):
    k = re.sub(r"\s", "", c.upper())
    return next((v for key, v in STREAMS if key in k), "Other")
def degree(c):
    if "(NBEMS-DIPLOMA)" in c: return "DNB Diploma"
    if "(NBEMS)" in c: return "DNB"
    if re.match(r"(PG )?DIP", c, re.I): return "Diploma"
    return "MS" if c.startswith("M.S") else "MD/MS" if "MS (" in c or c.startswith("MD/MS") else "MD"
def key(i): return re.sub(r"[^A-Z0-9 ]", "", re.sub(r"\s+", " ", i.split(",")[0].upper())).strip()
states = {}
for full in pd.concat([r.i3, s.inst]):
    m = re.search(r",\s*([A-Za-z .()&]+?)\s*,?\s*(\d{6})\s*$", full)
    if m: states.setdefault(key(full), m.group(1).strip())

recs = []
for n, (q, i, c) in enumerate([("q1", "i1", "c1"), ("q2", "i2", "c2"), ("q3", "i3", "c3")], 1):
    d = r[(r[q] != "-") & (r[i] != "") & (r[c] != "")]
    cat = d.cat_allot if n == 3 else pd.Series("", index=d.index)
    recs.append(pd.DataFrame({"src": "2024", "round": f"2024 R{n}", "rank": d["rank"].astype(int), "q": d[q], "inst": d[i], "course": d[c], "cat": cat, "cand": d.cat_cand}))
st = s[(s.inst != "") & (s.course != "")]
recs.append(pd.DataFrame({"src": "2025 Stray", "round": "2025 Stray", "rank": st["rank"].astype(int), "q": st.quota.map(QN).fillna(st.quota),
                          "inst": st.inst, "course": st.course, "cat": st.cat_allot, "cand": st.cat_cand}))
A = pd.concat(recs, ignore_index=True)
A["key"] = A.inst.map(key); A = A[A.key != ""]
A["Stream"] = A.course.map(stream); A["Degree"] = A.course.map(degree)
full = A.groupby("key").inst.agg(lambda x: max(x, key=len))
A["Institute"] = A.key.map(full).str.split(",").str[0].str.strip()
A["State"] = A.key.map(states).fillna("")
A["Sector"] = A.q.map(SECTOR).fillna("Other"); A["Quota"] = A.q.map(QUOTA).fillna(A.q)

g = ["Stream", "Degree", "Institute", "State", "Sector", "Quota"]
def agg(d):
    op = d[(d.cat == "Open") | (d.cand == "General")]["rank"]
    return pd.Series({"Allotments": len(d), "Opening Rank (all cat)": d["rank"].min(), "Closing Rank (all cat)": d["rank"].max(),
                      "General Closing Rank": op.max() if len(op) else None, "Rounds": ", ".join(sorted(d["round"].unique()))})
T = {}
for src in ["2024", "2025 Stray"]:
    T[src] = A[A.src == src].groupby(g).apply(agg).reset_index()
C = T["2024"].merge(T["2025 Stray"][g + ["Closing Rank (all cat)", "General Closing Rank"]].rename(columns={
    "Closing Rank (all cat)": "2025 Stray Closing (all cat)", "General Closing Rank": "2025 Stray General Closing"}), on=g, how="outer")
C["Allotments"] = C["Allotments"].fillna(0).astype(int)
ELIG = {"All India 50%", "Deemed (Self-financed merit)", "DNB"}
def chance(row):
    op = pd.Series([row["General Closing Rank"], row["2025 Stray General Closing"]]).max()
    allc = pd.Series([row["Closing Rank (all cat)"], row["2025 Stray Closing (all cat)"]]).max()
    if row.Quota not in ELIG: return pd.Series(["Not eligible (special quota)", None, ""])
    if pd.isna(op): return pd.Series(["Unclear (no General data)", None, f"All-category closing {allc:.0f}; General cutoff lower" if pd.notna(allc) else ""])
    b, basis = op, "Last General-category rank allotted"
    lab = "High" if b >= RANK * 1.15 else "Good" if b >= RANK else "Borderline" if b >= RANK * 0.9 else "Low"
    return pd.Series([lab, b, basis])
C[["Chance (as General)", "Rank used for chance", "Basis"]] = C.apply(chance, axis=1)
order = {"High": 0, "Good": 1, "Borderline": 2}
C = C.sort_values(["Stream", "Degree", "Rank used for chance"], ascending=[True, True, True])
P = C[C["Chance (as General)"].isin(["High", "Good", "Borderline"])].copy()
P["o"] = P["Chance (as General)"].map(order); P = P.sort_values(["Stream", "o", "Rank used for chance"]).drop(columns="o")

SS = P.pivot_table(index="Stream", columns="Sector", values="Institute", aggfunc="count", fill_value=0)
SS["Total options"] = SS.sum(axis=1)
best = P[P["Chance (as General)"].isin(["High", "Good", "Borderline"])].sort_values("Rank used for chance").groupby("Stream").head(3)
SS["Top options (Open closing nearest to rank)"] = best.assign(t=best.Institute + " [" + best.Degree + ", " + best.Sector + ", " + best["Rank used for chance"].astype(int).astype(str) + "]").groupby("Stream").t.agg("; ".join)
SS = SS.fillna("").sort_values("Total options", ascending=False).reset_index()

notes = pd.DataFrame({"Item": ["Candidate", "Score (out of 720)", "NEET-PG 2026 All India Rank", "Percentile (<= score)", "Category assumed",
    "Data source 1", "Data source 2", "Chance rule", "Govt / Private", "Limitations"], "Detail": [APP, SCORE, RANK, 96.69, "General (Open seat). Tell me category for re-run.",
    "MCC Final Allotment Result Round 3, PG Counselling 2024 (cumulative Round 1-3, mcc.nic.in)",
    "MCC Final Result Stray Vacancy Round, PG Counselling 2025 (mcc.nic.in). MCC no longer hosts 2025 Round 1-3 ranked results.",
    "General closing = highest rank at which a General-category candidate (or an Open seat) was allotted that college+course in 2024 R1-R3 or 2025 stray. High >= 1.15x rank, Good >= rank, Borderline >= 0.9x rank. Only All India 50%, Deemed and DNB quotas counted (AFMS, NRI, minority, DU/IP/BHU/AMU need special eligibility).",
    "From MCC quota: AIQ/Central Univ = Govt; Deemed/NRI/Minority = Private (Deemed); DNB quota = NBEMS hospitals (mostly private/trust).",
    "Only MCC counselling (AIQ 50% govt seats, central, deemed, DNB). State quota counselling (other 50% govt seats + state private) not included. Closing ranks change yearly; 2026 had ~266k candidates, more than 2024, so rank 8839 is slightly stronger in 2026."]})
cols = g + ["Chance (as General)", "Rank used for chance", "Basis", "General Closing Rank", "Closing Rank (all cat)", "Opening Rank (all cat)",
            "2025 Stray General Closing", "2025 Stray Closing (all cat)", "Allotments", "Rounds"]
S25 = A[A.src == "2025 Stray"][["rank", "Quota", "Sector", "Institute", "State", "Stream", "Degree", "cat"]].rename(columns={"rank": "Rank", "cat": "Allotted Category"}).sort_values("Rank")
out = "/Users/vedantparikh/Downloads/PG11111111 Admission Possibilities.xlsx"
with pd.ExcelWriter(out) as w:
    notes.to_excel(w, sheet_name="Summary", index=False)
    SS.to_excel(w, sheet_name="Stream-wise Options", index=False)
    P[cols].to_excel(w, sheet_name="Possible Colleges", index=False)
    C[cols].to_excel(w, sheet_name="All Closing Ranks", index=False)
    S25.to_excel(w, sheet_name="2025 Stray Round Allotments", index=False)
print(len(A), len(C), len(P)); print(C["Chance (as General)"].value_counts().to_string())
print(SS.drop(columns="Top options (Open closing nearest to rank)").to_string())
print(A.Stream.eq("Other").sum(), A[A.Stream == "Other"].course.unique()[:10])
