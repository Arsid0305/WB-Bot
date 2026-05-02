# Контекст проекта для Claude — WB-Bot

## ⛔ ГЛАВНОЕ ПРАВИЛО

Никаких изменений без явного согласования с пользователем.
Заметил баг или улучшение — сообщи и жди разрешения. Не трогай.

**Claude вносит изменения ТОЛЬКО если:**
1. Пользователь явно описал задачу
2. Claude объяснил что именно будет менять
3. Пользователь подтвердил («делай», «да», «ок» или аналог)

**Запрещено:**
- Менять логику, которую не обсуждали
- «Заодно» исправлять что-то ещё
- Откатывать или переписывать ранее сделанное без явной просьбы
- Добавлять фичи, рефакторинг, «улучшения» по своей инициативе

> В конце каждого чата — обновлять раздел «Открытые баги».

---

## Инфраструктура

- Запуск: локально через `uvicorn` или Docker
- Репо: github.com/Arsid0305/WB-Bot
- Ветки: `main` (продакшн) → `dev` (интеграция) → `claude/*` (рабочие)
- CI: GitHub Actions — pytest на каждый push/PR в `main` и `dev`
- Автомерж: `dev → main` только после успешного CI

## Стек

- Python 3.11
- FastAPI + Uvicorn + Jinja2
- OpenAI API (генерация ответов)
- Wildberries Feedbacks API
- Ozon Seller API
- pytest + httpx (тесты)

## Структура проекта

```
WB-Bot/
├── web/
│   ├── app.py              # FastAPI приложение (API + UI)
│   ├── templates/queue.html
│   └── static/
├── connectors/
│   ├── wb_connector.py     # Wildberries Feedbacks API
│   └── ozon_connector.py   # Ozon Seller API
├── tests/
│   ├── test_wb_connector.py
│   ├── test_ozon_connector.py
│   ├── test_app_utils.py
│   └── test_api.py
├── .github/workflows/
│   ├── ci.yml
│   └── automerge.yml
├── requirements.txt
├── .env.example
├── Dockerfile
└── docker-compose.yml
```

Рантайм-файлы (`queue.json`, `approved_log.json`, `wb_feedback_history.json`) — в корне, не коммитятся.

## Переменные окружения

| Переменная | Описание |
|---|---|
| `WB_TOKEN` | Токен Wildberries API (без префикса Bearer) |
| `OZON_CLIENT_ID` | Client-ID Ozon Seller API |
| `OZON_API_KEY` | API-ключ Ozon Seller API |
| `OPENAI_API_KEY_REVIEWBOT` | OpenAI API ключ |
| `OPENAI_MODEL` | Модель OpenAI (по умолчанию `gpt-4o-mini`) |

## Среда Claude

- Python 3.11 — есть
- pip / venv — есть
- Docker — есть
- node_modules — не нужны
- Supabase CLI — не используется
- Установка зависимостей: `pip install -r requirements.txt`

## Рабочий процесс

1. Пользователь ставит задачу
2. Claude объясняет план (коротко: что меняет и где)
3. Пользователь говорит «делай»
4. Claude делает — строго то, что обговорили
5. Коммит + пуш в `claude/*` → PR в `dev`
6. CI прогоняет тесты → автомерж в `main`

## API endpoints

| Метод | Путь | Описание |
|---|---|---|
| GET | `/` | Очередь отзывов |
| GET | `/api/wb/reviews` | Неотвеченные отзывы WB |
| POST | `/api/wb/send` | Отправить ответ WB |
| GET | `/api/wb/check-token` | Проверить WB токен |
| GET | `/api/ozon/reviews` | Неотвеченные отзывы Ozon |
| POST | `/api/ozon/send` | Отправить ответ Ozon |
| GET | `/api/ozon/check-token` | Проверить Ozon токен |
| POST | `/api/generate` | Сгенерировать ответ (OpenAI) |
| POST | `/api/feedback` | Сохранить обратную связь |
| GET | `/api/feedback/stats` | Статистика обратной связи |
| POST | `/approve` | Одобрить и отправить ответ |
| POST | `/reject` | Отклонить отзыв |

## Запуск

```bash
# Локально
pip install -r requirements.txt
cp .env.example .env  # заполнить токены
uvicorn web.app:app --host 127.0.0.1 --port 8000

# Docker
docker-compose up -d

# Тесты
pytest tests/ -v
```

---

## Открытые баги

_(пусто)_
