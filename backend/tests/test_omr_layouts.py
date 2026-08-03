import numpy as np
import pytest

from app.core.omr_layouts import (
    DrawingElementType,
    get_layout_provider,
    resolve_layout_version,
)


def test_get_layout_provider_success():
    provider_10 = get_layout_provider("v1_std_10q")
    assert provider_10.get_layout_version() == "v1_std_10q"
    assert provider_10.get_total_questions() == 10
    assert provider_10.get_options_per_question() == 5

    provider_20 = get_layout_provider("v1_std_20q")
    assert provider_20.get_layout_version() == "v1_std_20q"
    assert provider_20.get_total_questions() == 20
    assert provider_20.get_options_per_question() == 5

    provider_30 = get_layout_provider("v1_std_30q")
    assert provider_30.get_layout_version() == "v1_std_30q"
    assert provider_30.get_total_questions() == 30

    provider_40 = get_layout_provider("v1_std_40q")
    assert provider_40.get_layout_version() == "v1_std_40q"
    assert provider_40.get_total_questions() == 40

    provider_50 = get_layout_provider("v1_std_50q")
    assert provider_50.get_layout_version() == "v1_std_50q"
    assert provider_50.get_total_questions() == 50

    provider_60 = get_layout_provider("v1_std_60q")
    assert provider_60.get_layout_version() == "v1_std_60q"
    assert provider_60.get_total_questions() == 60

    provider_70 = get_layout_provider("v1_std_70q")
    assert provider_70.get_layout_version() == "v1_std_70q"
    assert provider_70.get_total_questions() == 70

    provider_80 = get_layout_provider("v1_std_80q")
    assert provider_80.get_layout_version() == "v1_std_80q"
    assert provider_80.get_total_questions() == 80

    provider_90 = get_layout_provider("v1_std_90q")
    assert provider_90.get_layout_version() == "v1_std_90q"
    assert provider_90.get_total_questions() == 90

    provider_100 = get_layout_provider("v1_std_100q")
    assert provider_100.get_layout_version() == "v1_std_100q"
    assert provider_100.get_total_questions() == 100


def test_get_layout_provider_not_found():
    with pytest.raises(ValueError):
        get_layout_provider("non_existent")


@pytest.mark.parametrize(
    ("total_questions", "expected_layout"),
    [
        (1, "v1_std_10q"),
        (9, "v1_std_10q"),
        (10, "v1_std_10q"),
        (11, "v1_std_20q"),
        (20, "v1_std_20q"),
        (21, "v1_std_30q"),
        (30, "v1_std_30q"),
        (31, "v1_std_40q"),
        (32, "v1_std_40q"),
        (40, "v1_std_40q"),
        (41, "v1_std_50q"),
        (50, "v1_std_50q"),
        (51, "v1_std_60q"),
        (60, "v1_std_60q"),
        (61, "v1_std_70q"),
        (70, "v1_std_70q"),
        (71, "v1_std_80q"),
        (75, "v1_std_80q"),
        (80, "v1_std_80q"),
        (81, "v1_std_90q"),
        (90, "v1_std_90q"),
        (91, "v1_std_100q"),
        (99, "v1_std_100q"),
        (100, "v1_std_100q"),
    ],
)
def test_resolve_layout_version_rounds_up_to_the_next_ten(
    total_questions: int,
    expected_layout: str,
):
    assert resolve_layout_version(total_questions) == expected_layout


@pytest.mark.parametrize(
    "layout_version",
    [
        "v1_std_10q",
        "v1_std_20q",
        "v1_std_30q",
        "v1_std_40q",
        "v1_std_50q",
        "v1_std_60q",
        "v1_std_70q",
        "v1_std_80q",
        "v1_std_90q",
        "v1_std_100q",
    ],
)
def test_render_elements_for_all_supported_layout_versions(layout_version: str):
    provider = get_layout_provider(layout_version)
    elements = provider.render(student_code="12345")

    anchors = [e for e in elements if e.type == DrawingElementType.ANCHOR]
    assert len(anchors) == 4

    bubbles = [e for e in elements if e.type == DrawingElementType.BUBBLE]
    assert len(bubbles) == 50 + (provider.get_total_questions() * 5)

    filled_bubbles = [e for e in bubbles if e.is_filled and e.digit_col is not None]
    assert len(filled_bubbles) == 5
    assert [fb.digit_val for fb in filled_bubbles] == [1, 2, 3, 4, 5]


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
