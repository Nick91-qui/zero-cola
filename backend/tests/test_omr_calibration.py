from app.services.omr_engine import OMREngine
from app.services.omr_pdf import generate_omr_pdf
from app.services.omr_sheet_image import render_sheet_png


def test_pdf_generation_and_layout_detection_agree_on_student_code():
    """Calibration check: PDF uses same layout provider as detection raster."""
    student_code = "10234"
    answers = {"1": "A", "2": "B", "3": "C"}

    pdf_bytes = generate_omr_pdf("v1_std_20q", student_code=student_code)
    assert pdf_bytes.startswith(b"%PDF")

    sheet_png = render_sheet_png("v1_std_20q", student_code=student_code, answers=answers)
    detected = OMREngine.process_image(sheet_png, "v1_std_20q")

    assert detected["student_code"] == student_code
    assert detected["detected_answers"]["1"] == "A"
    assert detected["detected_answers"]["2"] == "B"
    assert detected["detected_answers"]["3"] == "C"
