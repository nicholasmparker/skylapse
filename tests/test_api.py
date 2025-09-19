from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_health_requires_token(monkeypatch, tmp_path: Path):
    # No token --> 503 per security rules
    monkeypatch.delenv("ADMIN_TOKEN", raising=False)
    client = TestClient(app)
    resp = client.get("/api/admin/health")
    assert resp.status_code == 503


def test_health_ok_with_token(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ADMIN_TOKEN", "test-token")
    monkeypatch.setenv("SKYLAPSE_LOCAL_DIR", str(tmp_path))
    client = TestClient(app)
    resp = client.get("/api/admin/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["local_dir"] == str(tmp_path)
