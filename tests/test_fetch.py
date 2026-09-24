from pipeline.fetch import fetch


def test_manual_source_reported_missing(tmp_path):
    assert fetch({"nbems/result.pdf": None}, tmp_path) == ["nbems/result.pdf"]


def test_existing_file_not_downloaded(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "x.pdf").write_bytes(b"old")
    assert fetch({"a/x.pdf": "http://invalid.invalid/x.pdf"}, tmp_path) == []
    assert (tmp_path / "a" / "x.pdf").read_bytes() == b"old"
