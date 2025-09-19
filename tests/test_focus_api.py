from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _login(client: TestClient, password: str = "test-token") -> None:
    r = client.post("/api/login", json={"password": password})
    assert r.status_code == 200, r.text


def test_focus_score_with_mock_capture(monkeypatch, tmp_path: Path):
    # Arrange environment for mock camera and local storage
    monkeypatch.setenv("ADMIN_TOKEN", "test-token")
    monkeypatch.setenv("SKYLAPSE_LOCAL_DIR", str(tmp_path))
    monkeypatch.setenv("SKYLAPSE_CAMERA", "mock")

    client = TestClient(app)

    # Login via cookie
    _login(client)

    # Capture once to generate an image (cookie auth)
    r_cap = client.post("/api/admin/capture_once")
    assert r_cap.status_code == 200, r_cap.text
    body = r_cap.json()
    img_path = Path(body["path"])
    assert img_path.exists(), "image file should exist"

    # Act: compute focus score on latest
    r = client.get("/api/admin/focus_score")
    assert r.status_code == 200, r.text
    payload = r.json()
    assert set(["path", "url", "width", "height", "score"]).issubset(payload.keys())
    assert payload["score"] >= 0.0


def test_frontend_index_served(monkeypatch, tmp_path: Path):
    # Index should be served from static/index.html in repo
    monkeypatch.setenv("ADMIN_TOKEN", "test-token")
    monkeypatch.setenv("SKYLAPSE_LOCAL_DIR", str(tmp_path))

    client = TestClient(app)

    r = client.get("/")
    assert r.status_code == 200
    assert b"Skylapse" in r.content
