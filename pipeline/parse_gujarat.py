import re

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
