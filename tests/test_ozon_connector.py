import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock
import pytest
from connectors.ozon_connector import _fmt_date, get_unanswered_feedbacks, check_token


def test_fmt_date_valid():
    assert _fmt_date("2024-03-20T12:00:00Z") == "20.03.2024"


def test_fmt_date_empty():
    assert _fmt_date("") == ""


def test_fmt_date_invalid_returns_prefix():
    result = _fmt_date("2024-13-45")
    assert result == "2024-13-45"


@patch("connectors.ozon_connector.requests.post")
def test_get_unanswered_feedbacks_empty(mock_post):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"reviews": []}
    mock_post.return_value = mock_resp

    with patch.dict(os.environ, {"OZON_CLIENT_ID": "123", "OZON_API_KEY": "key"}):
        result = get_unanswered_feedbacks()

    assert result == []


@patch("connectors.ozon_connector.requests.post")
def test_get_unanswered_feedbacks_with_reviews(mock_post):
    def side_effect(url, *args, **kwargs):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.ok = True
        if "review/list" in url:
            resp.json.return_value = {
                "reviews": [
                    {
                        "id": "rev-1",
                        "rating": 4,
                        "text": "Хороший товар",
                        "sku": "99999",
                        "published_at": "2024-02-01T00:00:00Z",
                        "photos": [],
                        "videos": [],
                    }
                ]
            }
        elif "product/info" in url:
            resp.json.return_value = {"items": []}
        return resp

    mock_post.side_effect = side_effect

    with patch.dict(os.environ, {"OZON_CLIENT_ID": "123", "OZON_API_KEY": "key"}):
        result = get_unanswered_feedbacks()

    assert len(result) == 1
    assert result[0]["id"] == "rev-1"
    assert result[0]["platform"] == "ozon"
    assert result[0]["stars"] == 4


@patch("connectors.ozon_connector.requests.post")
def test_get_unanswered_feedbacks_skips_empty_text(mock_post):
    def side_effect(url, *args, **kwargs):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.ok = True
        if "review/list" in url:
            resp.json.return_value = {
                "reviews": [
                    {
                        "id": "rev-empty",
                        "rating": 3,
                        "text": "",
                        "sku": "11111",
                        "published_at": "",
                        "photos": [],
                        "videos": [],
                    }
                ]
            }
        elif "product/info" in url:
            resp.json.return_value = {"items": []}
        return resp

    mock_post.side_effect = side_effect

    with patch.dict(os.environ, {"OZON_CLIENT_ID": "123", "OZON_API_KEY": "key"}):
        result = get_unanswered_feedbacks()

    assert result == []


@patch("connectors.ozon_connector.requests.post")
def test_check_token_ok(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"reviews": []}
    mock_post.return_value = mock_resp

    with patch.dict(os.environ, {"OZON_CLIENT_ID": "123", "OZON_API_KEY": "key"}):
        result = check_token()

    assert result["ok"] is True


@patch("connectors.ozon_connector.requests.post")
def test_check_token_unauthorized(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_post.return_value = mock_resp

    with patch.dict(os.environ, {"OZON_CLIENT_ID": "123", "OZON_API_KEY": "key"}):
        result = check_token()

    assert result["ok"] is False
    assert "401" in result["error"]


@patch("connectors.ozon_connector.requests.post")
def test_check_token_forbidden(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_post.return_value = mock_resp

    with patch.dict(os.environ, {"OZON_CLIENT_ID": "123", "OZON_API_KEY": "key"}):
        result = check_token()

    assert result["ok"] is False
    assert "403" in result["error"]
