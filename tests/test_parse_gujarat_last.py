from pipeline.parse_gujarat import last_merit_rows


def w(text, x0, x1, top):
    return {"text": text, "x0": x0, "x1": x1, "top": top}


HEADER = [w("College", 84, 125, 100)] + [
    w(t, x1 - 25, x1, 100) for t, x1 in zip(
        "OPEN EWS SC ST SE OPEN EWS SC ST SE OPEN EWS SC ST SE".split(),
        [234, 278, 318, 358, 399, 447, 486, 510, 547, 584, 648, 684, 720, 756, 792])]

PAGE = HEADER + [
    w("Anaesthesiology", 78, 170, 128),
    w("*", 72, 79, 143), w("1102", 209, 234, 143), w("392", 259, 278, 143), w("396", 380, 399, 143),
    w("AMED", 90, 119, 149),
    w("99999", 202, 234, 169),
    w("BHUMED-MQ", 90, 155, 175),
]


def test_last_merit_rows():
    rows = last_merit_rows([PAGE])
    assert rows == [
        {"course": "Anaesthesiology", "code": "AMED", "values": {"GQ_OPEN": 1102.0, "GQ_EWS": 392.0, "GQ_SE": 396.0}},
        {"course": "Anaesthesiology", "code": "BHUMED-MQ", "values": {"GQ_OPEN": 99999.0}},
    ]


def test_page_without_header_ignored():
    assert last_merit_rows([[w("Anaesthesiology", 78, 170, 128)]]) == []
