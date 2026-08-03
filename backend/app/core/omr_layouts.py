from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from math import ceil
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


class DrawingElementType(str, Enum):
    ANCHOR = "anchor"
    BUBBLE = "bubble"
    TEXT = "text"
    LINE = "line"
    RECT = "rect"


@dataclass
class DrawingElement:
    type: DrawingElementType
    coordinates: Tuple[float, float]  # (x, y) relative to 1000x1414 space
    radius: Optional[float] = None
    text: Optional[str] = None
    font_size: float = 12.0
    width: Optional[float] = None
    height: Optional[float] = None
    is_filled: bool = False
    label: Optional[str] = None
    question_num: Optional[int] = None
    option_label: Optional[str] = None  # A, B, C, D, E
    digit_col: Optional[int] = None  # column index 0-4 for student_code
    digit_val: Optional[int] = None  # digit value 0-9


class OMRLayoutProvider(ABC):
    @abstractmethod
    def get_layout_version(self) -> str:
        pass

    @abstractmethod
    def get_total_questions(self) -> int:
        pass

    @abstractmethod
    def get_options_per_question(self) -> int:
        pass

    @abstractmethod
    def render(self, student_code: Optional[str] = None) -> List[DrawingElement]:
        """
        Generates layout elements to be drawn on the PDF canvas.
        Coordinates are relative to 1000x1414 space.
        """
        pass

    @abstractmethod
    def detect(self, aligned_image: np.ndarray) -> Dict[str, Any]:
        """
        Analyzes a warped 1000x1414 grayscale or binary image.
        Returns a dict with student_code, detected_answers, and confidence information.
        """
        pass

    @abstractmethod
    def validate(self, detected_data: Dict[str, Any]) -> bool:
        """
        Validates the structure of the detected data.
        """
        pass


def _get_bubble_fill(image: np.ndarray, x: float, y: float, r: float = 8.0) -> float:
    """
    Calculates the fill percentage of a bubble centered at (x, y) with radius r.
    Returns a value between 0.0 (completely empty/white) and 1.0 (completely filled/black).
    """
    h, w = image.shape[:2]
    x_min = max(0, int(x - r))
    x_max = min(w, int(x + r + 1))
    y_min = max(0, int(y - r))
    y_max = min(h, int(y + r + 1))

    roi = image[y_min:y_max, x_min:x_max]
    if roi.size == 0:
        return 0.0

    # Calculate average pixel intensity (assuming 0 is black, 255 is white)
    mean_val = np.mean(roi)
    return float(255.0 - mean_val) / 255.0


class BaseStandardLayout(OMRLayoutProvider):
    def __init__(self, layout_version: str, total_questions: int, options_per_question: int = 5):
        self.layout_version = layout_version
        self.total_questions = total_questions
        self.options_per_question = options_per_question

        # 4 Anchors
        self.anchors = [(50.0, 50.0), (950.0, 50.0), (50.0, 1364.0), (950.0, 1364.0)]

        # Student Code Grid Configuration
        self.student_code_origin = (650.0, 120.0)
        self.student_code_cols = 5
        self.student_code_rows = 10
        self.student_code_dx = 30.0
        self.student_code_dy = 22.0
        self.student_code_bubble_radius = 8.0

    def get_layout_version(self) -> str:
        return self.layout_version

    def get_total_questions(self) -> int:
        return self.total_questions

    def get_options_per_question(self) -> int:
        return self.options_per_question

    def _get_student_code_bubble_coords(self, col: int, val: int) -> Tuple[float, float]:
        x = self.student_code_origin[0] + col * self.student_code_dx
        y = self.student_code_origin[1] + val * self.student_code_dy
        return (x, y)

    def _get_question_bubble_coords(
        self, question_num: int, option_idx: int
    ) -> Tuple[float, float]:
        """Must be implemented by subclasses to define the question layout geometry."""
        raise NotImplementedError()

    def render(self, student_code: Optional[str] = None) -> List[DrawingElement]:
        elements: List[DrawingElement] = []

        # Add Anchors
        for coord in self.anchors:
            elements.append(
                DrawingElement(type=DrawingElementType.ANCHOR, coordinates=coord, radius=15.0)
            )

        # Add Title and Header
        elements.append(
            DrawingElement(
                type=DrawingElementType.TEXT,
                coordinates=(100.0, 100.0),
                text="COLA-ZERO ANSWER SHEET",
                font_size=20.0,
            )
        )
        elements.append(
            DrawingElement(
                type=DrawingElementType.TEXT,
                coordinates=(100.0, 140.0),
                text="EXAM: _________________________________________",
                font_size=12.0,
            )
        )
        elements.append(
            DrawingElement(
                type=DrawingElementType.TEXT,
                coordinates=(100.0, 170.0),
                text="STUDENT: ______________________________________",
                font_size=12.0,
            )
        )
        elements.append(
            DrawingElement(
                type=DrawingElementType.TEXT,
                coordinates=(100.0, 200.0),
                text=f"LAYOUT VERSION: {self.layout_version}",
                font_size=10.0,
            )
        )

        # Add Student Code Header
        elements.append(
            DrawingElement(
                type=DrawingElementType.TEXT,
                coordinates=(self.student_code_origin[0], self.student_code_origin[1] - 30.0),
                text="STUDENT CODE (OMR)",
                font_size=10.0,
            )
        )

        # Draw Student Code Column labels above grid
        for col in range(self.student_code_cols):
            x = self.student_code_origin[0] + col * self.student_code_dx
            elements.append(
                DrawingElement(
                    type=DrawingElementType.TEXT,
                    coordinates=(x - 4.0, self.student_code_origin[1] - 10.0),
                    text=str(col + 1),
                    font_size=8.0,
                )
            )

        prefilled_digits = [None] * self.student_code_cols
        if student_code and len(student_code) == self.student_code_cols:
            try:
                prefilled_digits = [int(char) for char in student_code]
            except ValueError:
                pass

        for col in range(self.student_code_cols):
            fill_digit = prefilled_digits[col]
            for val in range(self.student_code_rows):
                coords = self._get_student_code_bubble_coords(col, val)
                is_filled = fill_digit == val
                elements.append(
                    DrawingElement(
                        type=DrawingElementType.BUBBLE,
                        coordinates=coords,
                        radius=self.student_code_bubble_radius,
                        is_filled=is_filled,
                        label=str(val),
                        digit_col=col,
                        digit_val=val,
                    )
                )

        # Render Question Bubbles (defined by subclasses)
        options = ["A", "B", "C", "D", "E"][: self.options_per_question]
        for q_num in range(1, self.total_questions + 1):
            # Render question label
            label_coords = self._get_question_label_coords(q_num)
            elements.append(
                DrawingElement(
                    type=DrawingElementType.TEXT,
                    coordinates=label_coords,
                    text=f"{q_num:02d}:",
                    font_size=10.0,
                )
            )

            # Render option bubbles
            for o_idx, o_lbl in enumerate(options):
                coords = self._get_question_bubble_coords(q_num, o_idx)
                elements.append(
                    DrawingElement(
                        type=DrawingElementType.BUBBLE,
                        coordinates=coords,
                        radius=8.0,
                        label=o_lbl,
                        question_num=q_num,
                        option_label=o_lbl,
                    )
                )

        return elements

    def _get_question_label_coords(self, question_num: int) -> Tuple[float, float]:
        raise NotImplementedError()

    def detect(self, aligned_image: np.ndarray) -> Dict[str, Any]:
        """
        Processes aligned_image to detect OMR bubbles.
        """
        # Ensure image is grayscale
        if len(aligned_image.shape) == 3:
            aligned_image = np.mean(aligned_image, axis=2).astype(np.uint8)

        # 1. Detect Student Code
        detected_digits = []
        raw_confidence_student_code = []

        for col in range(self.student_code_cols):
            fill_levels = []
            for val in range(self.student_code_rows):
                x, y = self._get_student_code_bubble_coords(col, val)
                fill_val = _get_bubble_fill(aligned_image, x, y, self.student_code_bubble_radius)
                fill_levels.append(fill_val)

            # Choose digit with highest fill
            best_val = int(np.argmax(fill_levels))
            detected_digits.append(str(best_val))
            raw_confidence_student_code.append(fill_levels)

        student_code = "".join(detected_digits)

        # 2. Detect Question Answers
        detected_answers = {}
        raw_confidence_answers = {}
        options = ["A", "B", "C", "D", "E"][: self.options_per_question]

        for q_num in range(1, self.total_questions + 1):
            fill_levels = []
            for o_idx in range(self.options_per_question):
                x, y = self._get_question_bubble_coords(q_num, o_idx)
                fill_val = _get_bubble_fill(aligned_image, x, y, 8.0)
                fill_levels.append(fill_val)

            raw_confidence_answers[str(q_num)] = fill_levels

            # Threshold to consider a bubble filled
            filled_options = [i for i, fill in enumerate(fill_levels) if fill >= 0.25]

            if len(filled_options) == 1:
                # Exactly one filled option
                detected_answers[str(q_num)] = options[filled_options[0]]
            elif len(filled_options) > 1:
                # Multiple filled options - mark as ambiguous
                detected_answers[str(q_num)] = "MULTIPLE"
            else:
                # No filled options - blank
                detected_answers[str(q_num)] = None

        return {
            "student_code": student_code,
            "detected_answers": detected_answers,
            "raw_confidence": {
                "student_code": raw_confidence_student_code,
                "answers": raw_confidence_answers,
            },
        }

    def validate(self, detected_data: Dict[str, Any]) -> bool:
        if "student_code" not in detected_data or "detected_answers" not in detected_data:
            return False

        student_code = detected_data["student_code"]
        if (
            not isinstance(student_code, str)
            or len(student_code) != self.student_code_cols
            or not student_code.isdigit()
        ):
            return False

        detected_answers = detected_data["detected_answers"]
        if not isinstance(detected_answers, dict) or len(detected_answers) != self.total_questions:
            return False

        return True


class ColumnedStandardLayout(BaseStandardLayout):
    def __init__(
        self,
        layout_version: str,
        total_questions: int,
        question_column_origins: List[Tuple[float, float]],
        options_per_question: int = 5,
        question_dx: float = 35.0,
        question_dy: float = 32.0,
    ):
        super().__init__(
            layout_version=layout_version,
            total_questions=total_questions,
            options_per_question=options_per_question,
        )
        self.question_column_origins = question_column_origins
        self.question_dx = question_dx
        self.question_dy = question_dy
        self.questions_per_column = ceil(total_questions / len(question_column_origins))

    def _get_question_column_and_relative_idx(self, question_num: int) -> Tuple[int, int]:
        if question_num < 1 or question_num > self.total_questions:
            raise ValueError(f"Question number {question_num} is out of range for this layout.")

        q_index = question_num - 1
        col_idx = min(q_index // self.questions_per_column, len(self.question_column_origins) - 1)
        rel_idx = q_index - (col_idx * self.questions_per_column)
        return col_idx, rel_idx

    def _get_question_bubble_coords(
        self, question_num: int, option_idx: int
    ) -> Tuple[float, float]:
        col_idx, rel_idx = self._get_question_column_and_relative_idx(question_num)
        origin = self.question_column_origins[col_idx]
        x = origin[0] + option_idx * self.question_dx
        y = origin[1] + rel_idx * self.question_dy
        return (x, y)

    def _get_question_label_coords(self, question_num: int) -> Tuple[float, float]:
        col_idx, rel_idx = self._get_question_column_and_relative_idx(question_num)
        origin = self.question_column_origins[col_idx]
        x = origin[0] - 50.0
        y = origin[1] + rel_idx * self.question_dy + 3.0
        return (x, y)

    def render(self, student_code: Optional[str] = None) -> List[DrawingElement]:
        elements = super().render(student_code)

        # Add question option header letters at the top of each question column.
        options = ["A", "B", "C", "D", "E"]
        for origin in self.question_column_origins:
            header_y = origin[1] - 25.0
            for idx, opt in enumerate(options):
                x = origin[0] + idx * self.question_dx
                elements.append(
                    DrawingElement(
                        type=DrawingElementType.TEXT,
                        coordinates=(x - 4.0, header_y),
                        text=opt,
                        font_size=10.0,
                    )
                )

        return elements


class Standard10QuestionLayout(ColumnedStandardLayout):
    def __init__(self):
        super().__init__(
            layout_version="v1_std_10q",
            total_questions=10,
            question_column_origins=[(250.0, 420.0)],
            question_dx=45.0,
            question_dy=40.0,
        )


class Standard20QuestionLayout(ColumnedStandardLayout):
    def __init__(self):
        super().__init__(
            layout_version="v1_std_20q",
            total_questions=20,
            question_column_origins=[(250.0, 420.0)],
            question_dx=45.0,
            question_dy=40.0,
        )


class Standard30QuestionLayout(ColumnedStandardLayout):
    def __init__(self):
        super().__init__(
            layout_version="v1_std_30q",
            total_questions=30,
            question_column_origins=[(180.0, 420.0), (580.0, 420.0)],
        )


class Standard40QuestionLayout(ColumnedStandardLayout):
    def __init__(self):
        super().__init__(
            layout_version="v1_std_40q",
            total_questions=40,
            question_column_origins=[(180.0, 420.0), (580.0, 420.0)],
        )


class Standard50QuestionLayout(ColumnedStandardLayout):
    def __init__(self):
        super().__init__(
            layout_version="v1_std_50q",
            total_questions=50,
            question_column_origins=[(180.0, 420.0), (580.0, 420.0)],
        )


class Standard60QuestionLayout(ColumnedStandardLayout):
    def __init__(self):
        super().__init__(
            layout_version="v1_std_60q",
            total_questions=60,
            question_column_origins=[(140.0, 420.0), (420.0, 420.0), (700.0, 420.0)],
        )


class Standard70QuestionLayout(ColumnedStandardLayout):
    def __init__(self):
        super().__init__(
            layout_version="v1_std_70q",
            total_questions=70,
            question_column_origins=[(140.0, 420.0), (420.0, 420.0), (700.0, 420.0)],
        )


class Standard80QuestionLayout(ColumnedStandardLayout):
    def __init__(self):
        super().__init__(
            layout_version="v1_std_80q",
            total_questions=80,
            question_column_origins=[
                (120.0, 420.0),
                (360.0, 420.0),
                (600.0, 420.0),
                (840.0, 420.0),
            ],
        )


class Standard90QuestionLayout(ColumnedStandardLayout):
    def __init__(self):
        super().__init__(
            layout_version="v1_std_90q",
            total_questions=90,
            question_column_origins=[
                (120.0, 420.0),
                (360.0, 420.0),
                (600.0, 420.0),
                (840.0, 420.0),
            ],
        )


class Standard100QuestionLayout(ColumnedStandardLayout):
    def __init__(self):
        super().__init__(
            layout_version="v1_std_100q",
            total_questions=100,
            question_column_origins=[
                (120.0, 420.0),
                (360.0, 420.0),
                (600.0, 420.0),
                (840.0, 420.0),
            ],
        )


# Registry
LAYOUT_REGISTRY: Dict[str, type[OMRLayoutProvider]] = {
    "v1_std_10q": Standard10QuestionLayout,
    "v1_std_20q": Standard20QuestionLayout,
    "v1_std_30q": Standard30QuestionLayout,
    "v1_std_40q": Standard40QuestionLayout,
    "v1_std_50q": Standard50QuestionLayout,
    "v1_std_60q": Standard60QuestionLayout,
    "v1_std_70q": Standard70QuestionLayout,
    "v1_std_80q": Standard80QuestionLayout,
    "v1_std_90q": Standard90QuestionLayout,
    "v1_std_100q": Standard100QuestionLayout,
}


def resolve_layout_version(total_questions: int) -> str:
    if total_questions < 1:
        raise ValueError("An OMR layout requires at least one question.")

    layout_questions = ceil(total_questions / 10) * 10
    if layout_questions > 100:
        raise ValueError(
            "No OMR layout version is available for "
            f"{total_questions} questions. Supported layouts are 10 through 100 questions."
        )

    return f"v1_std_{layout_questions}q"


def get_layout_provider(layout_version: str) -> OMRLayoutProvider:
    if layout_version not in LAYOUT_REGISTRY:
        raise ValueError(f"Unknown OMR layout version: {layout_version}")
    return LAYOUT_REGISTRY[layout_version]()
