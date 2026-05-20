# Project Context

> WB-Bot — бот для автоматического ответа на отзывы WB и Ozon через AI провайдеров.

---

## 1. Tech Stack
- Frontend: статический HTML (`wb-reviewbot-v3.html`) — без фреймворков
- Animations: none
- Backend: Python 3 + FastAPI (`web/app.py`)
- DB & Auth: none
- AI провайдеры: openai, anthropic, gemini, deepseek — SSOT: `web/app.py:api_generate()`
- Коннекторы: `connectors/wb_connector.py` (Wildberries), `connectors/ozon_connector.py` (Ozon)

---

## 2. Infrastructure & CI/CD
- Frontend deploy: none (статический HTML, открывается локально)
- Repo: github.com/Arsid0305/WB-Bot

Workflows:
- `automerge.yml` — `claude/** | cursor/**` → `main` авто ✅
- `promote.yml` — не используется ❌
- `deploy.yml` — не используется ❌

---

## 3. AI Environment

| Tool | Status | Note |
|------|--------|------|
| Node.js / npm | ❌ | не используется |
| Python | ✅ | 3.x, зависимости в `requirements.txt` |
| Supabase CLI | ❌ | нет |
| .env (real keys) | ✅ | API ключи провайдеров + WB/Ozon токены |

---

## 4. Design System

Не используется. Весь UI — в `wb-reviewbot-v3.html`.

---

## 5. Project Structure

```
.github/workflows/
  automerge.yml        — авто-мерж ветки в main
connectors/
  wb_connector.py      — Wildberries API
  ozon_connector.py    — Ozon API
docs/
  AUDIT_PROMPT.md      — контекст для аудита
scripts/
  check_consistency.py — CI-проверки консистентности
tasks/
  todo.md              — активные задачи
  lessons.md           — уроки из ошибок
web/
  app.py               — FastAPI приложение, SSOT провайдеров
wb-reviewbot-v3.html   — основной UI
requirements.txt
.env.example
```

---

## 6. Standard Packages

**Python:**
- `fastapi` — веб-фреймворк
- `uvicorn` — ASGI сервер
- `openai` — OpenAI SDK
- `anthropic` — Anthropic SDK
- `google-generativeai` — Gemini SDK
- `httpx` — HTTP клиент

---

## 7. Auth (Supabase OTP)

Не используется — нет Supabase.

---

## 8. Open Bugs

_(empty)_
