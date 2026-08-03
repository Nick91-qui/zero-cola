import numpy as np
import pytest

from app.core.omr_layouts import (
    DrawingElementType,
    get_layout_provider,
    resolve_layout_version,
)


def test_get_layout_provider_success():
    provider_20 = get_layout_provider("v1_std_20q")
    assert provider_20.get_layout_version() == "v1_std_20q"
    assert provider_20.get_total_questions() == 20
    assert provider_20.get_options_per_question() == 5

    provider_50 = get_layout_provider("v1_std_50q")
    assert provider_50.get_layout_version() == "v1_std_50q"
    assert provider_50.get_total_questions() == 50

    provider_100 = get_layout_provider("v1_std_100q")
    assert provider_100.get_layout_version() == "v1_std_100q"
    assert provider_100.get_total_questions() == 100


def test_get_layout_provider_not_found():
    with pytest.raises(ValueError):
        get_layout_provider("non_existent")


@pytest.mark.parametrize(
    ("total_questions", "expected_layout"),
    [
        (75, "v1_std_100q"),
        (80, "v1_std_100q"),
        (100, "v1_std_100q"),
    ],
)
def test_resolve_layout_version_uses_100q_layout_for_large_exams(
    total_questions: int,
    expected_layout: str,
):
    assert resolve_layout_version(total_questions) == expected_layout


def test_render_elements():
    provider = get_layout_provider("v1_std_20q")
    elements = provider.render(student_code="12345")

    # Verify we have anchors, titles, student code bubbles, and question bubbles
    assert len(elements) > 0

    anchors = [e for e in elements if e.type == DrawingElementType.ANCHOR]
    assert len(anchors) == 4

    # student code bubbles: 5 columns * 10 rows = 50 bubbles
    # questions bubbles: 20 questions * 5 options = 100 bubbles
    # Total bubbles = 150
    bubbles = [e for e in elements if e.type == DrawingElementType.BUBBLE]
    assert len(bubbles) == 150

    # Ensure one bubble is prefilled for student_code "12345" in each col
    filled_bubbles = [e for e in bubbles if e.is_filled and e.digit_col is not None]
    assert len(filled_bubbles) == 5
    assert [fb.digit_val for fb in filled_bubbles] == [1, 2, 3, 4, 5]


def test_detect_mock_image():
    provider = get_layout_provider("v1_std_20q")

    # Create a white image of 1414 x 1000 pixels (grayscale, 255 represents white)
    img = np.ones((1414, 1000), dtype=np.uint8) * 255

    # "Draw" a prefilled student code: "10234"
    # Column 0: 1, Column 1: 0, Column 2: 2, Column 3: 3, Column 4: 4
    code_digits = [1, 0, 2, 3, 4]
    for col, digit in enumerate(code_digits):
        x, y = provider._get_student_code_bubble_coords(col, digit)
        # Draw a black filled region (0 represents black)
        img[int(y - 5) : int(y + 6), int(x - 5) : int(x + 6)] = 0

    # "Draw" some correct answers: Q1=A (idx 0), Q2=C (idx 2)
    # Q1 coords
    x1, y1 = provider._get_question_bubble_coords(1, 0)
    img[int(y1 - 5) : int(y1 + 6), int(x1 - 5) : int(x1 + 6)] = 0

    # Q2 coords
    x2, y2 = provider._get_question_bubble_coords(2, 2)
    img[int(y2 - 5) : int(y2 + 6), int(x2 - 5) : int(x2 + 6)] = 0

    res = provider.detect(img)

    assert res["student_code"] == "10234"
    assert res["detected_answers"]["1"] == "A"
    assert res["detected_answers"]["2"] == "C"
    # The remaining questions should be empty/None
    for q in range(3, 21):
        assert res["detected_answers"][str(q)] is None

    assert provider.validate(res) is True


def test_render_elements_100q():
    provider = get_layout_provider("v1_std_100q")
    elements = provider.render(student_code="98765")

    anchors = [e for e in elements if e.type == DrawingElementType.ANCHOR]
    assert len(anchors) == 4

    bubbles = [e for e in elements if e.type == DrawingElementType.BUBBLE]
    assert len(bubbles) == 550

    filled_bubbles = [e for e in bubbles if e.is_filled and e.digit_col is not None]
    assert len(filled_bubbles) == 5
    assert [fb.digit_val for fb in filled_bubbles] == [9, 8, 7, 6, 5]
