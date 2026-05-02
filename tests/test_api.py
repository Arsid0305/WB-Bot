import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("WB_TOKEN", "test")
os.environ.setdefault("OZON_CLIENT_ID", "test")
os.environ.setdefault("OZON_API_KEY", "test")
os.environ.setdefault("OPENAI_API_KEY_REVIEWBOT", "test")
os.environ.setdefault("OPENAI_MODEL", "gpt-4o-mini")

import pytest
from fastapi.testclient import TestClient
import web.app as app_module
from web.app import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def patch_files(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "QUEUE_FILE", tmp_path / "queue.json")
    monkeypatch.setattr(app_module, "LOG_FILE", tmp_path / "approved_log.json")
    monkeypatch.setattr(app_module, "FEEDBACK_FILE", tmp_path / "feedback.json")
    yield


def test_index_empty_queue():
    response = client.get("/")
    assert response.status_code == 200


def test_index_platform_filter():
    response = client.get("/?platform=wb")
    assert response.status_code == 200


def test_reject_empty_queue():
    response = client.post("/reject", data={"index": "0"}, follow_redirects=False)
    assert response.status_code == 303


def test_approve_empty_queue():
    response = client.post(
        "/approve",
        data={"index": "0", "edited_response": "Спасибо за отзыв!"},
        follow_redirects=False,
    )
    assert response.status_code == 303


def test_api_feedback_save():
    payload = {
        "reviewText": "Отличный товар",
        "response": "Спасибо!",
        "stars": 5,
        "rating": 5,
    }
    response = client.post("/api/feedback", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["total"] == 1


def test_api_feedback_save_multiple():
    for i in range(3):
        client.post("/api/feedback", json={"reviewText": f"Отзыв {i}", "response": "Ответ", "stars": 4})
    response = client.get("/api/feedback/stats")
    data = response.json()
    assert data["total"] == 3


def test_api_feedback_stats_empty():
    response = client.get("/api/feedback/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["total"] == 0
    assert data["avg_rating"] is None


def test_api_feedback_stats_with_rating():
    client.post("/api/feedback", json={"reviewText": "Хорошо", "response": "Спасибо", "stars": 5, "rating": 5})
    response = client.get("/api/feedback/stats")
    data = response.json()
    assert data["avg_rating"] == 5.0


def test_api_wb_send_missing_params():
    response = client.post("/api/wb/send", json={})
    assert response.status_code == 400


def test_api_wb_send_text_too_long():
    response = client.post("/api/wb/send", json={"feedback_id": "1", "text": "x" * 1001})
    assert response.status_code == 400


def test_api_ozon_send_missing_params():
    response = client.post("/api/ozon/send", json={})
    assert response.status_code == 400


def test_api_wb_check_token_error():
    from unittest.mock import patch
    with patch("connectors.wb_connector.requests.get", side_effect=Exception("connection error")):
        response = client.get("/api/wb/check-token")
    assert response.status_code == 500
    assert response.json()["ok"] is False


def test_api_ozon_check_token_error():
    from unittest.mock import patch
    with patch("connectors.ozon_connector.requests.post", side_effect=Exception("connection error")):
        response = client.get("/api/ozon/check-token")
    assert response.status_code == 500
    assert response.json()["ok"] is False
