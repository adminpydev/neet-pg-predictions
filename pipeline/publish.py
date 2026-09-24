"""Build the static GitHub Pages site into site/ and optionally push it to gh-pages.

Usage:
    .venv/bin/python -m pipeline.publish          # build site/ only
    .venv/bin/python -m pipeline.publish --push   # build and force-push site/ to origin gh-pages
"""
import json
import shutil
import subprocess
import sys

from pipeline.sources import OUT, ROOT

SITE = ROOT / "site"
WEB = ROOT / "web"
PAGE_FILES = ["index.html", "styles.css", "app.js", "engine.js", "favicon.svg"]
DATA_FILES = ["merit_map.json", "gujarat.json", "mcc.json", "meta.json"]


def strip_rolls(results):
    """Published copy keeps app number, score, rank, status; roll numbers are dropped."""
    rows = {app: ["", score, rank, status] for app, (_, score, rank, status) in results["rows"].items()}
    return {"rows": rows, "stats": results["stats"]}


def build():
    if not (OUT / "results.json").exists():
        raise SystemExit("web/data missing: run .venv/bin/python -m pipeline.build first")
    shutil.rmtree(SITE, ignore_errors=True)
    (SITE / "data").mkdir(parents=True)
    for f in PAGE_FILES:
        shutil.copy(WEB / f, SITE / f)
    for f in DATA_FILES:
        shutil.copy(OUT / f, SITE / "data" / f)
    results = json.loads((OUT / "results.json").read_text())
    (SITE / "data" / "results.json").write_text(json.dumps(strip_rolls(results), separators=(",", ":")))
    (SITE / ".nojekyll").touch()  # serve files as-is, no Jekyll processing
    print(f"built {SITE}")


def push():
    # ponytail: gh-pages is a throwaway single-commit branch, so history never accumulates old data
    git = lambda *a: subprocess.run(["git", *a], cwd=SITE, check=True)
    git("init", "-q", "-b", "gh-pages")
    git("add", "-A")
    git("commit", "-qm", "Deploy site")
    remote = subprocess.run(["git", "remote", "get-url", "origin"], cwd=ROOT, check=True,
                            capture_output=True, text=True).stdout.strip()
    git("push", "-f", remote, "gh-pages")
    shutil.rmtree(SITE / ".git")


if __name__ == "__main__":
    build()
    if "--push" in sys.argv:
        push()
