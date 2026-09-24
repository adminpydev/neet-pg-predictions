GOVT = {"AMED", "BMED", "SMED", "RMED", "JMED", "BHMED", "IKDMED"}
MUNICIPAL = {"NHL", "SMC", "NAMOMED"}
GMERS = {"GOTMED", "SOLMED", "GMED", "PATMED", "VALMED", "HIMMED", "JUMED", "VADMED", "PORMED", "MORMED"}


def type_of(code):
    if code in GOVT:
        return "Govt"
    if code in MUNICIPAL:
        return "Municipal (Govt)"
    if code in GMERS:
        return "GMERS (Govt society)"
    return "Private"
