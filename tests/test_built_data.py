import json

import pytest

from pipeline.sources import OUT

pytestmark = pytest.mark.skipif(not (OUT / "gujarat.json").exists(), reason="run pipeline.build first")


def load(name):
    return json.loads((OUT / name).read_text())


def test_candidate_row():
    # reference candidate found by rank so no real application number lives in the repo
    rows = load("results.json")["rows"]
    assert [r[1:] for r in rows.values() if r[2] == 8839] == [[512, 8839, "OK"]]


def test_known_last_merits():
    guj = load("gujarat.json")
    find = lambda code, stream: [r for r in guj if r["code"] == code and r["stream"] == stream
                                 and r["seat"] == "GQ" and r["degree"] == "MD"]
    assert find("SMC", "Dermatology")[0]["last"]["1"]["SEBC"] == 132
    bj = find("AMED", "Radio-Diagnosis")[0]["last"]["1"]
    assert bj["OPEN"] == 28 and bj["SEBC"] == 14
