from pipeline import sources
from pipeline.build import GUJ_GOVT_MCC, _spot_checks, gujarat_json, merit_json, validate


def test_gujarat_json_merges_rounds_and_drops_pwd_nri():
    last = {
        1: [{"course": "Dermatology ,Venereology & Leprosy", "code": "SMC", "values": {"GQ_SE": 132.0}},
            {"course": "PWD", "code": "SMC", "values": {"GQ_OPEN": 5.0}},
            {"course": "Anaesthesiology", "code": "SMC-NQ", "values": {"GQ_OPEN": 99999.0}}],
        2: [{"course": "Dermatology Venereology & Leprosy", "code": "SMC", "values": {"GQ_SE": 156.0, "INST_OPEN": 3.0}}],
    }
    names = {"SMC": "Surat Municipal Institute of Medical Education & Research (SMIMER), Surat"}
    recs = gujarat_json(last, names, fees={}, seats={})
    assert len(recs) == 1
    r = recs[0]
    assert r["code"] == "SMC" and r["seat"] == "GQ" and r["type"] == "Municipal (Govt)"
    assert r["stream"] == "Dermatology"
    assert r["last"] == {"1": {"SEBC": 132.0}, "2": {"SEBC": 156.0}}


def test_dnb_course_stays_separate_from_md():
    last = {1: [{"course": "General Medicine", "code": "SMC", "values": {"GQ_OPEN": 700.0}},
                {"course": "General Medicine (DNB)", "code": "SMC", "values": {"GQ_OPEN": 900.0}}]}
    recs = gujarat_json(last, {"SMC": "SMIMER"}, fees={}, seats={})
    assert sorted(r["degree"] for r in recs) == ["DNB", "MD"]


def test_merit_json_uses_general_list_for_gen():
    merit = {"GEN": [(17, 1, None), (8824, 510, None)], "SEBC": [(133, 9, 1.0), (8723, 506, 98.0)]}
    assert merit_json(merit) == {"GEN": [[17, 1], [8824, 510]], "SEBC": [[133, 1.0], [8723, 98.0]]}


def test_validate_reports_problems():
    problems = validate(results=[{"app": "A", "sno": 1}, {"app": "A", "sno": 2}],
                        merit={"GEN": [[10, 5], [9, 6]]}, gujarat=[{"code": "X", "college": "X"}],
                        expected_rows=3)
    assert any("row count" in p for p in problems)
    assert any("duplicate" in p for p in problems)
    assert any("GEN" in p for p in problems)
    assert any("name" in p for p in problems)


def ok_merit(**over):
    merit = {cat: [[1, 1], [2, 2]] for cat in sources.MERIT}
    merit.update(over)
    return merit


def test_validate_passes_on_clean_merit():
    assert validate([], ok_merit(), [], expected_rows=0) == []


def test_validate_empty_merit_list():
    assert "merit map SC is empty" in validate([], ok_merit(SC=[]), [], expected_rows=0)


def test_validate_missing_merit_category():
    merit = ok_merit()
    del merit["ST"]
    assert any("ST" in p and "missing" in p for p in validate([], merit, [], expected_rows=0))


def test_validate_none_in_merit_does_not_crash():
    problems = validate([], ok_merit(EWS=[[1, 1], [2, None], [3, 3]]), [], expected_rows=0)
    assert any("EWS" in p for p in problems)


def test_spot_check_requires_all_gujarat_govt_colleges_in_mcc():
    mcc = [{"college": c, "quota": "All India 50%"} for c in GUJ_GOVT_MCC.values()]
    mcc_problems = lambda recs: [p for p in _spot_checks({}, [], recs) if "MCC" in p]
    assert mcc_problems(mcc) == []
    assert mcc_problems(mcc[1:]) == [f"spot check MCC All India 50% missing {list(GUJ_GOVT_MCC)[0]}"]
    assert len(mcc_problems([dict(r, quota="DNB") for r in mcc])) == 7
