from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

_APP_DIR  = Path(__file__).resolve().parent
_BOT_DIR  = _APP_DIR.parent
_DATA_DIR = _BOT_DIR

QUEUE_FILE    = _DATA_DIR / "queue.json"
LOG_FILE      = _DATA_DIR / "approved_log.json"
FEEDBACK_FILE = _DATA_DIR / "wb_feedback_history.json"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "null",  # file:// protocol sends Origin: null
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

templates = Jinja2Templates(directory=str(_APP_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(_APP_DIR / "static")), name="static")

SIGNATURE = "\n\nС уважением,\nкоманда Arols"

sys.path.insert(0, str(_BOT_DIR))


def load_queue():
    if not QUEUE_FILE.exists():
        return []
    try:
        return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_queue(queue):
    QUEUE_FILE.write_text(
        json.dumps(queue, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def load_feedback_history():
    if not FEEDBACK_FILE.exists():
        return []
    try:
        return json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_feedback_history(data):
    FEEDBACK_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def log_approved(item, final_response):
    log_entry = {
        "timestamp":      datetime.now().isoformat(),
        "review":         item.get("review"),
        "final_response": final_response,
    }
    logs = []
    if LOG_FILE.exists():
        try:
            logs = json.loads(LOG_FILE.read_text(encoding="utf-8"))
        except Exception:
            logs = []
    logs.append(log_entry)
    LOG_FILE.write_text(
        json.dumps(logs, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def append_signature(text: str, signature: str) -> str:
    # Strip any signature the model might have added anyway
    text = re.sub(
        r'\s*(С уважением|Искренне ваш[а]?|Команда\s+\S+)[^\n]*$',
        '', text, flags=re.IGNORECASE
    ).rstrip()
    return text + "\n" + signature


def build_review_text(review: dict) -> str:
    parts = []
    if review.get("pros"):    parts.append(f"Достоинства: {review['pros']}")
    if review.get("cons"):    parts.append(f"Недостатки: {review['cons']}")
    if review.get("comment"): parts.append(f"Комментарий: {review['comment']}")
    return "\n".join(parts)


def extract_first_name(full_name: str) -> str:
    if not full_name or not full_name.strip():
        return ""
    parts = full_name.strip().split()
    first = parts[0]
    if re.match(r'^[А-ЯЁA-Z][а-яёa-z]{1,14}$', first):
        return first
    return ""


def build_system_prompt(settings: dict, feedback_history: list) -> str:
    good = [f for f in feedback_history if f.get("rating", 0) >= 4][-6:]
    bad  = [f for f in feedback_history if f.get("rating", 0) <= 2 and f.get("note")][-4:]

    tone_map = {
        "formal":   "официальный и вежливый, на «вы», без эмодзи",
        "friendly": "тёплый и дружелюбный, допустимы эмодзи (1-2 шт.)",
        "neutral":  "нейтральный деловой, без лишних эмоций",
    }
    len_map = {
        "short":  "до 200 символов — 2-3 предложения",
        "medium": "200-500 символов — 3-5 предложений",
        "long":   "500-900 символов — развёрнуто",
    }

    brand  = settings.get("brandName", "Наш бренд")
    tone   = tone_map.get(settings.get("tone", "friendly"), tone_map["friendly"])
    length = len_map.get(settings.get("responseLength", "medium"), len_map["medium"])
    sign   = settings.get("signature") or f"Команда {brand}"
    extra  = settings.get("customInstructions", "")

    p = f"""Ты — специалист по работе с клиентами на маркетплейсе Wildberries. Пишешь ответы на отзывы покупателей от лица бренда.

ПАРАМЕТРЫ БРЕНДА:
- Бренд: «{brand}»
- Тон: {tone}
- Длина: {length}
{f'- Инструкции: {extra}' if extra else ''}

ПРАВИЛА:
1. ВСЕГДА органично упоминай название товара в тексте ответа
2. Если известно имя покупателя — обращайсь по имени в начале. Если имя неизвестно (пусто) — НЕ используй никакого обращения, начинай ответ сразу по сути.
3. Только русский язык
4. Максимум 900 символов (подпись добавится автоматически)
5. Негатив (1-2★): признай проблему, извинись, предложи написать в ЛС для решения
6. Позитив (4-5★): поблагодари, выдели конкретную деталь из отзыва
7. Нейтраль (3★): поблагодари за честную оценку, ответь на конкретное замечание
8. Не копируй фразы из отзыва дословно
9. Не используй штампы: «Спасибо за обратную связь», «Будем рады видеть вас снова»
10. НЕ добавляй подпись («С уважением», «Команда» и т.п.) — она будет добавлена автоматически

СТРУКТУРА: [Имя + приветствие] → [Суть с названием товара] → [Конкретный шаг]"""

    if good:
        p += "\n\nПРИМЕРЫ ОДОБРЕННЫХ ОТВЕТОВ (воспроизводи стиль):"
        for i, ex in enumerate(good, 1):
            p += f"\n\n[{i}] Отзыв ({ex.get('stars')}★): \"{str(ex.get('reviewText',''))[:120]}\"\nОтвет: \"{ex.get('response')}\""

    if bad:
        p += "\n\nЧЕГО СТРОГО ИЗБЕГАТЬ:"
        for ex in bad:
            p += f"\n- {ex.get('note')}"

    p += "\n\nОтвечай ТОЛЬКО текстом ответа, без кавычек и пояснений."
    return p


@app.get("/")
def index(request: Request, platform: str = None):
    queue = load_queue()
    safe_queue = [item for item in queue if isinstance(item, dict) and "review" in item]
    if platform in ["wb", "ozon"]:
        filtered = [item for item in safe_queue if item["review"].get("platform") == platform]
    else:
        filtered = safe_queue
    return templates.TemplateResponse("queue.html", {
        "request": request,
        "queue": filtered,
        "active_platform": platform,
    })


@app.post("/approve")
def approve(index: int = Form(...), edited_response: str = Form(...)):
    queue = load_queue()
    if index < 0 or index >= len(queue):
        return RedirectResponse("/", status_code=303)
    item = queue.pop(index)
    final_response = edited_response.strip()
    if SIGNATURE.strip() not in final_response:
        final_response += SIGNATURE
    log_approved(item, final_response)
    save_queue(queue)
    return RedirectResponse("/", status_code=303)


@app.post("/reject")
def reject(index: int = Form(...)):
    queue = load_queue()
    if index < 0 or index >= len(queue):
        return RedirectResponse("/", status_code=303)
    queue.pop(index)
    save_queue(queue)
    return RedirectResponse("/", status_code=303)


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(str(_APP_DIR / "static" / "favicon.ico"))


@app.get("/api/wb/check-token")
def api_check_token():
    try:
        from connectors.wb_connector import check_token
        return JSONResponse(check_token())
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@app.get("/api/wb/reviews")
def api_get_reviews(take: int = 100, skip: int = 0):
    try:
        from connectors.wb_connector import get_unanswered_feedbacks
        reviews = get_unanswered_feedbacks(take=take, skip=skip)
        return JSONResponse({"ok": True, "reviews": reviews, "count": len(reviews)})
    except Exception as e:
        msg = str(e)
        if "401" in msg:
            return JSONResponse({"ok": False, "error": "WB токен недействителен"}, status_code=401)
        if "403" in msg:
            return JSONResponse({"ok": False, "error": "Нет доступа к WB Feedbacks API"}, status_code=403)
        return JSONResponse({"ok": False, "error": msg}, status_code=502)


@app.post("/api/wb/send")
async def api_send_reply(request: Request):
    body = await request.json()
    feedback_id = body.get("feedback_id")
    text = body.get("text", "").strip()

    if not feedback_id or not text:
        return JSONResponse({"ok": False, "error": "feedback_id и text обязательны"}, status_code=400)
    if len(text) > 1000:
        return JSONResponse({"ok": False, "error": f"Текст превышает 1000 символов ({len(text)})"}, status_code=400)

    try:
        from connectors.wb_connector import send_reply
        send_reply(feedback_id, text)
        return JSONResponse({"ok": True})
    except Exception as e:
        msg = str(e)
        if "401" in msg:
            return JSONResponse({"ok": False, "error": "WB токен недействителен"}, status_code=401)
        return JSONResponse({"ok": False, "error": msg}, status_code=502)


@app.post("/api/generate")
async def api_generate(request: Request):
    body = await request.json()
    review   = body.get("review", {})
    settings = body.get("settings", {})

    review_text      = build_review_text(review)
    first_name       = extract_first_name(review.get("author", ""))
    feedback_history = load_feedback_history()
    system_prompt    = build_system_prompt(settings, feedback_history)
    user_prompt = (
        f"Товар: «{review.get('productName', '—')}» (арт. {review.get('article', '—')})\n"
        f"Оценка: {review.get('stars', 0)} из 5★\n"
        f"Имя покупателя: {review.get('author', '—')} → обращайсь: «{first_name or 'без обращения'}»\n"
        f"{review_text}"
    )

    provider  = settings.get("provider", "openai")
    model     = settings.get("model", "")
    brand     = settings.get("brandName", "бренда")
    signature = (settings.get("signature") or f"Команда {brand}").strip()

    try:
        if provider == "gemini":
            from openai import OpenAI
            client = OpenAI(
                api_key=os.getenv("GOOGLE_API_KEY_REVIEWBOT"),
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            )
            resp = client.chat.completions.create(
                model=model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
                max_tokens=500,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
            )
            text = resp.choices[0].message.content.strip()

        elif provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY_REVIEWBOT"))
            resp = client.messages.create(
                model=model or os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
                max_tokens=500,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            text = resp.content[0].text.strip()

        else:  # openai (default)
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_REVIEWBOT"))
            resp = client.chat.completions.create(
                model=model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                max_tokens=500,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
            )
            text = resp.choices[0].message.content.strip()

        text = append_signature(text, signature)
        return JSONResponse({"ok": True, "text": text})

    except Exception as e:
        msg = str(e)
        if "401" in msg or "Incorrect API key" in msg or "invalid_api_key" in msg:
            return JSONResponse({"ok": False, "error": f"Неверный API-ключ ({provider})"}, status_code=401)
        if "insufficient_quota" in msg:
            return JSONResponse({"ok": False, "error": "Недостаточно средств на счёте"}, status_code=402)
        return JSONResponse({"ok": False, "error": msg}, status_code=500)


@app.post("/api/feedback")
async def api_save_feedback(request: Request):
    body = await request.json()
    history = load_feedback_history()
    history.append({
        "id":         int(datetime.now().timestamp() * 1000),
        "reviewText": body.get("reviewText", ""),
        "response":   body.get("response", ""),
        "stars":      body.get("stars", 0),
        "rating":     body.get("rating"),
        "note":       body.get("note"),
        "ts":         datetime.now().isoformat(),
    })
    if len(history) > 200:
        history = history[-200:]
    save_feedback_history(history)
    return JSONResponse({"ok": True, "total": len(history)})


@app.get("/api/ozon/check-token")
def api_ozon_check_token():
    try:
        from connectors.ozon_connector import check_token
        return JSONResponse(check_token())
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@app.get("/api/ozon/reviews")
def api_ozon_get_reviews(take: int = 100, skip: int = 0):
    try:
        from connectors.ozon_connector import get_unanswered_feedbacks
        reviews = get_unanswered_feedbacks(take=take, skip=skip)
        return JSONResponse({"ok": True, "reviews": reviews, "count": len(reviews)})
    except Exception as e:
        msg = str(e)
        return JSONResponse({"ok": False, "error": msg}, status_code=502)


@app.post("/api/ozon/send")
async def api_ozon_send_reply(request: Request):
    body = await request.json()
    feedback_id = body.get("feedback_id")
    text = body.get("text", "").strip()

    if not feedback_id or not text:
        return JSONResponse({"ok": False, "error": "feedback_id и text обязательны"}, status_code=400)

    try:
        from connectors.ozon_connector import send_reply
        send_reply(feedback_id, text)
        return JSONResponse({"ok": True})
    except Exception as e:
        msg = str(e)
        if "401" in msg:
            return JSONResponse({"ok": False, "error": "Ozon токен недействителен"}, status_code=401)
        return JSONResponse({"ok": False, "error": msg}, status_code=502)


@app.post("/regenerate")
def regenerate(index: int = Form(...)):
    queue = load_queue()
    if index < 0 or index >= len(queue):
        return RedirectResponse("/", status_code=303)

    item   = queue[index]
    review = item.get("review", {})
    first_name = extract_first_name(review.get("author", ""))
    feedback_history = load_feedback_history()

    default_settings = {"brandName": "Наш бренд", "tone": "friendly", "responseLength": "medium", "signature": ""}
    system_prompt = build_system_prompt(default_settings, feedback_history)
    user_prompt = (
        f"Товар: «{review.get('productName', '—')}» (арт. {review.get('article', '—')})\n"
        f"Оценка: {review.get('stars', 0)} из 5★\n"
        f"Имя покупателя: {review.get('author', '—')} → обращайся: «{first_name}»\n"
        f"{build_review_text(review)}"
    )

    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_REVIEWBOT"))
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            max_tokens=500,
            temperature=0.7,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
        )
        queue[index]["response"] = resp.choices[0].message.content.strip()
        save_queue(queue)
    except Exception:
        pass

    return RedirectResponse("/", status_code=303)


@app.get("/api/feedback/stats")
def api_feedback_stats():
    history = load_feedback_history()
    if not history:
        return JSONResponse({"ok": True, "total": 0, "avg_rating": None})
    rated = [f for f in history if f.get("rating")]
    avg = round(sum(f["rating"] for f in rated) / len(rated), 1) if rated else None
    return JSONResponse({"ok": True, "total": len(history), "rated": len(rated), "avg_rating": avg})
