from pipeline.publish import strip_rolls


def test_strip_rolls_drops_roll_keeps_rest():
    results = {"rows": {"PG1": ["26661000001", 512, 8839, "OK"], "PG2": ["26661000002", None, None, "ABSENT"]},
               "stats": {"appeared": 1}}
    out = strip_rolls(results)
    assert out == {"rows": {"PG1": ["", 512, 8839, "OK"], "PG2": ["", None, None, "ABSENT"]},
                   "stats": {"appeared": 1}}
