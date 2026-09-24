import urllib.request

from pipeline.sources import RAW, SOURCES


def fetch(sources=SOURCES, raw=RAW):
    """Download missing files. Returns manual sources that are still missing."""
    missing = []
    for rel, url in sources.items():
        path = raw / rel
        if path.exists():
            continue
        if url is None:
            missing.append(rel)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=300) as resp:
            path.write_bytes(resp.read())
    return missing
