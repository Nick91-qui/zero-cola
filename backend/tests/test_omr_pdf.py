from app.services.omr_pdf import generate_omr_pdf


def test_generate_omr_pdf_success():
    # Test for standard 20 question layout without student code
    pdf_bytes = generate_omr_pdf("v1_std_20q")
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    # A valid PDF file starts with %PDF
    assert pdf_bytes.startswith(b"%PDF")


def test_generate_omr_pdf_with_student_code():
    # Test with custom student code
    pdf_bytes = generate_omr_pdf("v1_std_20q", student_code="12345")
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")


def test_generate_omr_pdf_50q():
    # Test for standard 50 question layout
    pdf_bytes = generate_omr_pdf("v1_std_50q", student_code="09876")
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")
