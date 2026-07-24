"""Shared helpers to render OMR sheets as images for tests and calibration."""

from __future__ import annotations

import cv2
import numpy as np

from app.core.omr_layouts import DrawingElementType, get_layout_provider


def render_sheet_png(
    layout_version: str,
    student_code: str | None = None,
    answers: dict[str, str] | None = None,
    margin: int = 50,
) -> bytes:
    """
    Renders an OMR sheet PNG in the same coordinate space used by the OpenCV engine.

    This is the calibration source of truth for bubble positions (layout units),
    matching what teachers print conceptually via PDF (same layout provider).
    """
    answers = answers or {}
    page_w, page_h = 1000, 1414
    canvas_w = page_w + 2 * margin
    canvas_h = page_h + 2 * margin
    img = np.ones((canvas_h, canvas_w, 3), dtype=np.uint8) * 255

    provider = get_layout_provider(layout_version)
    elements = provider.render(student_code)

    for elem in elements:
        x = int(elem.coordinates[0] + margin)
        y = int(elem.coordinates[1] + margin)

        if elem.type == DrawingElementType.ANCHOR:
            cv2.circle(img, (x, y), 15, (0, 0, 0), -1)

        elif elem.type == DrawingElementType.BUBBLE:
            is_filled = bool(elem.is_filled)
            if elem.question_num is not None and elem.option_label is not None:
                q_num = str(elem.question_num)
                if q_num in answers and answers[q_num] == elem.option_label:
                    is_filled = True

            radius = int(elem.radius or 8)
            cv2.circle(img, (x, y), radius, (0, 0, 0), 1)
            if is_filled:
                cv2.circle(img, (x, y), radius, (0, 0, 0), -1)
            else:
                cv2.circle(img, (x, y), max(radius - 1, 1), (255, 255, 255), -1)

        elif elem.type == DrawingElementType.TEXT and elem.text:
            cv2.putText(
                img,
                elem.text,
                (x, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (0, 0, 0),
                1,
                cv2.LINE_AA,
            )

    success, buffer = cv2.imencode(".png", img)
    if not success:
        raise RuntimeError("Failed to encode OMR sheet PNG")
    return buffer.tobytes()
