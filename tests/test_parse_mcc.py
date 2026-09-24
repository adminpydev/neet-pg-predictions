from pipeline.parse_mcc import gujarat_records, round3_allotments, stray_allotments

BJ = "B. J. MEDICAL COLLEGE,Asarwa, Ahmedabad, Gujarat, 380016"
R3_ROWS = [
    # rank q1 i1 c1 rem1 q2 i2 c2 rem2 q3 i3 c3 cat_allot cat_cand opt remarks
    ["9000", "AI", "B. J. MEDICAL COLLEGE", "M.S. (GENERAL SURGERY)", "Reported", "-", "-", "-", "-",
     "-", "-", "-", "-", "-", "-", "Did not opt"],
    ["12000", "-", "-", "-", "-", "-", "-", "-", "-",
     "AI", BJ, "M.S. (GENERAL SURGERY)", "OBC", "OBC", "2", "Fresh Allotted"],
    ["15000", "-", "-", "-", "-", "-", "-", "-", "-",
     "AI", BJ, "M.S. (GENERAL SURGERY)", "SC", "SC", "3", "Fresh Allotted"],
    ["20000", "PS", "KMC MANIPAL", "M.D. (PAEDIATRICS)", "Reported", "-", "-", "-", "-",
     "-", "-", "-", "-", "-", "-", "Did not opt"],
]
STRAY_ROWS = [["1", "30000", "All India", BJ, "M.S. (GENERAL SURGERY)", "Open", "General", "Allotted"],
              ["2", "40000", "Armed Forces Medical", BJ, "M.S. (GENERAL SURGERY)", "Open", "General", "Allotted"]]


def test_round3_allotments():
    a = round3_allotments(R3_ROWS)
    assert a[0] == {"round": "2024 R1", "rank": 9000, "quota": "AI", "inst": "B. J. MEDICAL COLLEGE",
                    "course": "M.S. (GENERAL SURGERY)", "cat": "", "cand": "-"}
    assert a[1]["round"] == "2024 R3" and a[1]["cat"] == "OBC"


def test_seventeen_cell_rows_drop_empty_column():
    row = R3_ROWS[1][:10] + [None] + R3_ROWS[1][10:]
    assert round3_allotments([row])[0]["inst"] == BJ


def test_gujarat_records_last_rank_per_category():
    recs = gujarat_records(round3_allotments(R3_ROWS) + stray_allotments(STRAY_ROWS))
    assert len(recs) == 1  # KMC Manipal is not in Gujarat; Armed Forces quota excluded
    r = recs[0]
    assert r["quota"] == "AI" and r["sector"] == "Govt" and r["stream"] == "General Surgery"
    assert r["last"] == {"GEN": 30000, "EWS": 30000, "SEBC": 30000, "SC": 30000, "ST": 30000}


def test_reserved_seats_only_count_for_their_category():
    recs = gujarat_records(round3_allotments(R3_ROWS))
    assert recs[0]["last"] == {"GEN": None, "EWS": None, "SEBC": 12000, "SC": 15000, "ST": None}
