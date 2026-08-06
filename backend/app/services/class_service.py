from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.class_ import Class, ClassStudent, TeacherClass
from app.models.enums import UserRole
from app.models.user import User
from app.services.audit_log import AuditLogService


class ClassService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_log_service = AuditLogService(db)

    @staticmethod
    def _default_academic_period() -> str:
        return str(datetime.now(timezone.utc).year)

    @staticmethod
    def _require_admin(current_user: User) -> None:
        if current_user.role != UserRole.ADMIN:
            raise ValueError("Only admins can manage classes and memberships.")

    def _teacher_link(self, *, class_id: UUID, teacher_id: UUID) -> TeacherClass | None:
        return (
            self.db.query(TeacherClass)
            .filter(
                TeacherClass.class_id == class_id,
                TeacherClass.teacher_id == teacher_id,
                TeacherClass.is_active.is_(True),
            )
            .first()
        )

    def _require_class(
        self,
        class_id: UUID,
        current_user: User,
        *,
        include_inactive: bool = True,
    ) -> Class:
        query = self.db.query(Class).filter(Class.id == class_id)
        if not include_inactive:
            query = query.filter(Class.is_active.is_(True))
        class_obj = query.first()
        if class_obj is None:
            raise ValueError(f"Class {class_id} not found.")
        if current_user.role == UserRole.ADMIN:
            return class_obj
        if current_user.role != UserRole.TEACHER:
            raise ValueError(f"Class {class_id} not found.")
        if self._teacher_link(class_id=class_id, teacher_id=current_user.id) is None:
            raise ValueError(f"Class {class_id} not found.")
        return class_obj

    def create_class(
        self,
        *,
        current_user: User,
        name: str,
        description: str | None = None,
        academic_period: str | None = None,
        teacher_id: UUID | None = None,
    ) -> Class:
        self._require_admin(current_user)
        if teacher_id is None:
            raise ValueError("teacher_id is required for admin class creation.")

        teacher = self.db.query(User).filter(User.id == teacher_id).first()
        if (
            teacher is None
            or teacher.role != UserRole.TEACHER
            or not teacher.is_active
            or teacher.anonymized_at is not None
        ):
            raise ValueError(f"Teacher {teacher_id} not found.")

        class_obj = Class(
            teacher_id=teacher_id,
            name=name,
            academic_period=academic_period or self._default_academic_period(),
            description=description,
            is_active=True,
        )
        self.db.add(class_obj)
        self.db.flush()
        self.db.add(
            TeacherClass(
                teacher_id=teacher_id,
                class_id=class_obj.id,
                is_active=True,
            )
        )
        self.audit_log_service.record(
            event_type="class.create",
            user_id=current_user.id,
            resource_type="class",
            resource_id=class_obj.id,
            metadata={
                "name": name,
                "teacher_id": str(teacher_id),
                "academic_period": class_obj.academic_period,
            },
        )
        self.db.commit()
        self.db.refresh(class_obj)
        return class_obj

    def list_classes(
        self,
        *,
        current_user: User,
        include_archived: bool = False,
    ) -> list[Class]:
        query = self.db.query(Class).options(joinedload(Class.memberships))
        if current_user.role == UserRole.ADMIN:
            if not include_archived:
                query = query.filter(Class.is_active.is_(True))
            return query.order_by(Class.created_at.desc()).all()

        if current_user.role == UserRole.TEACHER:
            query = query.join(TeacherClass, TeacherClass.class_id == Class.id).filter(
                TeacherClass.teacher_id == current_user.id,
                TeacherClass.is_active.is_(True),
            )
        else:
            query = query.join(ClassStudent, ClassStudent.class_id == Class.id).filter(
                ClassStudent.student_id == current_user.id,
                ClassStudent.is_active.is_(True),
            )

        if not include_archived:
            query = query.filter(Class.is_active.is_(True))
        return query.order_by(Class.created_at.desc()).all()

    def get_class(self, *, class_id: UUID, current_user: User) -> Class:
        return self._require_class(class_id, current_user, include_inactive=True)

    def update_class(
        self,
        *,
        class_id: UUID,
        current_user: User,
        name: str | None = None,
        description: str | None = None,
    ) -> Class:
        self._require_admin(current_user)
        class_obj = self._require_class(class_id, current_user, include_inactive=True)
        if class_obj.archived_at is not None:
            raise ValueError(f"Class {class_id} is archived and cannot be edited.")
        if name is not None:
            class_obj.name = name
        if description is not None:
            class_obj.description = description
        self.audit_log_service.record(
            event_type="class.update",
            user_id=current_user.id,
            resource_type="class",
            resource_id=class_obj.id,
            metadata={"name": class_obj.name, "description": class_obj.description},
        )
        self.db.commit()
        self.db.refresh(class_obj)
        return class_obj

    def archive_class(self, *, class_id: UUID, current_user: User) -> Class:
        self._require_admin(current_user)
        class_obj = self._require_class(class_id, current_user, include_inactive=True)
        if not class_obj.is_active and class_obj.archived_at is not None:
            return class_obj
        class_obj.is_active = False
        class_obj.archived_at = datetime.now(timezone.utc)
        self.audit_log_service.record(
            event_type="class.archive",
            user_id=current_user.id,
            resource_type="class",
            resource_id=class_obj.id,
        )
        self.db.commit()
        self.db.refresh(class_obj)
        return class_obj

    def add_students(
        self,
        *,
        class_id: UUID,
        current_user: User,
        student_ids: list[UUID],
    ) -> list[ClassStudent]:
        self._require_admin(current_user)
        class_obj = self._require_class(class_id, current_user, include_inactive=True)
        if not class_obj.is_active:
            raise ValueError(f"Class {class_id} is archived.")

        memberships: list[ClassStudent] = []
        for student_id in student_ids:
            student = self.db.query(User).filter(User.id == student_id).first()
            if (
                student is None
                or student.role != UserRole.STUDENT
                or not student.is_active
                or student.anonymized_at is not None
            ):
                raise ValueError(f"Student {student_id} not found.")

            membership = (
                self.db.query(ClassStudent)
                .filter(
                    ClassStudent.class_id == class_obj.id,
                    ClassStudent.student_id == student_id,
                )
                .first()
            )
            if membership and membership.is_active:
                raise ValueError(f"Student {student_id} is already a member of class {class_id}.")

            period_conflict = (
                self.db.query(ClassStudent)
                .join(Class, Class.id == ClassStudent.class_id)
                .filter(
                    ClassStudent.student_id == student_id,
                    ClassStudent.is_active.is_(True),
                    Class.academic_period == class_obj.academic_period,
                )
                .first()
            )
            if period_conflict and period_conflict.class_id != class_obj.id:
                raise ValueError(
                    "Student "
                    f"{student_id} already has an active class for period "
                    f"{class_obj.academic_period}."
                )

            if membership is None:
                membership = ClassStudent(
                    class_id=class_obj.id,
                    student_id=student_id,
                    academic_period=class_obj.academic_period,
                    is_active=True,
                )
                self.db.add(membership)
                self.db.flush()
            else:
                membership.academic_period = class_obj.academic_period
                membership.is_active = True
                membership.archived_at = None

            memberships.append(membership)
            self.audit_log_service.record(
                event_type="class_student.add",
                user_id=current_user.id,
                resource_type="class_student",
                resource_id=membership.id,
                metadata={
                    "class_id": str(class_obj.id),
                    "student_id": str(student_id),
                    "academic_period": class_obj.academic_period,
                },
            )

        self.db.commit()
        for membership in memberships:
            self.db.refresh(membership)
        return memberships

    def list_students(
        self,
        *,
        class_id: UUID,
        current_user: User,
        include_archived: bool = False,
    ) -> list[ClassStudent]:
        class_obj = self._require_class(class_id, current_user, include_inactive=True)
        query = (
            self.db.query(ClassStudent)
            .options(joinedload(ClassStudent.student))
            .filter(ClassStudent.class_id == class_obj.id)
        )
        if not include_archived:
            query = query.filter(ClassStudent.is_active.is_(True))
        return query.order_by(ClassStudent.created_at.asc()).all()

    def remove_student(
        self,
        *,
        class_id: UUID,
        student_id: UUID,
        current_user: User,
    ) -> None:
        self._require_admin(current_user)
        class_obj = self._require_class(class_id, current_user, include_inactive=True)
        membership = (
            self.db.query(ClassStudent)
            .filter(ClassStudent.class_id == class_obj.id, ClassStudent.student_id == student_id)
            .first()
        )
        if membership is None:
            raise ValueError(f"Membership {class_id}/{student_id} not found.")
        membership.is_active = False
        membership.archived_at = datetime.now(timezone.utc)
        self.audit_log_service.record(
            event_type="class_student.remove",
            user_id=current_user.id,
            resource_type="class_student",
            resource_id=membership.id,
            metadata={
                "class_id": str(class_obj.id),
                "student_id": str(student_id),
                "academic_period": class_obj.academic_period,
            },
        )
        self.db.commit()

    def list_teachers(
        self,
        *,
        class_id: UUID,
        current_user: User,
        include_archived: bool = False,
    ) -> list[TeacherClass]:
        class_obj = self._require_class(class_id, current_user, include_inactive=True)
        query = (
            self.db.query(TeacherClass)
            .options(joinedload(TeacherClass.teacher))
            .filter(TeacherClass.class_id == class_obj.id)
        )
        if not include_archived:
            query = query.filter(TeacherClass.is_active.is_(True))
        return query.order_by(TeacherClass.created_at.asc()).all()

    def add_teachers(
        self,
        *,
        class_id: UUID,
        current_user: User,
        teacher_ids: list[UUID],
    ) -> list[TeacherClass]:
        self._require_admin(current_user)
        class_obj = self._require_class(class_id, current_user, include_inactive=True)
        if not class_obj.is_active:
            raise ValueError(f"Class {class_id} is archived.")

        teacher_links: list[TeacherClass] = []
        for teacher_id in teacher_ids:
            teacher = self.db.query(User).filter(User.id == teacher_id).first()
            if (
                teacher is None
                or teacher.role != UserRole.TEACHER
                or not teacher.is_active
                or teacher.anonymized_at is not None
            ):
                raise ValueError(f"Teacher {teacher_id} not found.")

            teacher_link = (
                self.db.query(TeacherClass)
                .filter(
                    TeacherClass.class_id == class_obj.id,
                    TeacherClass.teacher_id == teacher_id,
                )
                .first()
            )
            if teacher_link and teacher_link.is_active:
                raise ValueError(
                    f"Teacher {teacher_id} is already associated with class {class_id}."
                )

            if teacher_link is None:
                teacher_link = TeacherClass(
                    class_id=class_obj.id,
                    teacher_id=teacher_id,
                    is_active=True,
                )
                self.db.add(teacher_link)
                self.db.flush()
            else:
                teacher_link.is_active = True
                teacher_link.archived_at = None

            teacher_links.append(teacher_link)
            self.audit_log_service.record(
                event_type="class_teacher.add",
                user_id=current_user.id,
                resource_type="class_teacher",
                resource_id=teacher_link.id,
                metadata={
                    "class_id": str(class_obj.id),
                    "teacher_id": str(teacher_id),
                },
            )

        self.db.commit()
        for teacher_link in teacher_links:
            self.db.refresh(teacher_link)
        return teacher_links

    def remove_teacher(
        self,
        *,
        class_id: UUID,
        teacher_id: UUID,
        current_user: User,
    ) -> None:
        self._require_admin(current_user)
        class_obj = self._require_class(class_id, current_user, include_inactive=True)
        teacher_link = (
            self.db.query(TeacherClass)
            .filter(
                TeacherClass.class_id == class_obj.id,
                TeacherClass.teacher_id == teacher_id,
            )
            .first()
        )
        if teacher_link is None:
            raise ValueError(f"Teacher link {class_id}/{teacher_id} not found.")
        if teacher_link.is_active:
            active_links = (
                self.db.query(TeacherClass)
                .filter(
                    TeacherClass.class_id == class_obj.id,
                    TeacherClass.is_active.is_(True),
                )
                .count()
            )
            if active_links <= 1:
                raise ValueError("A class must keep at least one active teacher.")
        teacher_link.is_active = False
        teacher_link.archived_at = datetime.now(timezone.utc)
        self.audit_log_service.record(
            event_type="class_teacher.remove",
            user_id=current_user.id,
            resource_type="class_teacher",
            resource_id=teacher_link.id,
            metadata={
                "class_id": str(class_obj.id),
                "teacher_id": str(teacher_id),
            },
        )
        self.db.commit()

    def list_my_classes(self, *, current_user: User, include_archived: bool = False) -> list[Class]:
        if current_user.role == UserRole.ADMIN:
            return self.list_classes(current_user=current_user, include_archived=include_archived)
        if current_user.role == UserRole.TEACHER:
            return self.list_classes(current_user=current_user, include_archived=include_archived)
        query = (
            self.db.query(Class)
            .join(ClassStudent, ClassStudent.class_id == Class.id)
            .filter(
                ClassStudent.student_id == current_user.id,
                ClassStudent.is_active.is_(True),
            )
        )
        if not include_archived:
            query = query.filter(Class.is_active.is_(True))
        return query.order_by(Class.created_at.desc()).all()
