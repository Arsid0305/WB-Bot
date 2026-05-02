import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("WB_TOKEN", "test")
os.environ.setdefault("OZON_CLIENT_ID", "test")
os.environ.setdefault("OZON_API_KEY", "test")
os.environ.setdefault("OPENAI_API_KEY_REVIEWBOT", "test")

from web.app import build_review_text, extract_first_name, build_system_prompt


def test_build_review_text_all_fields():
    review = {"pros": "Отлично", "cons": "Дорого", "comment": "Советую"}
    result = build_review_text(review)
    assert "Достоинства: Отлично" in result
    assert "Недостатки: Дорого" in result
    assert "Комментарий: Советую" in result


def test_build_review_text_empty():
    assert build_review_text({}) == ""


def test_build_review_text_partial():
    review = {"comment": "Хорошо"}
    result = build_review_text(review)
    assert "Комментарий: Хорошо" in result
    assert "Достоинства" not in result


def test_extract_first_name_cyrillic():
    assert extract_first_name("Иван Иванов") == "Иван"


def test_extract_first_name_empty():
    assert extract_first_name("") == "Покупатель"


def test_extract_first_name_none():
    assert extract_first_name(None) == "Покупатель"


def test_extract_first_name_lowercase():
    assert extract_first_name("ivan") == "Покупатель"


def test_extract_first_name_single_word():
    assert extract_first_name("Мария") == "Мария"


def test_build_system_prompt_contains_brand():
    settings = {"brandName": "TestBrand", "tone": "friendly", "responseLength": "medium"}
    result = build_system_prompt(settings, [])
    assert "TestBrand" in result


def test_build_system_prompt_custom_instructions():
    settings = {"brandName": "X", "customInstructions": "Упоминай скидки"}
    result = build_system_prompt(settings, [])
    assert "Упоминай скидки" in result


def test_build_system_prompt_tone_formal():
    settings = {"brandName": "X", "tone": "formal"}
    result = build_system_prompt(settings, [])
    assert "официальный" in result


def test_build_system_prompt_length_short():
    settings = {"brandName": "X", "responseLength": "short"}
    result = build_system_prompt(settings, [])
    assert "200 символов" in result


def test_build_system_prompt_with_good_history():
    settings = {"brandName": "Brand"}
    history = [
        {"rating": 5, "stars": 5, "reviewText": "Отлично!", "response": "Спасибо!"},
    ]
    result = build_system_prompt(settings, history)
    assert "ПРИМЕРЫ ОДОБРЕННЫХ ОТВЕТОВ" in result


def test_build_system_prompt_with_bad_history():
    settings = {"brandName": "Brand"}
    history = [
        {"rating": 1, "stars": 1, "reviewText": "Плохо", "response": "Извините", "note": "Не обещать возврат"},
    ]
    result = build_system_prompt(settings, history)
    assert "ЧЕГО СТРОГО ИЗБЕГАТЬ" in result
    assert "Не обещать возврат" in result
