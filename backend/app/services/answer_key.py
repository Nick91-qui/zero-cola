from collections.abc import Mapping
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.answer_key import AnswerKey, AnswerKeyItem


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
