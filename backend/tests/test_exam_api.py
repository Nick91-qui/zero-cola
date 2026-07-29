from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_and_get_exam_api(auth_headers):
    # 1. Create Exam
    payload = {
        "title": "Avaliação de Física - 1º Bimestre",
        "description": "Mecânica Clássica",
        "class_id": "TURMA-101",
        "total_questions": 2,
        "max_score": 10.0,
        "questions": [
            {
                "display_order": 2,
                "question": {
                    "statement": "Questão 2",
                    "correct_answer": "B",
                },
            },
            {
                "display_order": 1,
                "question": {
                    "statement": "Questão 1",
                    "correct_answer": "A",
                },
            },
        ],
    }

    response = client.post("/api/v1/exams", json=payload, headers=auth_headers)
    assert response.status_code == 201
    exam = response.json()
    exam_id = exam["id"]
    assert exam["title"] == "Avaliação de Física - 1º Bimestre"
    assert exam["class_id"] == "TURMA-101"
    assert exam["omr_template_id"] is None

    publish_res = client.post(f"/api/v1/exams/{exam_id}/publish", headers=auth_headers)
    assert publish_res.status_code == 200

    # 2. List Exams
    list_res = client.get("/api/v1/exams", headers=auth_headers)
    assert list_res.status_code == 200
    exams = list_res.json()
    assert len(exams) >= 1

    # 3. Get Exam Detail
    detail_res = client.get(f"/api/v1/exams/{exam_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == exam_id
    assert len(detail["questions"]) == 2
    assert len(detail["exam_questions"]) == 2

    # 4. Get Statistics
    stats_res = client.get(f"/api/v1/exams/{exam_id}/statistics", headers=auth_headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["exam_id"] == exam_id
    assert len(stats["question_statistics"]) == 2

    # 5. Export PDF
    pdf_res = client.get(f"/api/v1/exams/{exam_id}/export/pdf", headers=auth_headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF")

    # 6. Export XLSX
    xlsx_res = client.get(f"/api/v1/exams/{exam_id}/export/xlsx", headers=auth_headers)
    assert xlsx_res.status_code == 200
    assert "spreadsheetml" in xlsx_res.headers["content-type"]
