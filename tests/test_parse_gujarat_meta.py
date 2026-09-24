from pipeline.colleges import type_of
from pipeline.parse_gujarat import branch_key, match_college, parse_fees, parse_names, parse_seats

INST = """
001     AMED         B. J. Medical college, Ahmedabad
Anaesthesiology
1     F HETA KIRITBHAI SOMAIYA                782       EW 235
012     NAMOMED
                 Narendra Modi Medical College, Ahmedabad
123   PATEL FENIL                             1561
"""

FEES = """
                   Branch
                                                          B. J. Medical college, Ahmedabad
                                                  TUTION FEE GQ TUTION FEE MQ TUTION FEE NQ
MD-Anaesthesiology                                        130800 -                  -
                                                  Parul Institute Of Medical Sciences & Research, Post.
                      Branch                        Limda, Dist. Parul Institute Of Medical Sciences &
                                                          Research, Post. Limda, Dist. Vadodara
                                                  TUTION FEE GQ TUTION FEE MQ TUTION FEE NQ
MD-Anaesthesiology                                        1000000             1500000           1500000
"""

SEATS = """
                                                                B. J. Medical college, Ahmedabad
Branch                                                SANCTION_SEAT CURR_YR_SEAT AIQ GQ MQ NRI TOTAL
MD-Anaesthesiology                                               65           65 32 33   0   0    65
"""


def test_parse_names_only_known_codes():
    names = parse_names(INST, {"AMED", "NAMOMED"})
    assert names == {"AMED": "B. J. Medical college, Ahmedabad",
                     "NAMOMED": "Narendra Modi Medical College, Ahmedabad"}


def test_parse_fees():
    rows = parse_fees(FEES)
    assert rows[0][1:] == ("MD-Anaesthesiology", 130800, None)
    assert rows[1][1:] == ("MD-Anaesthesiology", 1000000, 1500000)
    assert "Parul Institute" in rows[1][0]


def test_parse_seats():
    assert parse_seats(SEATS) == [("B. J. Medical college, Ahmedabad", "MD-Anaesthesiology", 33, 0)]


def test_match_college_and_branch_key():
    names = {"AMED": "B. J. Medical college, Ahmedabad",
             "PRMED": "Parul Institute Of Medical Sciences & Research, Post. Limda, Dist. Vadodara"}
    assert match_college(parse_fees(FEES)[1][0], names) == "PRMED"
    assert match_college("Unknown College", names) is None
    assert branch_key("MD-Dermatology Venereology & Leprosy") == branch_key("Dermatology ,Venereology & Leprosy")
    assert branch_key("General Medicine (DNB)") == branch_key("MD-General Medicine")


def test_type_of():
    assert type_of("AMED") == "Govt"
    assert type_of("SMC") == "Municipal (Govt)"
    assert type_of("SOLMED") == "GMERS (Govt society)"
    assert type_of("PRMED") == "Private"
