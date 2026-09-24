from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "web" / "data"

GUJ = "http://medadmgujarat.ncode.in/web/PG2025/MDMS"
MCC = "https://cdnbbsr.s3waas.gov.in/s3e0f7a4d0ef9b84b83b693bbf3feb8e6e/uploads"

NBEMS = "nbems/NEET-PG 2026 Published Result_DS.pdf"
MCC_R3 = "mcc/r3_2024.pdf"
MCC_STRAY = "mcc/stray.pdf"
GUJ_INST = "gujarat/inst.pdf"
GUJ_SEATS = "gujarat/seats.pdf"
GUJ_FEES = "gujarat/fees.pdf"
MERIT = {"GEN": "gujarat/gen0.pdf", "SEBC": "gujarat/se0.pdf", "SC": "gujarat/sc0.pdf",
         "ST": "gujarat/st0.pdf", "EWS": "gujarat/ew0.pdf"}
LAST_MERIT = {1: "gujarat/r1_last_merit_xyz1.pdf", 2: "gujarat/r2_last_merit_22122025.pdf",
              3: "gujarat/r3_last_merit_1.pdf", 4: "gujarat/r4_last_merit.pdf"}

SOURCES = {
    NBEMS: None,  # downloaded manually from NBEMS
    MCC_R3: f"{MCC}/2025/01/2025012533.pdf",
    MCC_STRAY: f"{MCC}/2026/02/20260223177387794.pdf",
    GUJ_INST: f"{GUJ}/inst_branchwise_adm_07042026.pdf",
    GUJ_SEATS: f"{GUJ}/PG%20MD%20MS%20SEATS%202025-26.pdf",
    GUJ_FEES: f"{GUJ}/PG%20MD%20MS%20FEES%202025-26.pdf",
    MERIT["GEN"]: f"{GUJ}/MERIT/mdms_gen_merit.pdf",
    MERIT["SEBC"]: f"{GUJ}/MERIT/mdms_se_merit.pdf",
    MERIT["SC"]: f"{GUJ}/MERIT/mdms_sc_merit.pdf",
    MERIT["ST"]: f"{GUJ}/MERIT/mdms_st_merit.pdf",
    MERIT["EWS"]: f"{GUJ}/MERIT/mdms_ew_merit.pdf",
    LAST_MERIT[1]: f"{GUJ}/R1/r1_last_merit_xyz1.pdf",
    LAST_MERIT[2]: f"{GUJ}/R2/r2_last_merit_22122025.pdf",
    LAST_MERIT[3]: f"{GUJ}/R3/r3_last_merit_1.pdf",
    LAST_MERIT[4]: f"{GUJ}/R4/r4_last_merit.pdf",
}
