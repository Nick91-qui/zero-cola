from datetime import datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app
from app.models.attempt import Attempt
from app.models.consent import Consent
from app.models.enums import AttemptStatus, UserRole
from app.models.exam import Exam
from app.models.user import User
from app.schemas.exam import ExamCreate, ExamQuestionCreate, QuestionCreate
from app.services.exam import ExamService
from tests.helpers import create_user

client = TestClient(app)


def _register_user(
    test_db_session,
    *,
    email: str,
    password: str,
    role: UserRole,
    student_code: str | None = None,
):
    return create_user(
        test_db_session,
        email=email,
        password=password,
        role=role,
        student_code=student_code,
    )


def _login_user(email: str, password: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    client.cookies.clear()
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _create_teacher_user(test_db_session, email: str, password: str) -> tuple[User, dict[str, str]]:
    _register_user(test_db_session, email=email, password=password, role=UserRole.TEACHER)
    user = test_db_session.query(User).filter(User.email == email).one()
    return user, _login_user(email, password)


def _create_student_user(
    test_db_session,
    *,
    email: str,
    password: str,
    student_code: str,
) -> tuple[User, dict[str, str]]:
    _register_user(
        test_db_session,
        email=email,
        password=password,
        role=UserRole.STUDENT,
        student_code=student_code,
    )
    user = test_db_session.query(User).filter(User.email == email).one()
    return user, _login_user(email, password)


def _create_admin_user(test_db_session, email: str, password: str) -> tuple[User, dict[str, str]]:
    _register_user(test_db_session, email=email, password=password, role=UserRole.ADMIN)
    user = test_db_session.query(User).filter(User.email == email).one()
    return user, _login_user(email, password)


def _create_published_exam(test_db_session, teacher: User, *, title: str) -> Exam:
    service = ExamService(test_db_session)
    exam = service.create_exam(
        ExamCreate(
            title=title,
            total_questions=1,
            questions=[
                ExamQuestionCreate(
                    display_order=1,
                    question=QuestionCreate(
                        statement=f"{title} question",
                        options={"A": "A", "B": "B"},
                        correct_answer="A",
                    ),
                )
            ],
        ),
        teacher_id=teacher.id,
    )
    return service.publish_exam(exam.id)


def _create_in_progress_attempt(
    test_db_session,
    *,
    exam: Exam,
    student: User,
) -> Attempt:
    attempt = Attempt(
        exam_id=exam.id,
        answer_key_id=exam.answer_key.id if exam.answer_key else None,
        student_id=student.id,
        student_code=student.student_code,
        attempt_number=1,
        status=AttemptStatus.IN_PROGRESS.value,
        source="ONLINE",
        total_questions=1,
        correct_answers=0,
        incorrect_answers=0,
        accuracy_percentage=Decimal("0.00"),
        raw_score=Decimal("0.00"),
        final_score=Decimal("0.00"),
        started_at=datetime.now(timezone.utc),
    )
    test_db_session.add(attempt)
    test_db_session.commit()
    test_db_session.refresh(attempt)
    return attempt


def test_class_ownership_and_student_access_controls(override_get_db, test_db_session):
    teacher_a, teacher_a_headers = _create_teacher_user(
        test_db_session,
        "teacher_a_step9@cola-zero.edu",
        "teacher-a-pass",
    )
    teacher_b, teacher_b_headers = _create_teacher_user(
        test_db_session,
        "teacher_b_step9@cola-zero.edu",
        "teacher-b-pass",
    )
    student, student_headers = _create_student_user(
        test_db_session,
        email="student_step9@cola-zero.edu",
        password="student-pass",
        student_code="12345",
    )
    _admin, admin_headers = _create_admin_user(
        test_db_session,
        "admin_step9@cola-zero.edu",
        "admin-pass",
    )

    forbidden_create = client.post(
        "/api/v1/classes",
        json={
            "name": "Turma proibida",
            "description": "professor não pode criar",
            "teacher_id": str(teacher_a.id),
        },
        headers=teacher_a_headers,
    )
    assert forbidden_create.status_code == 403

    class_a_res = client.post(
        "/api/v1/classes",
        json={
            "name": "Turma A",
            "description": "Owned by teacher A",
            "teacher_id": str(teacher_a.id),
        },
        headers=admin_headers,
    )
    assert class_a_res.status_code == 201, class_a_res.text
    class_a = class_a_res.json()

    class_b_res = client.post(
        "/api/v1/classes",
        json={
            "name": "Turma B",
            "description": "Owned by teacher B",
            "teacher_id": str(teacher_b.id),
        },
        headers=admin_headers,
    )
    assert class_b_res.status_code == 201, class_b_res.text
    class_b = class_b_res.json()

    teacher_a_list = client.get("/api/v1/classes", headers=teacher_a_headers)
    assert teacher_a_list.status_code == 200
    assert [item["id"] for item in teacher_a_list.json()] == [class_a["id"]]

    teacher_b_list = client.get("/api/v1/classes", headers=teacher_b_headers)
    assert teacher_b_list.status_code == 200
    assert [item["id"] for item in teacher_b_list.json()] == [class_b["id"]]

    admin_list = client.get("/api/v1/classes", headers=admin_headers)
    assert admin_list.status_code == 200
    assert {item["id"] for item in admin_list.json()} == {class_a["id"], class_b["id"]}

    forbidden_get = client.get(f"/api/v1/classes/{class_a['id']}", headers=teacher_b_headers)
    assert forbidden_get.status_code == 404

    forbidden_update = client.patch(
        f"/api/v1/classes/{class_a['id']}",
        json={"name": "Hacked"},
        headers=teacher_b_headers,
    )
    assert forbidden_update.status_code == 403

    add_student = client.post(
        f"/api/v1/classes/{class_a['id']}/students",
        json={"student_ids": [str(student.id)]},
        headers=admin_headers,
    )
    assert add_student.status_code == 201, add_student.text
    assert add_student.json()[0]["student_id"] == str(student.id)

    conflict_student = client.post(
        f"/api/v1/classes/{class_b['id']}/students",
        json={"student_ids": [str(student.id)]},
        headers=admin_headers,
    )
    assert conflict_student.status_code == 409

    forbidden_add_student = client.post(
        f"/api/v1/classes/{class_a['id']}/students",
        json={"student_ids": [str(student.id)]},
        headers=teacher_b_headers,
    )
    assert forbidden_add_student.status_code == 403

    student_classes = client.get("/api/v1/me/classes", headers=student_headers)
    assert student_classes.status_code == 200
    assert [item["id"] for item in student_classes.json()] == [class_a["id"]]

    forbidden_student_detail = client.get(
        f"/api/v1/classes/{class_a['id']}",
        headers=student_headers,
    )
    assert forbidden_student_detail.status_code == 403

    remove_student = client.delete(
        f"/api/v1/classes/{class_a['id']}/students/{student.id}",
        headers=teacher_b_headers,
    )
    assert remove_student.status_code == 403

    forbidden_student_memberships = client.get(
        f"/api/v1/classes/{class_a['id']}/students",
        headers=teacher_b_headers,
    )
    assert forbidden_student_memberships.status_code == 404

    archive_res = client.post(f"/api/v1/classes/{class_a['id']}/archive", headers=teacher_a_headers)
    assert archive_res.status_code == 403

    archive_res = client.post(f"/api/v1/classes/{class_a['id']}/archive", headers=admin_headers)
    assert archive_res.status_code == 200
    assert archive_res.json()["is_active"] is False

    teacher_a_list_after_archive = client.get("/api/v1/classes", headers=teacher_a_headers)
    assert teacher_a_list_after_archive.status_code == 200
    assert [item["id"] for item in teacher_a_list_after_archive.json()] == []

    archived_detail = client.get(f"/api/v1/classes/{class_a['id']}", headers=teacher_a_headers)
    assert archived_detail.status_code == 200
    assert archived_detail.json()["is_active"] is False

    update_archived = client.patch(
        f"/api/v1/classes/{class_a['id']}",
        json={"description": "nope"},
        headers=teacher_a_headers,
    )
    assert update_archived.status_code == 403

    admin_memberships = client.get(
        f"/api/v1/classes/{class_a['id']}/students",
        headers=admin_headers,
    )
    assert admin_memberships.status_code == 200
    assert admin_memberships.json()[0]["student_id"] == str(student.id)


def test_teachers_can_share_a_class_and_operate_on_it(override_get_db, test_db_session):
    teacher_a, teacher_a_headers = _create_teacher_user(
        test_db_session,
        "teacher_share_a@cola-zero.edu",
        "teacher-share-a-pass",
    )
    teacher_b, teacher_b_headers = _create_teacher_user(
        test_db_session,
        "teacher_share_b@cola-zero.edu",
        "teacher-share-b-pass",
    )
    student, student_headers = _create_student_user(
        test_db_session,
        email="student_share@cola-zero.edu",
        password="student-share-pass",
        student_code="24680",
    )
    _admin, admin_headers = _create_admin_user(
        test_db_session,
        "admin_share@cola-zero.edu",
        "admin-share-pass",
    )

    class_res = client.post(
        "/api/v1/classes",
        json={
            "name": "Turma Compartilhada",
            "description": "turma de teste",
            "academic_period": "2026",
            "teacher_id": str(teacher_a.id),
        },
        headers=admin_headers,
    )
    assert class_res.status_code == 201, class_res.text
    class_id = class_res.json()["id"]

    forbidden_before_share = client.get(f"/api/v1/classes/{class_id}", headers=teacher_b_headers)
    assert forbidden_before_share.status_code == 404

    share_res = client.post(
        f"/api/v1/classes/{class_id}/teachers",
        json={"teacher_ids": [str(teacher_b.id)]},
        headers=admin_headers,
    )
    assert share_res.status_code == 201, share_res.text
    assert [item["teacher_id"] for item in share_res.json()] == [str(teacher_b.id)]

    teacher_b_list = client.get("/api/v1/classes", headers=teacher_b_headers)
    assert teacher_b_list.status_code == 200
    assert class_id in [item["id"] for item in teacher_b_list.json()]

    class_detail_b = client.get(f"/api/v1/classes/{class_id}", headers=teacher_b_headers)
    assert class_detail_b.status_code == 200
    assert {item["teacher_id"] for item in class_detail_b.json()["teachers"]} == {
        str(teacher_a.id),
        str(teacher_b.id),
    }

    add_student_res = client.post(
        f"/api/v1/classes/{class_id}/students",
        json={"student_ids": [str(student.id)]},
        headers=admin_headers,
    )
    assert add_student_res.status_code == 201, add_student_res.text
    assert add_student_res.json()[0]["student_id"] == str(student.id)

    student_classes = client.get("/api/v1/me/classes", headers=student_headers)
    assert student_classes.status_code == 200
    assert [item["id"] for item in student_classes.json()] == [class_id]


def test_audit_logs_consents_and_monitoring_security_events(override_get_db, test_db_session):
    teacher, teacher_headers = _create_teacher_user(
        test_db_session,
        "teacher_monitoring@cola-zero.edu",
        "teacher-monitoring-pass",
    )
    other_teacher, other_teacher_headers = _create_teacher_user(
        test_db_session,
        "teacher_monitoring_other@cola-zero.edu",
        "teacher-monitoring-other-pass",
    )
    student, student_headers = _create_student_user(
        test_db_session,
        email="student_monitoring@cola-zero.edu",
        password="student-monitoring-pass",
        student_code="54321",
    )
    _admin, admin_headers = _create_admin_user(
        test_db_session,
        "admin_monitoring@cola-zero.edu",
        "admin-monitoring-pass",
    )

    class_res = client.post(
        "/api/v1/classes",
        json={
            "name": "Monitorada",
            "description": "classe",
            "teacher_id": str(teacher.id),
        },
        headers=admin_headers,
    )
    assert class_res.status_code == 201, class_res.text

    exam = _create_published_exam(test_db_session, teacher, title="Exame monitorado")
    attempt = _create_in_progress_attempt(test_db_session, exam=exam, student=student)

    consent_res = client.post(
        "/api/v1/consents/monitoring",
        json={"purpose": "monitoring", "granted": True, "policy_version": "step9-v1"},
        headers=student_headers,
    )
    assert consent_res.status_code == 201, consent_res.text
    assert consent_res.json()["consent_type"] == "monitoring"
    assert consent_res.json()["granted"] is True

    my_consents_res = client.get("/api/v1/me/consents", headers=student_headers)
    assert my_consents_res.status_code == 200
    assert [item["consent_type"] for item in my_consents_res.json()] == ["monitoring"]

    first_event_res = client.post(
        f"/api/v1/attempts/{attempt.id}/security-events",
        json={"event_type": "blur"},
        headers=student_headers,
    )
    assert first_event_res.status_code == 201, first_event_res.text
    assert first_event_res.json()["event_type"] == "blur"

    revoke_res = client.delete("/api/v1/consents/monitoring", headers=student_headers)
    assert revoke_res.status_code == 200
    assert revoke_res.json()["granted"] is False

    second_event_res = client.post(
        f"/api/v1/attempts/{attempt.id}/security-events",
        json={"event_type": "focus"},
        headers=student_headers,
    )
    assert second_event_res.status_code == 403

    teacher_events = client.get(
        f"/api/v1/attempts/{attempt.id}/security-events",
        headers=teacher_headers,
    )
    assert teacher_events.status_code == 200
    assert [event["event_type"] for event in teacher_events.json()] == ["blur"]

    forbidden_teacher_events = client.get(
        f"/api/v1/attempts/{attempt.id}/security-events",
        headers=other_teacher_headers,
    )
    assert forbidden_teacher_events.status_code == 403

    forbidden_student_events = client.get(
        f"/api/v1/attempts/{attempt.id}/security-events",
        headers=student_headers,
    )
    assert forbidden_student_events.status_code == 403

    audit_logs = client.get("/api/v1/audit-logs", headers=admin_headers)
    assert audit_logs.status_code == 200
    event_types = {item["event_type"] for item in audit_logs.json()}
    assert "class.create" in event_types
    assert "consent.updated" in event_types
    assert "consent.revoked" in event_types
    assert "security_event.recorded" in event_types
    assert "auth.login_success" in event_types

    assert client.get("/api/v1/audit-logs", headers=teacher_headers).status_code == 403
    assert client.get("/api/v1/audit-logs", headers=student_headers).status_code == 403


def test_privacy_export_and_anonymization_blocks_access(override_get_db, test_db_session):
    student, student_headers = _create_student_user(
        test_db_session,
        email="student_privacy@cola-zero.edu",
        password="student-privacy-pass",
        student_code="67890",
    )

    policy_res = client.get("/api/v1/privacy-policy")
    assert policy_res.status_code == 200
    assert policy_res.json()["title"] == "COLA-ZERO Privacy Policy"

    consent_res = client.post(
        "/api/v1/consents/monitoring",
        json={"purpose": "monitoring", "granted": True, "policy_version": "step9-v1"},
        headers=student_headers,
    )
    assert consent_res.status_code == 201, consent_res.text

    my_consents_res = client.get("/api/v1/me/consents", headers=student_headers)
    assert my_consents_res.status_code == 200
    assert my_consents_res.json()[0]["granted"] is True

    class_res = client.post(
        "/api/v1/classes",
        json={
            "name": "Turma Privacidade",
            "description": "classe",
            "teacher_id": str(student.id),
        },
        headers=student_headers,
    )
    assert class_res.status_code == 403

    export_res = client.get("/api/v1/me/data-export", headers=student_headers)
    assert export_res.status_code == 200
    export_payload = export_res.json()["data"]
    assert export_payload["user"]["email"] == "student_privacy@cola-zero.edu"
    assert export_payload["consents"]
    assert export_payload["audit_logs"]

    assert client.get("/api/v1/me/data-export").status_code == 401

    anonymize_res = client.post("/api/v1/me/request-anonymization", headers=student_headers)
    assert anonymize_res.status_code == 202
    assert anonymize_res.json()["status"] == "anonymized"

    test_db_session.expire_all()
    anonymized_student = test_db_session.query(User).filter(User.id == student.id).one()
    assert anonymized_student.is_active is False
    assert anonymized_student.anonymized_at is not None
    assert anonymized_student.email.startswith("anonymized-")

    revoked_consent = (
        test_db_session.query(Consent)
        .filter(Consent.user_id == student.id, Consent.consent_type == "monitoring")
        .one()
    )
    assert revoked_consent.granted is False
    assert revoked_consent.revoked_at is not None

    current_user_res = client.get("/api/v1/auth/me", headers=student_headers)
    assert current_user_res.status_code == 401

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "student_privacy@cola-zero.edu", "password": "student-privacy-pass"},
    )
    assert login_res.status_code == 401

    assert client.get("/api/v1/me/data-export", headers=student_headers).status_code == 401
