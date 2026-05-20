# План: привести WB-Bot в соответствие со стандартами TEMPLATE

> BIG задача. Ждать «делай» перед выполнением каждого пункта.

---

## 1. Исправить `CLAUDE.md`

- [x] 1.1 Заменить `Flask` → `FastAPI` в секции «Безопасность Flask» (заголовок + чеклист)
- [x] 1.2 Исправить секцию «Инфраструктура»: стек `Python / FastAPI`, фронтенд `wb-reviewbot-v3.html` (статический HTML)
- [x] 1.3 Исправить секцию «Рабочий процесс»: убрать `dev` + `promote.yml`, заменить на `claude/... → main` напрямую через `automerge.yml`
- [x] 1.4 Добавить `cursor/**` в секцию «Правила Git»
- [x] 1.5 Добавить список AI-провайдеров (`openai`, `anthropic`, `gemini`, `deepseek`) для проверки `check_consistency.py`

## 2. Исправить `.github/workflows/automerge.yml`

- [x] 2.1 Добавить `cursor/**` в список триггерных веток (рядом с `claude/**`)
- [x] 2.2 Добавить conflict guard: проверять `git merge --no-commit --no-ff` перед реальным мержем — при конфликте падать с ошибкой, не зависать
- [x] 2.3 Добавить шаг запуска `scripts/check_consistency.py` до шага merge

## 3. Добавить отсутствующие файлы

- [x] 3.1 Создать `scripts/check_consistency.py` — CI-гейт, адаптированный для WB-Bot (4 проверки из задания)
- [x] 3.2 Создать `SYSTEM.md` — скопировать из TEMPLATE без изменений
- [x] 3.3 Создать `docs/AUDIT_PROMPT.md` — скопировать из TEMPLATE без изменений

**Порядок:** 1 → 2 → 3 (последовательно, чтобы `check_consistency.py` проверял уже исправленный `CLAUDE.md`)

---

✅ Выполнено в рамках `claude/read-file-GESlc`
