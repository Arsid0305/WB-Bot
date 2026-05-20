# План: привести WB-Bot в соответствие со стандартами TEMPLATE

> BIG задача. Ждать «делай» перед выполнением каждого пункта.

---

## 1. Исправить `CLAUDE.md`

- [ ] 1.1 Заменить `Flask` → `FastAPI` в секции «Безопасность Flask» (заголовок + чеклист)
- [ ] 1.2 Исправить секцию «Инфраструктура»: стек `Python / FastAPI`, фронтенд `wb-reviewbot-v3.html` (статический HTML)
- [ ] 1.3 Исправить секцию «Рабочий процесс»: убрать `dev` + `promote.yml`, заменить на `claude/... → main` напрямую через `automerge.yml`
- [ ] 1.4 Добавить `cursor/**` в секцию «Правила Git»
- [ ] 1.5 Добавить список AI-провайдеров (`openai`, `anthropic`, `gemini`, `deepseek`) — для проверки `check_consistency.py`

## 2. Исправить `.github/workflows/automerge.yml`

- [ ] 2.1 Добавить `cursor/**` в список триггерных веток (рядом с `claude/**`)
- [ ] 2.2 Добавить conflict guard: проверять `git merge --no-commit --no-ff` перед реальным мержем — при конфликте падать с ошибкой, не зависать
- [ ] 2.3 Добавить шаг запуска `scripts/check_consistency.py` до шага merge

## 3. Добавить отсутствующие файлы

- [ ] 3.1 Создать `scripts/check_consistency.py` — CI-гейт, адаптированный для WB-Bot:
  - нет слова `Flask` в `CLAUDE.md`
  - нет `dev` и `promote.yml` в `CLAUDE.md`
  - `automerge.yml` содержит `claude/**` и `cursor/**` в allowlist
  - в `CLAUDE.md` присутствуют все четыре провайдера: `openai`, `anthropic`, `gemini`, `deepseek`
- [ ] 3.2 Создать `SYSTEM.md` — скопировать из TEMPLATE без изменений
- [ ] 3.3 Создать `docs/AUDIT_PROMPT.md` — скопировать из TEMPLATE без изменений

---

## Порядок выполнения

1 → 2 → 3 (последовательно, чтобы `check_consistency.py` проверял уже исправленный `CLAUDE.md`)
