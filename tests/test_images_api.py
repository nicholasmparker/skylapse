from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_capture_writes_sidecar_and_db(monkeypatch, tmp_path: Path):
    # Configure environment for mock capture
    monkeypatch.setenv("ADMIN_TOKEN", "test-token")
    monkeypatch.setenv("SKYLAPSE_LOCAL_DIR", str(tmp_path))
    monkeypatch.setenv("SKYLAPSE_CAMERA", "mock")

    client = TestClient(app)

    # Capture two images
    r1 = client.post("/api/admin/capture_once", headers={"Authorization": "Bearer test-token"})
    assert r1.status_code == 200, r1.text
    body1 = r1.json()
    p1 = Path(body1["path"])
    assert p1.exists() and p1.suffix == ".jpg"
    assert p1.with_suffix(".json").exists()

    r2 = client.post("/api/admin/capture_once", headers={"Authorization": "Bearer test-token"})
    assert r2.status_code == 200, r2.text
    body2 = r2.json()
    p2 = Path(body2["path"])
    assert p2.exists() and p2.suffix == ".jpg"
    assert p2.with_suffix(".json").exists()

    # List images without filters
    list_resp = client.get("/api/images", params={"page": 1, "page_size": 10})
    assert list_resp.status_code == 200, list_resp.text
    payload = list_resp.json()
    assert payload["page"] == 1
    assert payload["page_size"] == 10
    assert payload["total"] >= 2
    assert isinstance(payload["items"], list)
    assert len(payload["items"]) >= 2
    first = payload["items"][0]
    assert {"path", "url", "captured_at", "size_bytes", "width", "height"}.issubset(first.keys())

    # Filter by today's UTC date
    ts = body1["captured_at"]
    dt = datetime.fromtimestamp(ts, tz=UTC)
    day_str = dt.strftime("%Y-%m-%d")
    list_day = client.get("/api/images", params={"from_": day_str, "to": day_str})
    assert list_day.status_code == 200, list_day.text
    pl_day = list_day.json()
    assert pl_day["total"] >= 1
