from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_capture_once_saves_image(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ADMIN_TOKEN", "test-token")
    monkeypatch.setenv("SKYLAPSE_LOCAL_DIR", str(tmp_path))
    monkeypatch.setenv("SKYLAPSE_CAMERA", "mock")

    client = TestClient(app)

    resp = client.post("/api/admin/capture_once")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    p = Path(body["path"])
    assert p.exists()
    assert p.suffix.lower() == ".jpg"
    # Media URL should be under /media
    assert body["url"].startswith("/media/")
