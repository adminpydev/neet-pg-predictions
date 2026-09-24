import re, pandas as pd
G, E, RANK = 510, 99, 8839   # Gujarat 2025 general / SEBC merit equivalent to AIR 8839
NAMES = {}
NAMES = {c: n.strip() for _, c, n in (re.split(r"\s{2,}", l.strip(), 2) for l in open("guj/codes.txt"))}
NAMES.update({"JUMED": "GMERS Medical College, Junagadh", "VADMED": "GMERS Medical College, Vadnagar", "AMRMED": "Shantabaa Medical College, Amreli",
    "NDMED": "Dr. N. D. Desai Faculty of Medical Science, Nadiad", "VISMED": "Nootan Medical College, Visnagar", "PORMED": "GMERS Medical College, Porbandar",
    "MORMED": "GMERS Medical College, Morbi", "ANAMED": "Ananya College of Medicine and Research", "SWAMED": "Swaminarayan Institute of Medical Sciences",
    "KIRMED": "Kiran Medical College, Surat", "ZYMED": "Zydus Medical College, Dahod", "NAMOMED": "Narendra Modi Medical College, Ahmedabad"})
TYPE = {**{c: "Govt" for c in "AMED BMED SMED RMED JMED BHMED IKDMED".split()},
        **{c: "Municipal (Govt)" for c in "NHL SMC NAMOMED".split()},
        **{c: "GMERS (Govt society)" for c in "GOTMED SOLMED GMED PATMED VALMED HIMMED JUMED VADMED PORMED MORMED".split()}}
# fees: college header line then "Branch  GQ  MQ  NQ"
fees, col = {}, None
for l in open("guj/fees.txt"):
    t = l.strip()
    if not t: continue
    m = re.match(r"(.+?)\s{2,}(\d+|-)\s+(\d+|-)\s+(\d+|-)$", t)
    if m: fees[(col, re.sub(r"^(MD|MS)-", "", m.group(1)).strip().lower())] = m.groups()[1:]
    elif not re.search(r"TUTION|^Branch$", t): col = t.lower()
def fee(code, course, q):
    n = NAMES.get(code, "").lower()
    k = next((c for c in {c for c, _ in fees} if c and n and (c[:25] == n[:25])), None)
    f = fees.get((k, course.lower()))
    v = f[{"GQ": 0, "MQ": 1}[q]] if f else None
    return int(v) if v and v.isdigit() else None

L = pd.read_pickle("guj/glast.pkl")
L["Base"] = L.Code.str.replace(r"-(MQ|NQ)$", "", regex=True)
L["Seat"] = L.Code.str.extract(r"-(MQ|NQ)$")[0].fillna("GQ")
L = L[L.Seat != "NQ"]
L = L[~L.Course.str.startswith("PWD")]
L["Course"] = L.Course.str.replace(" ,", ",").str.replace("Dermatology, Venereology", "Dermatology Venereology")
L = L.drop_duplicates(["Round", "Course", "Code"])
rows = []
for (course, code), d in L.groupby(["Course", "Code"]):
    d = d.set_index("Round"); base, seat = d.Base.iloc[0], d.Seat.iloc[0]
    rec = {"Course": course, "College": NAMES.get(base, base), "Code": base, "Type": TYPE.get(base, "Private"),
           "Seat": "Govt Quota" if seat == "GQ" else "Management Quota"}
    best = 0
    for r in (1, 2, 3, 4):
        o = d.GQ_OPEN.get(r); se = d.GQ_SE.get(r) if seat == "GQ" else None
        rec[f"R{r} OPEN last merit"] = o; rec[f"R{r} SEBC last merit"] = se
        ratio = max([x for x in [o / G if pd.notna(o) else None, se / E if pd.notna(se) else None] if x] or [0])
        rec[f"R{r} ok"] = ratio >= 1; best = max(best, ratio)
    rec["Best ratio"] = best
    rec["Chance (OBC/SEBC)"] = "High" if best >= 1.15 else "Good" if best >= 1 else "Borderline" if best >= 0.9 else "Low"
    rec["Earliest round reachable"] = next((f"Round {r}" for r in (1, 2, 3, 4) if rec[f"R{r} ok"]), "-")
    rec["Annual tuition fee (Rs)"] = fee(base, course, seat)
    rows.append(rec)
Gj = pd.DataFrame(rows).drop(columns=[f"R{r} ok" for r in (1, 2, 3, 4)])
Gj = Gj.replace(99999.0, "Vacant")
Gj["o"] = Gj["Chance (OBC/SEBC)"].map({"High": 0, "Good": 1, "Borderline": 2, "Low": 3})
Gj["t"] = Gj.Type.map({"Govt": 0, "Municipal (Govt)": 1, "GMERS (Govt society)": 2, "Private": 3})
Gj = Gj.sort_values(["o", "t", "Earliest round reachable", "Course"]).drop(columns=["o", "t", "Best ratio"])
GP = Gj[Gj["Chance (OBC/SEBC)"] != "Low"]

C = pd.read_pickle("mcc_obc.pkl")
cols = ["Stream", "Degree", "Institute", "State", "Sector", "Quota", "Chance (OBC)", "Rank used for chance", "OBC-eligible Closing Rank",
        "Closing Rank (all cat)", "2025 Stray OBC-eligible Closing", "Rounds"]
ok = C["Chance (OBC)"].isin(["High", "Good", "Borderline"])
MG = C[(C.State == "Gujarat") & (C["Chance (OBC)"] != "Not eligible (special quota)")].sort_values(["Chance (OBC)", "Sector", "Stream"])[cols]
MA = C[ok].copy(); MA["o"] = MA["Chance (OBC)"].map({"High": 0, "Good": 1, "Borderline": 2})
MA = MA.sort_values(["Stream", "o", "Rank used for chance"])[cols]

# stream summary: Gujarat state + Gujarat MCC + all-India MCC Govt
def stream_of(c):
    k = re.sub(r"\s", "", c.upper())
    for a, b in [("RADIO", "Radio-Diagnosis"), ("DERM", "Dermatology"), ("GENERALMEDICINE", "General Medicine"), ("GENERALSURGERY", "General Surgery"),
                 ("PAEDIATRIC", "Paediatrics"), ("D.C.H", "Paediatrics"), ("ORTHO", "Orthopaedics"), ("GYN", "Obstetrics & Gynaecology"), ("ANAES", "Anaesthesiology"),
                 ("OPHTHAL", "Ophthalmology"), ("OTO", "ENT"), ("ENT", "ENT"), ("PSYCH", "Psychiatry"), ("RESPIR", "Respiratory Medicine"), ("EMERGENCY", "Emergency Medicine"),
                 ("RADIATION", "Radiation Oncology"), ("PATHOLOGY", "Pathology"), ("MICRO", "Microbiology"), ("PHARMA", "Pharmacology"), ("PHYSIO", "Physiology"),
                 ("BIOCHEM", "Biochemistry"), ("ANATOMY", "Anatomy"), ("FORENSIC", "Forensic Medicine"), ("COMMUNITY", "Community Medicine"), ("FAMILY", "Family Medicine"),
                 ("TRANSFUSION", "Transfusion Medicine (IHBT)"), ("PALLIATIVE", "Palliative Medicine"), ("GERIATRIC", "Geriatrics"), ("PHYSICAL", "PMR")]:
        if a in k: return b
    return c
GP2 = GP.assign(Stream=GP.Course.map(stream_of))
gov = GP2.Type != "Private"
SS = pd.DataFrame({
    "Gujarat State - Govt/GMERS/Municipal (GQ)": GP2[gov].groupby("Stream").size(),
    "Gujarat State - Private (GQ+MQ)": GP2[~gov].groupby("Stream").size(),
    "MCC - Gujarat colleges": C[ok & (C.State == "Gujarat")].groupby("Stream").size(),
    "MCC - Govt All India (AIQ)": C[ok & (C.Sector == "Govt")].groupby("Stream").size(),
    "MCC - Deemed All India": C[ok & (C.Sector == "Private (Deemed)")].groupby("Stream").size()}).fillna(0).astype(int)
top = GP2[gov & GP2["Chance (OBC/SEBC)"].isin(["High", "Good", "Borderline"])].groupby("Stream").apply(
    lambda d: "; ".join((d.College + " [" + d["Chance (OBC/SEBC)"] + ", " + d["Earliest round reachable"] + "]").head(4)), include_groups=False)
SS["Best Gujarat Govt options"] = top; SS = SS.fillna("").sort_values("Gujarat State - Govt/GMERS/Municipal (GQ)", ascending=False).reset_index().rename(columns={"index": "Stream"})

notes = pd.DataFrame({"Item": ["Candidate", "Score / AIR", "Category", "Preference", "Gujarat merit equivalent", "Gujarat data", "MCC data", "Chance rule",
    "Gujarat eligibility", "Not included", "Caveat"], "Detail": ["PG11111111", "512 / 8839 (top 3.4%)", "OBC (= SEBC in Gujarat state counselling)", "Gujarat first",
    f"In Gujarat 2025 merit list, AIR 8839 fell at General merit ~{G} and SEBC merit ~{E}. Used these to compare with Gujarat 2025 last merit.",
    "ACPPGMEC Gujarat 2025-26 Last Merit Rounds 1-4, merit lists, seat and fee lists (medadmgujarat.org)",
    "MCC 2024 Round 1-3 final allotment + 2025 stray round (mcc.nic.in). OBC can take Open or OBC seats; Deemed seats have no reservation.",
    "Gujarat: best of (Open last merit / 510, SEBC last merit / 99). MCC: last OBC-eligible rank / 8839. High >= 1.15, Good >= 1, Borderline >= 0.9.",
    "Gujarat state quota (GQ/MQ) needs Gujarat domicile / eligibility per ACPPGMEC rules; SEBC seats need Gujarat SEBC certificate. MCC AIQ OBC needs central OBC-NCL certificate.",
    "Institutional (university) seats, in-service seats, NRI seats, DNB-only Gujarat rows are in data but not used for chance.",
    "Based on 2024/2025 cutoffs; 2026 will shift. Seat counts per college/branch are small (often 1-4 SEBC seats), so check seat matrix when 2026 counselling opens."]})
out = "/Users/vedantparikh/Downloads/PG11111111 Admission Possibilities (OBC, Gujarat).xlsx"
with pd.ExcelWriter(out) as w:
    notes.to_excel(w, sheet_name="Summary", index=False)
    SS.to_excel(w, sheet_name="Stream-wise Options", index=False)
    GP.to_excel(w, sheet_name="Gujarat State Options", index=False)
    MG.to_excel(w, sheet_name="MCC Gujarat Colleges", index=False)
    MA.to_excel(w, sheet_name="MCC All India Options", index=False)
    Gj.to_excel(w, sheet_name="Gujarat All Last Merits", index=False)
    pd.read_pickle("s25.pkl").to_excel(w, sheet_name="MCC 2025 Stray Allotments", index=False)
print(Gj["Chance (OBC/SEBC)"].value_counts().to_dict(), "fees found", Gj["Annual tuition fee (Rs)"].notna().mean().round(2))
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 200)
print(SS.to_string())
