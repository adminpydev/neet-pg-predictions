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
