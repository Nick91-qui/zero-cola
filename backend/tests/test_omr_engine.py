import cv2
import numpy as np
import pytest

from app.core.omr_layouts import DrawingElementType, get_layout_provider
from app.services.omr_engine import OMREngine, OMREngineError
from app.services.omr_sheet_image import render_sheet_png


def test_omr_engine_synthetic_processing():
    # 1. Create a synthetic A4 white page (1000x1414 space)
    # We will simulate a slightly larger size and then crop/transform it to verify alignment
    page_w, page_h = 1000, 1414
    margin = 50
    # Create canvas with a border to simulate a scan
    canvas_w = page_w + 2 * margin
    canvas_h = page_h + 2 * margin
    img = np.ones((canvas_h, canvas_w, 3), dtype=np.uint8) * 255

    # 2. Get layout provider
    provider = get_layout_provider("v1_std_20q")

    # We will fill student_code = "90123" and questions: Q1=A, Q2=B, Q3=C, Q4=D, Q5=E
    student_code = "90123"
    elements = provider.render(student_code)

    # Draw elements onto canvas, shifting coordinates by `margin`
    for elem in elements:
        x = int(elem.coordinates[0] + margin)
        y = int(elem.coordinates[1] + margin)

        if elem.type == DrawingElementType.ANCHOR:
            cv2.circle(img, (x, y), 15, (0, 0, 0), -1)

        elif elem.type == DrawingElementType.BUBBLE:
            is_filled = elem.is_filled
            if elem.question_num is not None:
                q_num = elem.question_num
                opt_lbl = elem.option_label
                if q_num == 1 and opt_lbl == "A":
                    is_filled = True
                elif q_num == 2 and opt_lbl == "B":
                    is_filled = True
                elif q_num == 3 and opt_lbl == "C":
                    is_filled = True
                elif q_num == 4 and opt_lbl == "D":
                    is_filled = True
                elif q_num == 5 and opt_lbl == "E":
                    is_filled = True

            # Draw outer bubble
            cv2.circle(img, (x, y), 8, (0, 0, 0), 1)
            if is_filled:
                cv2.circle(img, (x, y), 8, (0, 0, 0), -1)
            else:
                # White fill
                cv2.circle(img, (x, y), 7, (255, 255, 255), -1)

    # 3. Simulate minor skew/rotation
    # Rotate by 1.5 degrees around the center
    center = (canvas_w // 2, canvas_h // 2)
    rot_mat = cv2.getRotationMatrix2D(center, 1.5, 1.0)
    rotated = cv2.warpAffine(img, rot_mat, (canvas_w, canvas_h), borderValue=(255, 255, 255))

    # Encode to PNG bytes
    success, buffer = cv2.imencode(".png", rotated)
    assert success is True
    image_bytes = buffer.tobytes()

    # 4. Process using OMREngine
    result = OMREngine.process_image(image_bytes, "v1_std_20q")

    # 5. Assertions
    assert result["student_code"] == student_code
    assert result["detected_answers"]["1"] == "A"
    assert result["detected_answers"]["2"] == "B"
    assert result["detected_answers"]["3"] == "C"
    assert result["detected_answers"]["4"] == "D"
    assert result["detected_answers"]["5"] == "E"

    # Remaining questions should be None
    for q in range(6, 21):
        assert result["detected_answers"][str(q)] is None


def test_omr_engine_invalid_image():
    with pytest.raises(OMREngineError):
        OMREngine.process_image(b"invalid_image_bytes_here", "v1_std_20q")


def test_omr_engine_missing_anchors():
    # Create white canvas with no anchors
    img = np.ones((600, 400, 3), dtype=np.uint8) * 255
    success, buffer = cv2.imencode(".png", img)
    assert success is True

    with pytest.raises(OMREngineError) as exc_info:
        OMREngine.process_image(buffer.tobytes(), "v1_std_20q")

    assert "Could not detect all 4 anchor marks" in str(exc_info.value)


def test_omr_engine_synthetic_processing_100q():
    sheet_png = render_sheet_png(
        "v1_std_100q",
        student_code="54321",
        answers={"1": "A", "26": "B", "51": "C", "76": "D"},
    )

    result = OMREngine.process_image(sheet_png, "v1_std_100q")

    assert result["student_code"] == "54321"
    assert result["detected_answers"]["1"] == "A"
    assert result["detected_answers"]["26"] == "B"
    assert result["detected_answers"]["51"] == "C"
    assert result["detected_answers"]["76"] == "D"
    for q in (2, 27, 52, 77):
        assert result["detected_answers"][str(q)] is None
