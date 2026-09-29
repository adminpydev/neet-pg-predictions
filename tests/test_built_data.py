import json

import pytest

from pipeline.sources import OUT

pytestmark = pytest.mark.skipif(not (OUT / "gujarat.json").exists(), reason="run pipeline.build first")


def load(name):
    return json.loads((OUT / name).read_text())


def test_results_shape():
    # no individual candidate is referenced in the repo; check structure only
    results = load("results.json")
    ranked = [r for r in results["rows"].values() if r[3] == "OK"]
    assert len(results["rows"]) == 273096 and len(ranked) == results["stats"]["appeared"]
    assert min(r[2] for r in ranked) == 1


def test_known_last_merits():
    guj = load("gujarat.json")
    find = lambda code, stream: [r for r in guj if r["code"] == code and r["stream"] == stream
                                 and r["seat"] == "GQ" and r["degree"] == "MD"]
    assert find("SMC", "Dermatology")[0]["last"]["1"]["SEBC"] == 132
    bj = find("AMED", "Radio-Diagnosis")[0]["last"]["1"]
    assert bj["OPEN"] == 28 and bj["SEBC"] == 14
