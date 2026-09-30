from pipeline.publish import stamp_sw, strip_rolls


def test_strip_rolls_drops_roll_keeps_rest():
    results = {"rows": {"PG1": ["26661000001", 400, 12345, "OK"], "PG2": ["26661000002", None, None, "ABSENT"]},
               "stats": {"appeared": 1}}
    out = strip_rolls(results)
    assert out == {"rows": {"PG1": ["", 400, 12345, "OK"], "PG2": ["", None, None, "ABSENT"]},
                   "stats": {"appeared": 1}}


def test_stamp_sw_sets_cache_name():
    assert stamp_sw('const CACHE = "pg-__BUILD__";', "abc123-1") == 'const CACHE = "pg-abc123-1";'
