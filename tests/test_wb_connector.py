import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock
import pytest
from connectors.wb_connector import _fmt_date, _parse_bables, get_unanswered_feedbacks, check_token


def test_fmt_date_valid():
    assert _fmt_date("2024-01-15T10:30:00Z") == "15.01.2024"


def test_fmt_date_empty():
    assert _fmt_date("") == ""


def test_fmt_date_invalid_returns_prefix():
    result = _fmt_date("not-a-date")
    assert result == "not-a-date"


def test_parse_bables_strings():
    fb = {"bables": ["Хорошее качество", "Быстрая доставка"]}
    result = _parse_bables(fb)
    assert result == "Хорошее качество, Быстрая доставка"


def test_parse_bables_dicts():
    fb = {"bables": [{"name": "Качество"}, {"name": ""}]}
    result = _parse_bables(fb)
    assert result == "Качество"


def test_parse_bables_empty():
    assert _parse_bables({}) == ""


def test_parse_bables_none():
    assert _parse_bables({"bables": None}) == ""


@patch("connectors.wb_connector.requests.get")
def test_get_unanswered_feedbacks_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "data": {
            "feedbacks": [
                {
                    "id": "fb-1",
                    "productValuation": 5,
                    "pros": "Отличный товар",
                    "cons": "",
                    "text": "",
                    "userName": "Иван",
                    "createdDate": "2024-01-01T00:00:00Z",
                    "productDetails": {"productName": "Футболка", "nmId": 12345},
                }
            ]
        }
    }
    mock_get.return_value = mock_resp

    with patch.dict(os.environ, {"WB_TOKEN": "test_token"}):
        result = get_unanswered_feedbacks()

    assert len(result) == 1
    assert result[0]["id"] == "fb-1"
    assert result[0]["stars"] == 5
    assert result[0]["platform"] == "wb"
    assert result[0]["productName"] == "Футболка"


@patch("connectors.wb_connector.requests.get")
def test_get_unanswered_feedbacks_skips_empty(mock_get):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "data": {
            "feedbacks": [
                {
                    "id": "fb-empty",
                    "productValuation": 3,
                    "pros": "",
                    "cons": "",
                    "text": "",
                    "productDetails": {},
                }
            ]
        }
    }
    mock_get.return_value = mock_resp

    with patch.dict(os.environ, {"WB_TOKEN": "test_token"}):
        result = get_unanswered_feedbacks()

    assert result == []


@patch("connectors.wb_connector.requests.get")
def test_get_unanswered_feedbacks_empty_list(mock_get):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"data": {"feedbacks": []}}
    mock_get.return_value = mock_resp

    with patch.dict(os.environ, {"WB_TOKEN": "test_token"}):
        result = get_unanswered_feedbacks()

    assert result == []


@patch("connectors.wb_connector.requests.get")
def test_check_token_ok(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"data": {"feedbacks": []}}
    mock_get.return_value = mock_resp

    with patch.dict(os.environ, {"WB_TOKEN": "valid_token"}):
        result = check_token()

    assert result["ok"] is True


@patch("connectors.wb_connector.requests.get")
def test_check_token_unauthorized(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_get.return_value = mock_resp

    with patch.dict(os.environ, {"WB_TOKEN": "bad_token"}):
        result = check_token()

    assert result["ok"] is False
    assert "401" in result["error"]


@patch("connectors.wb_connector.requests.get")
def test_check_token_forbidden(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_get.return_value = mock_resp

    with patch.dict(os.environ, {"WB_TOKEN": "bad_token"}):
        result = check_token()

    assert result["ok"] is False
    assert "403" in result["error"]
