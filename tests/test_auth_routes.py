from fastapi.testclient import TestClient

from app.main import app


def test_me_requires_bearer_token():
    client = TestClient(app)
    response = client.get("/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing bearer token."
