import re

import pdfplumber

MERIT_ROW = re.compile(
    r"^\s*\d{5}\s+2566\d{7}\s+([\d.]+)\s+(?:(?:SE|SC|ST|EW)-([\d.]+)\s+)?\S+\s+"
    r"(?:(?:SE|SC|ST|EW)-[\d.]+\s+)?([\d.]+)\s+-?\d+\s")


def parse_merit(text):
    rows = []
    for line in text.splitlines():
        m = MERIT_ROW.match(line)
        if m:
            gen, cat, air = m.groups()
            rows.append((int(float(air)), int(float(gen)), float(cat) if cat else None))
    return rows


LAST_COLS = [f"{g}_{c}" for g in ("GQ", "INST", "INSV") for c in ("OPEN", "EWS", "SC", "ST", "SE")]
NUM = re.compile(r"[\d.]+")


def last_merit_rows(pages):
    out, course = [], None
    for words in pages:
        lines = {}
        for word in words:
            lines.setdefault(round(word["top"]), []).append(word)
        header = next((ws for ws in lines.values() if [x["text"] for x in ws][:2] == ["College", "OPEN"]), None)
        if not header:
            continue
        xs = [x["x1"] for x in header[1:]]
        pending = None
        for top in sorted(lines):
            ws = [x for x in lines[top] if x["text"] != "*"]
            if not ws or top <= header[0]["top"]:
                continue
            if all(NUM.fullmatch(x["text"]) for x in ws):
                pending = {LAST_COLS[min(range(len(xs)), key=lambda i: abs(xs[i] - x["x1"]))]: float(x["text"])
                           for x in ws}
            elif ws[0]["x0"] < 85:
                course, pending = " ".join(x["text"] for x in ws), None
            elif pending is not None:
                out.append({"course": course, "code": " ".join(x["text"] for x in ws), "values": pending})
                pending = None
    return out


def read_last_merit(path):
    with pdfplumber.open(path) as pdf:
        return last_merit_rows([page.extract_words() for page in pdf.pages])
