import json
from collections.abc import Mapping
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.answer_key import AnswerKey, AnswerKeyItem
from app.models.exam_question import ExamQuestion


class AnswerKeyService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_exam_id(self, exam_id: UUID) -> AnswerKey | None:
        return self.db.query(AnswerKey).filter(AnswerKey.exam_id == exam_id).first()

    def require_for_exam(self, exam_id: UUID) -> AnswerKey:
        answer_key = self.get_by_exam_id(exam_id)
        if not answer_key:
            raise ValueError(f"Exam {exam_id} has no AnswerKey.")
        return answer_key

    def get_items_for_exam(self, exam_id: UUID) -> list[AnswerKeyItem]:
        answer_key = self.require_for_exam(exam_id)
        items = (
            self.db.query(AnswerKeyItem)
            .filter(AnswerKeyItem.answer_key_id == answer_key.id)
            .order_by(AnswerKeyItem.item_number.asc())
            .all()
        )
        if not items:
            raise ValueError(f"AnswerKey {answer_key.id} has no AnswerKeyItems.")
        return items

    def get_item_map_for_exam(self, exam_id: UUID) -> dict[int, AnswerKeyItem]:
        return {item.item_number: item for item in self.get_items_for_exam(exam_id)}

    def create_from_mapping(
        self,
        exam_id: UUID,
        correct_answers: Mapping[str, str],
        *,
        is_published: bool = False,
    ) -> AnswerKey:
        existing = self.get_by_exam_id(exam_id)
        if existing:
            return existing

        answer_key = AnswerKey(exam_id=exam_id, is_published=is_published)
        self.db.add(answer_key)
        self.db.flush()

        for key, value in correct_answers.items():
            if value is None:
                continue

            try:
                item_number = int(str(key).replace("q", "").replace("Q", ""))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid answer key item number: {key!r}") from exc

            self.db.add(
                AnswerKeyItem(
                    answer_key_id=answer_key.id,
                    item_number=item_number,
                    correct_answer=str(value),
                    weight=Decimal("1.00"),
                    statement=None,
                    question_id=None,
                )
            )

        self.db.commit()
        self.db.refresh(answer_key)
        return answer_key

    def create_from_exam_questions(
        self,
        exam_id: UUID,
        *,
        is_published: bool = False,
    ) -> AnswerKey:
        existing = self.get_by_exam_id(exam_id)
        if existing:
            return existing

        exam_questions = (
            self.db.query(ExamQuestion)
            .filter(ExamQuestion.exam_id == exam_id)
            .order_by(ExamQuestion.display_order.asc())
            .all()
        )
        if not exam_questions:
            raise ValueError(f"Exam {exam_id} has no exam_questions.")

        answer_key = AnswerKey(exam_id=exam_id, is_published=is_published)
        self.db.add(answer_key)
        self.db.flush()

        for exam_question in exam_questions:
            question = exam_question.question
            item = AnswerKeyItem(
                answer_key_id=answer_key.id,
                item_number=exam_question.display_order,
                correct_answer=self._normalize_correct_answer(question.correct_answer),
                weight=exam_question.weight,
                statement=question.statement,
                question_id=question.id,
            )
            self.db.add(item)
            self.db.flush()
            item.skills.extend(question.skills)

        self.db.commit()
        self.db.refresh(answer_key)
        return answer_key

    def _normalize_correct_answer(self, value) -> str:
        if isinstance(value, dict):
            for key in ("key", "answer", "value"):
                if key in value and value[key] is not None:
                    return str(value[key])
            return json.dumps(value, sort_keys=True)
        return str(value)
