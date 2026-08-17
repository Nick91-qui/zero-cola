import json
from collections.abc import Mapping
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session, selectinload

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
            .options(selectinload(AnswerKeyItem.skills))
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
        if is_published:
            answer_key.published_at = datetime.now(timezone.utc)
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

        self._validate_exam_questions(exam_questions)

        answer_key = AnswerKey(exam_id=exam_id, is_published=is_published)
        if is_published:
            answer_key.published_at = datetime.now(timezone.utc)
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

    def publish_for_exam(self, exam_id: UUID) -> AnswerKey:
        answer_key = self.get_by_exam_id(exam_id)
        if answer_key is None:
            answer_key = self.create_from_exam_questions(exam_id, is_published=False)

        return self.publish_answer_key(answer_key.id)

    def publish_answer_key(self, answer_key_id: UUID) -> AnswerKey:
        answer_key = (
            self.db.query(AnswerKey).filter(AnswerKey.id == answer_key_id).first()
        )
        if answer_key is None:
            raise ValueError(f"AnswerKey {answer_key_id} not found.")

        if not answer_key.items:
            raise ValueError(f"AnswerKey {answer_key.id} has no AnswerKeyItems.")

        if not answer_key.is_published:
            answer_key.is_published = True
            answer_key.published_at = datetime.now(timezone.utc)
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

    def _validate_exam_questions(self, exam_questions: list[ExamQuestion]) -> None:
        seen_orders: set[int] = set()
        expected_order = 1
        for exam_question in exam_questions:
            if exam_question.display_order < 1:
                raise ValueError("ExamQuestion.display_order must be positive.")
            if exam_question.display_order in seen_orders:
                raise ValueError("ExamQuestion.display_order must be unique per exam.")
            if exam_question.display_order != expected_order:
                raise ValueError(
                    "ExamQuestion.display_order must be contiguous starting at 1."
                )
            question = exam_question.question
            if question is None:
                raise ValueError(
                    f"ExamQuestion {exam_question.id} is missing its Question reference."
                )
            if not question.is_active:
                raise ValueError(
                    f"Question {question.id} is inactive and cannot be published."
                )
            seen_orders.add(exam_question.display_order)
            expected_order += 1


@event.listens_for(Session, "before_flush")
def _guard_published_answer_keys(session, flush_context, instances) -> None:
    publishing_answer_keys: set[UUID] = set()

    for obj in session.new:
        if isinstance(obj, AnswerKey) and obj.id is not None:
            publishing_answer_keys.add(obj.id)

    for obj in session.dirty:
        if isinstance(obj, AnswerKey):
            state = inspect(obj)
            if _is_publish_transition(state):
                publishing_answer_keys.add(obj.id)

    for obj in list(session.new) + list(session.dirty) + list(session.deleted):
        if isinstance(obj, AnswerKey):
            _guard_answer_key_mutation(session, obj)
        elif isinstance(obj, AnswerKeyItem):
            _guard_answer_key_item_mutation(session, obj, publishing_answer_keys)


def _guard_answer_key_mutation(session: Session, answer_key: AnswerKey) -> None:
    state = inspect(answer_key)
    if answer_key in session.new:
        return

    if _was_published(state) and not _is_publish_transition(state):
        if session.is_modified(answer_key, include_collections=True):
            raise ValueError("Published AnswerKey records are immutable.")


def _guard_answer_key_item_mutation(
    session: Session,
    item: AnswerKeyItem,
    publishing_answer_keys: set[UUID],
) -> None:
    answer_key = item.answer_key
    if answer_key is None and item.answer_key_id is not None:
        answer_key = session.get(AnswerKey, item.answer_key_id)

    if answer_key is None:
        return

    if answer_key in session.new:
        return

    if answer_key.id in publishing_answer_keys:
        return

    if answer_key.is_published:
        raise ValueError("Published AnswerKeyItem records are immutable.")


def _is_publish_transition(state) -> bool:
    is_published_history = state.attrs.is_published.history
    published_at_history = state.attrs.published_at.history
    return (
        is_published_history.has_changes()
        and bool(is_published_history.added)
        and is_published_history.added[-1] is True
        and published_at_history.has_changes()
    )


def _was_published(state) -> bool:
    is_published_history = state.attrs.is_published.history
    published_at_history = state.attrs.published_at.history
    if is_published_history.has_changes():
        return bool(is_published_history.deleted and is_published_history.deleted[-1] is True)
    if published_at_history.has_changes():
        return bool(
            published_at_history.deleted and published_at_history.deleted[-1] is not None
        )
    return bool(state.object.is_published and state.object.published_at is not None)
