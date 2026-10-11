import json
import logging
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.domain import Principal
from app.errors import ServiceError
from app.main import create_app
from app.repositories.memory import InMemoryLearningRepository
from app.services.learning import LearningService


@pytest.mark.parametrize("learner_id", ["learner-red-2", "learner-blue-1", "learner-deleted"])
def test_non_owned_progress_is_not_disclosed(learner_id: str) -> None:
    with TestClient(create_app()) as client:
        response = client.get(
            f"/v1/learners/{learner_id}/progress",
            headers={"Authorization": "Bearer demo-learner-red"},
        )
    assert response.status_code == 404
    assert set(response.json()["error"]) == {"code", "message", "request_id"}
    assert learner_id not in response.text
    assert "completion_percent" not in response.text
    assert response.headers["X-Request-ID"] == response.json()["error"]["request_id"]


@pytest.mark.parametrize("credential", [None, "Bearer unknown", "Basic demo-learner-red"])
def test_authentication_required(credential: str | None) -> None:
    headers = {"Authorization": credential} if credential else {}
    with TestClient(create_app()) as client:
        response = client.get("/v1/content", headers=headers)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize("suffix", ["?limit=0", "?limit=21", "?limit=invalid"])
def test_invalid_query_has_safe_error(suffix: str) -> None:
    with TestClient(create_app()) as client:
        response = client.get(
            "/v1/content" + suffix, headers={"Authorization": "Bearer demo-learner-red"}
        )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"
    assert "traceback" not in response.text.lower()
    assert "invalid" not in response.json()["error"]["message"].lower()


@pytest.mark.parametrize("learner_id", ["invalid%20id", "invalid%27id", "a" * 65])
def test_malformed_identifiers(learner_id: str) -> None:
    with TestClient(create_app()) as client:
        response = client.get(
            f"/v1/learners/{learner_id}/progress",
            headers={"Authorization": "Bearer demo-learner-red"},
        )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


@pytest.mark.parametrize("request_id", ["", "spaces are not valid", "a" * 65, "bad\r\nheader"])
def test_unsafe_request_ids_are_replaced(request_id: str) -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health", headers={"X-Request-ID": request_id})
    UUID(response.headers["X-Request-ID"])


def test_synthetic_fixture_and_repository_boundaries() -> None:
    repository = InMemoryLearningRepository()
    assert len(repository.tenants) == 2
    assert len(repository.learners) == 3
    assert len(repository.courses) == 2
    assert repository.get_progress("tenant-red", "learner-blue-1") is None
    assert repository.get_progress("tenant-blue", "learner-red-1") is None
    assert all(item.approved for item in repository.list_approved_content("tenant-red", 20))
    assert repository.list_approved_content("tenant-missing", 20) == ()


def test_service_checks_owner_independently_of_routes() -> None:
    service = LearningService(InMemoryLearningRepository())
    principal = Principal(subject="learner-red-1", tenant_id="tenant-red")
    with pytest.raises(ServiceError) as exception:
        service.read_progress(principal, "learner-red-2")
    assert exception.value.code == "not_found"


def test_blue_principal_sees_only_blue_data() -> None:
    with TestClient(create_app()) as client:
        headers = {"Authorization": "Bearer demo-learner-blue"}
        content = client.get("/v1/content", headers=headers)
        progress = client.get("/v1/learners/learner-blue-1/progress", headers=headers)
    assert content.json()["items"][0]["id"] == "content-blue-approved"
    assert "red" not in content.text
    assert progress.status_code == 200


def test_headers_without_credential_cannot_authenticate() -> None:
    with TestClient(create_app()) as client:
        response = client.get(
            "/v1/content", headers={"X-User-ID": "learner-red-1", "X-Tenant-ID": "tenant-red"}
        )
    assert response.status_code == 401


def test_request_logs_exclude_tokens_and_payloads(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="learning.requests")
    with TestClient(create_app()) as client:
        response = client.get(
            "/v1/content?private=must-not-log-this",
            headers={
                "Authorization": "Bearer demo-learner-red",
                "X-Request-ID": "demo-learner-red",
            },
        )
    events = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "learning.requests"
    ]
    assert events[-1]["request_id"] == response.headers["X-Request-ID"]
    serialized = json.dumps(events)
    assert "demo-learner-red" not in serialized
    assert "must-not-log-this" not in serialized
    assert "learner-red-1" not in serialized
    assert events[-1]["route"] == "/v1/content"


def test_unknown_route_and_unsupported_write_have_stable_errors() -> None:
    with TestClient(create_app()) as client:
        missing = client.get("/not-a-route")
        write = client.post("/v1/content", json={"private": "never-echo"})
    assert missing.status_code == 404
    assert write.status_code == 405
    assert "never-echo" not in write.text
    assert set(write.json()["error"]) == {"code", "message", "request_id"}


def test_repository_error_is_safe() -> None:
    class BrokenRepository(InMemoryLearningRepository):
        def get_progress(self, tenant_id: str, learner_id: str) -> None:
            raise RuntimeError("private-record-must-not-escape")

    with TestClient(create_app(repository=BrokenRepository())) as client:
        response = client.get(
            "/v1/learners/learner-red-1/progress",
            headers={"Authorization": "Bearer demo-learner-red"},
        )
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "private-record" not in response.text


@pytest.mark.parametrize("environment", ["production", "staging", ""])
def test_non_local_configuration_refused(
    monkeypatch: pytest.MonkeyPatch, environment: str
) -> None:
    monkeypatch.setenv("LEARNING_ENVIRONMENT", environment)
    with pytest.raises(ValueError, match="Invalid learning API configuration"):
        create_app()


@pytest.mark.parametrize("encoded", ["{}", "not-json", '{"sensitive-value":"forged-learner"}'])
def test_invalid_credential_configuration_is_not_echoed(
    monkeypatch: pytest.MonkeyPatch, encoded: str
) -> None:
    monkeypatch.setenv("LEARNING_DEMO_CREDENTIALS_JSON", encoded)
    with pytest.raises(ValueError) as exception:
        Settings.from_environment()
    assert str(exception.value) == "Invalid learning API configuration"
    assert encoded not in str(exception.value)
