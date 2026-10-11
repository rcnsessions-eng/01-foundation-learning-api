from fastapi.testclient import TestClient

from app.main import create_app


def test_health_and_correlation_id() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health", headers={"X-Request-ID": "foundation-check"})
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}
    assert response.headers["X-Request-ID"] == "foundation-check"


def test_approved_content_only() -> None:
    with TestClient(create_app()) as client:
        response = client.get(
            "/v1/content", headers={"Authorization": "Bearer demo-learner-red"}
        )
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == ["content-red-approved"]
    assert "draft" not in response.text
    assert "blue" not in response.text


def test_own_progress_and_cross_tenant_denial() -> None:
    with TestClient(create_app()) as client:
        headers = {"Authorization": "Bearer demo-learner-red"}
        own = client.get("/v1/learners/learner-red-1/progress", headers=headers)
        foreign = client.get("/v1/learners/learner-blue-1/progress", headers=headers)
        unknown = client.get("/v1/learners/learner-missing/progress", headers=headers)
    assert own.status_code == 200
    assert own.json()["learner_id"] == "learner-red-1"
    assert foreign.status_code == unknown.status_code == 404
    assert foreign.json()["error"]["code"] == unknown.json()["error"]["code"] == "not_found"
    assert "score" not in foreign.text


def test_spoofed_identity_headers_do_not_change_principal() -> None:
    with TestClient(create_app()) as client:
        response = client.get(
            "/v1/learners/learner-blue-1/progress",
            headers={
                "Authorization": "Bearer demo-learner-red",
                "X-Tenant-ID": "tenant-blue",
                "X-User-ID": "learner-blue-1",
                "X-Role": "admin",
            },
        )
    assert response.status_code == 404
