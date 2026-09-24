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
    assert r["quota"] == "All India 50%" and r["sector"] == "Govt" and r["stream"] == "General Surgery"
    assert r["college"] == "B. J. Medical College, Ahmedabad"
    assert r["last"] == {"GEN": None, "EWS": None, "SEBC": 12000, "SC": 15000, "ST": None}
    assert r["strayLast"] == {"GEN": 30000, "EWS": 30000, "SEBC": 30000, "SC": 30000, "ST": 30000}


def test_reserved_seats_only_count_for_their_category():
    recs = gujarat_records(round3_allotments(R3_ROWS))
    assert recs[0]["last"] == {"GEN": None, "EWS": None, "SEBC": 12000, "SC": 15000, "ST": None}


def allot(inst, rank=1000, rnd="2024 R3"):
    return {"round": rnd, "rank": rank, "quota": "AI", "inst": inst, "course": "M.D. (PATHOLOGY)",
            "cat": "Open", "cand": "General"}


def test_same_named_colleges_in_different_states_not_merged():
    recs = gujarat_records([allot("Govt. Medical College, Kozhikode, Kerala, 673008", 50000),
                            allot("Govt. Medical College, Baroda,Govt. Medical College, Baroda, Gujarat, 390001")])
    assert [(r["college"], r["last"]["GEN"]) for r in recs] == [("Govt. Medical College, Baroda", 1000)]


def test_gujarat_with_dash_pin_detected():
    recs = gujarat_records([allot("GMERS MEDICAL AND Hospital, Navsari, Gujarat-396445,M G G General Hospital")])
    assert len(recs) == 1 and recs[0]["college"].startswith("GMERS")


def test_generic_first_segment_two_gujarat_cities_two_records():
    recs = gujarat_records([allot("GMERS Medical College and Hospital, ,paddoc road, junagadh, Gujarat, 362001", 1),
                            allot("GMERS Medical College and Hospital, ,Halar Road,Valsad ,Gujarat, Gujarat, 396001", 2),
                            allot("GMERS Medical College and Hospital,", 99999, "2024 R1")])  # ambiguous: dropped
    assert sorted((r["college"], r["last"]["GEN"]) for r in recs) == [
        ("GMERS Medical College and Hospital, Junagadh", 1), ("GMERS Medical College and Hospital, Valsad", 2)]


def test_short_name_needs_unique_match_across_states():
    recs = gujarat_records([allot("Apollo Hospital, ,Bhat Gandhinagar, Gujarat, 382428", 1),
                            allot("Apollo Hospital, ,Greams Road, Chennai, Tamil Nadu, 600006", 2),
                            allot("Apollo Hospital,", 99999, "2024 R1")])
    assert [r["last"]["GEN"] for r in recs] == [1]
