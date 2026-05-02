# WB-Bot — ReviewBot

Бот для автоматической генерации ответов на отзывы покупателей на маркетплейсах Wildberries и Ozon с помощью OpenAI GPT и веб-интерфейса модерации.

## Структура проекта

```
WB-Bot/
├── web/
│   ├── app.py              # FastAPI приложение (API + UI)
│   ├── templates/
│   │   └── queue.html      # Jinja2 шаблон очереди отзывов
│   └── static/             # Статика (favicon, изображения)
├── connectors/
│   ├── wb_connector.py     # Коннектор Wildberries Feedbacks API
│   └── ozon_connector.py   # Коннектор Ozon Seller API
├── tests/
│   ├── test_wb_connector.py
│   ├── test_ozon_connector.py
│   ├── test_app_utils.py
│   └── test_api.py
├── .github/workflows/
│   ├── ci.yml              # CI: тесты на push/PR
│   └── automerge.yml       # Auto-merge dev→main после CI
├── requirements.txt
├── .env.example
├── Dockerfile
└── docker-compose.yml
```

Рантайм-файлы (`queue.json`, `approved_log.json`, `wb_feedback_history.json`) хранятся в корне проекта и не коммитятся.

## Переменные окружения

| Переменная | Описание |
|---|---|
| `WB_TOKEN` | Токен Wildberries API (без префикса Bearer) |
| `OZON_CLIENT_ID` | Client-ID Ozon Seller API |
| `OZON_API_KEY` | API-ключ Ozon Seller API |
| `OPENAI_API_KEY_REVIEWBOT` | OpenAI API ключ |
| `OPENAI_MODEL` | Модель OpenAI (по умолчанию `gpt-4o-mini`) |

## Запуск

### Локально (Python)
```bash
pip install -r requirements.txt
cp .env.example .env
# Заполни .env реальными токенами
uvicorn web.app:app --host 127.0.0.1 --port 8000
```

### Docker
```bash
cp .env.example .env
# Заполни .env реальными токенами
docker-compose up -d
```

## Тесты
```bash
pip install -r requirements.txt
pytest tests/ -v
```

## API endpoints

| Метод | Путь | Описание |
|---|---|---|
| GET | `/` | Главная страница (очередь отзывов) |
| GET | `/api/wb/reviews` | Получить неотвеченные отзывы WB |
| POST | `/api/wb/send` | Отправить ответ на отзыв WB |
| GET | `/api/wb/check-token` | Проверить WB токен |
| GET | `/api/ozon/reviews` | Получить неотвеченные отзывы Ozon |
| POST | `/api/ozon/send` | Отправить ответ на отзыв Ozon |
| GET | `/api/ozon/check-token` | Проверить Ozon токен |
| POST | `/api/generate` | Сгенерировать ответ через OpenAI |
| POST | `/api/feedback` | Сохранить обратную связь по ответу |
| GET | `/api/feedback/stats` | Статистика обратной связи |
| POST | `/approve` | Одобрить ответ (отправить на маркетплейс) |
| POST | `/reject` | Отклонить отзыв из очереди |

## Ветки

- `main` — продакшн
- `dev` — интеграционная ветка (вливается в main через CI)
- `claude/*` — рабочие ветки

## CI/CD

- `ci.yml` — запускает pytest на каждый push/PR в `main` и `dev`
- `automerge.yml` — автоматически вливает `dev` → `main` после успешного CI
