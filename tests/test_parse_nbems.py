from pipeline.parse_nbems import parse_results

TEXT = """
                          NATIONAL BOARD OF EXAMINATIONS
    1             PG26120268                 26661000001                   331                   88859
  219038          PG26083665                 26661219410                   WITHHELD           WITHHELD
  273076          PG26215715                 26664248775                   ABSENT               ABSENT
  273088          PG26247319                 26664270202                     -14                265921
"""


def test_parse_results():
    rows = parse_results(TEXT)
    assert [r["sno"] for r in rows] == [1, 219038, 273076, 273088]
    assert rows[0] == {"sno": 1, "app": "PG26120268", "roll": "26661000001",
                       "score": 331, "rank": 88859, "status": "OK"}
    assert rows[1]["status"] == "WITHHELD" and rows[1]["score"] is None and rows[1]["rank"] is None
    assert rows[2]["status"] == "ABSENT"
    assert rows[3]["score"] == -14
