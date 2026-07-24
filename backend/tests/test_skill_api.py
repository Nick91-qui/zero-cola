from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_and_list_skills(auth_headers):
    payload = {
        "code": "EM13MAT101",
        "description": "Análise e interpretação de funções no plano cartesiano",
        "subject": "Matemática",
        "curriculum": "BNCC",
    }

    res = client.post("/api/v1/skills", json=payload, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["code"] == "EM13MAT101"
    assert data["description"] == "Análise e interpretação de funções no plano cartesiano"

    # List skills
    list_res = client.get("/api/v1/skills", headers=auth_headers)
    assert list_res.status_code == 200
    skills = list_res.json()
    assert any(s["code"] == "EM13MAT101" for s in skills)
