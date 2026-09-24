from pipeline.parse_gujarat import parse_merit

TEXT = """
 User ID Roll No       GEN       CAT        Uni.       Uni.Cat  All India      Score   NAME
   40377 25661005088   0001                 MS-0001                     17     683   F AGRAWAL HIRAK KESHAV             GOVT. MEDICAL COLLEGE BARODA
   44945 25661238018   1162.50   SE-241.5   SU-169.7   SE-039.5     19838.00     516   M BADMALIYA AJAYKUMAR MAHESHBHAI      P. D. U. GOVT. MEDICAL COLLEGE RAJKOT
   44488 25661224006   0057     SC-001.0    SU-0005   SC-001.0          895     629   M BADHIYA HITESHKUMAR PURABHAI     P. D. U. GOVT. MEDICAL COLLEGE RAJKOT
   40504 25661085097   0300                SPU-0001                    5321     581   M DSYLVA MIT PARIKSHAT             NOOTAN MEDICAL COLLEGE
"""


def test_parse_merit():
    assert parse_merit(TEXT) == [(17, 1, None), (19838, 1162, 241.5), (895, 57, 1.0), (5321, 300, None)]
