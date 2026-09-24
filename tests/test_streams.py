import pytest

from pipeline.streams import degree_of, stream_of


@pytest.mark.parametrize("course,stream", [
    ("M.D. (RADIO- DIAGNOSIS)", "Radio-Diagnosis"),
    ("Radio Diagnosis", "Radio-Diagnosis"),
    ("Dermatology ,Venereology & Leprosy", "Dermatology"),
    ("M.D. (DERM.,VENE. and LEPROSY)/ (DERMATOLOGY)", "Dermatology"),
    ("General Medicine (DNB)", "General Medicine"),
    ("Diploma in Anesthesiology (D.A.)", "Anaesthesiology"),
    ("M.D. (ANAESTHESIOLOGY )", "Anaesthesiology"),
    ("Diploma in Paediatrics (D.C.H.)", "Paediatrics"),
    ("(NBEMS) Paediatric Surgery (Direct 6 Years Course)", "Paediatric Surgery"),
    ("Otorhinolaryngology/ENT", "ENT"),
    ("Tuberculosis & Respiratory Medicine", "Respiratory Medicine"),
    ("Radiation oncology", "Radiation Oncology"),
    ("Immuno Haematology & Blood Transfusion", "Transfusion Medicine (IHBT)"),
    ("M.D. (COMMUNITY HEALTH and ADMN.)", "Hospital Administration"),
    ("M.D. (PREVENTIVE and SOCIAL MEDICINE)/ COMMUNITY MEDICINE", "Community Medicine"),
    ("Obstetrics & Gynaecology", "Obstetrics & Gynaecology"),
    ("Something New", "Other"),
])
def test_stream_of(course, stream):
    assert stream_of(course) == stream


@pytest.mark.parametrize("course,degree", [
    ("(NBEMS-DIPLOMA) PAEDIATRICS", "DNB Diploma"),
    ("(NBEMS) GENERAL MEDICINE", "DNB"),
    ("General Medicine (DNB)", "DNB"),
    ("DIPLOMA IN ANAESTHESIOLOGY", "Diploma"),
    ("Diploma in Paediatrics (D.C.H.)", "Diploma"),
    ("M.S. (ORTHOPAEDICS)", "MS"),
    ("M.D. (Obst. and Gynae)/MS (Obstetrics and Gynaecology)", "MD/MS"),
    ("M.D. (GENERAL MEDICINE)", "MD"),
    ("Anaesthesiology", "MD"),
])
def test_degree_of(course, degree):
    assert degree_of(course) == degree
