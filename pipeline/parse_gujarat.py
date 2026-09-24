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


CODE_LINE = re.compile(r"^\s*\d{3}\s+([A-Z]+)\s*(.*?)\s*$")
FEE_ROW = re.compile(r"^(\S.*?)\s{2,}(\d+|-)\s+(\d+|-)\s+(\d+|-)$")
SEAT_ROW = re.compile(r"^(\S.*?)\s{2,}(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$")


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def branch_key(s):
    return norm(re.sub(r"\s*\(DNB\)\s*$", "", re.sub(r"^(MD|MS)-", "", s.strip())))


def parse_names(text, codes):
    names, lines = {}, text.splitlines()
    for i, line in enumerate(lines):
        m = CODE_LINE.match(line)
        if not m or m.group(1) not in codes:
            continue
        name = m.group(2) or next((x.strip() for x in lines[i + 1:] if x.strip()), "")
        if len(name) > len(names.get(m.group(1), "")):
            names[m.group(1)] = name
    return names


def _college_tables(text, row_re, header_marker):
    """Yield (college_header, match) for each table row. The header is the text seen
    since the previous row, up to the column-header line."""
    buffer, header = [], ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = row_re.match(line)
        if m:
            buffer = []
            yield header, m
        elif header_marker in line:
            header = re.sub(r"\s+", " ", " ".join(buffer).replace("Branch", " ")).strip()
            buffer = []
        else:
            buffer.append(line)


def parse_fees(text):
    num = lambda v: int(v) if v.isdigit() else None
    return [(h, m.group(1), num(m.group(2)), num(m.group(3))) for h, m in _college_tables(text, FEE_ROW, "TUTION FEE")]


def parse_seats(text):
    return [(h, m.group(1), int(m.group(5)), int(m.group(6))) for h, m in _college_tables(text, SEAT_ROW, "SANCTION_SEAT")]


def match_college(header, names):
    h = norm(header)
    return next((code for code, name in names.items() if norm(name)[:30] in h), None)
