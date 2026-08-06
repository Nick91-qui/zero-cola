import io
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.core.omr_layouts import DrawingElementType, get_layout_provider


def generate_omr_pdf(
    layout_version: str,
    student_code: Optional[str] = None,
    *,
    exam_title: Optional[str] = None,
    student_name: Optional[str] = None,
) -> bytes:
    """
    Generates a PDF bytes representation of the OMR answer sheet
    using ReportLab. Scales coordinates from the layout's 1000x1414 space
    to standard A4 page size (595.27 x 841.89 points).
    """
    provider = get_layout_provider(layout_version)
    elements = provider.render(
        student_code,
        exam_title=exam_title,
        student_name=student_name,
    )

    a4_width, a4_height = A4  # 595.27, 841.89

    # Scale helper functions
    def scale_x(x: float) -> float:
        return (x / 1000.0) * a4_width

    def scale_y(y: float) -> float:
        # Invert Y coordinate because ReportLab's origin is bottom-left
        return a4_height - (y / 1414.0) * a4_height

    def scale_size(size: float) -> float:
        return (size / 1000.0) * a4_width

    # Generate PDF in memory
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(f"OMR Answer Sheet - {layout_version}")

    for elem in elements:
        pdf_x = scale_x(elem.coordinates[0])
        pdf_y = scale_y(elem.coordinates[1])

        if elem.type == DrawingElementType.ANCHOR:
            pdf_r = scale_size(elem.radius or 15.0)
            # Draw a thick outer ring and solid center for robustness in OpenCV detection
            pdf.setFillColorRGB(0.0, 0.0, 0.0)
            pdf.setStrokeColorRGB(0.0, 0.0, 0.0)
            # Solid black filled circle
            pdf.circle(pdf_x, pdf_y, pdf_r, stroke=1, fill=1)

        elif elem.type == DrawingElementType.BUBBLE:
            pdf_r = scale_size(elem.radius or 8.0)
            pdf.setStrokeColorRGB(0.0, 0.0, 0.0)
            pdf.setLineWidth(1)

            if elem.is_filled:
                pdf.setFillColorRGB(0.0, 0.0, 0.0)
                pdf.circle(pdf_x, pdf_y, pdf_r, stroke=1, fill=1)

                # Draw white label inside filled black bubble
                if elem.label:
                    pdf.setFont("Helvetica-Bold", pdf_r * 1.1)
                    pdf.setFillColorRGB(1.0, 1.0, 1.0)
                    # Vertical offset for centering text inside the circle
                    pdf.drawCentredString(pdf_x, pdf_y - (pdf_r * 0.35), elem.label)
            else:
                pdf.setFillColorRGB(1.0, 1.0, 1.0)
                pdf.circle(pdf_x, pdf_y, pdf_r, stroke=1, fill=1)

                # Draw black label inside empty bubble
                if elem.label:
                    pdf.setFont("Helvetica", pdf_r * 1.1)
                    pdf.setFillColorRGB(0.0, 0.0, 0.0)
                    pdf.drawCentredString(pdf_x, pdf_y - (pdf_r * 0.35), elem.label)

        elif elem.type == DrawingElementType.TEXT:
            font_size = scale_size(elem.font_size * 2.0)  # Make font sizes look readable
            pdf.setFont("Helvetica-Bold" if elem.font_size >= 14.0 else "Helvetica", font_size)
            pdf.setFillColorRGB(0.0, 0.0, 0.0)
            pdf.drawString(pdf_x, pdf_y, elem.text or "")

        elif elem.type == DrawingElementType.LINE:
            # Not used in current layouts, but good for completeness
            if elem.width and elem.height:
                pdf.setStrokeColorRGB(0.0, 0.0, 0.0)
                pdf.setLineWidth(1)
                pdf.line(pdf_x, pdf_y, scale_x(elem.width), scale_y(elem.height))

        elif elem.type == DrawingElementType.RECT:
            if elem.width and elem.height:
                pdf.setStrokeColorRGB(0.0, 0.0, 0.0)
                pdf.setLineWidth(1)
                pdf.setFillColorRGB(1.0, 1.0, 1.0)
                w = scale_size(elem.width)
                h = scale_size(elem.height)
                pdf.rect(pdf_x, pdf_y - h, w, h, stroke=1, fill=1)

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return buffer.getvalue()
