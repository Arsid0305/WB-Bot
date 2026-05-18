# connectors/wb_connector.py
import os
import requests
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception


def _is_transient(exc: BaseException) -> bool:
    if isinstance(exc, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
        return True
    if isinstance(exc, requests.exceptions.HTTPError):
        return exc.response is not None and exc.response.status_code in (429, 500, 502, 503, 504)
    return False


_retry = retry(
    retry=retry_if_exception(_is_transient),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=16),
    reraise=True,
)

BASE_URL = "https://feedbacks-api.wildberries.ru"


def _headers():
    token = os.getenv("WB_TOKEN", "").strip()
    if not token.startswith("Bearer "):
        token = f"Bearer {token}"
    return {"Authorization": token, "Content-Type": "application/json"}


def _fmt_date(iso: str) -> str:
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y")
    except Exception:
        return iso[:10]


def _parse_bables(fb: dict) -> str:
    tags = fb.get("bables") or []
    names = [t if isinstance(t, str) else t.get("name", "") for t in tags]
    return ", ".join(n for n in names if n)


@_retry
def get_unanswered_feedbacks(take: int = 100, skip: int = 0) -> list[dict]:
    resp = requests.get(
        f"{BASE_URL}/api/v1/feedbacks",
        headers=_headers(),
        params={"isAnswered": "false", "take": take, "skip": skip, "order": "dateDesc"},
        timeout=30,
    )
    resp.raise_for_status()
    feedbacks = resp.json().get("data", {}).get("feedbacks", [])

    result = []
    for fb in feedbacks:
        pros    = (fb.get("pros")  or "").strip()
        cons    = (fb.get("cons")  or "").strip()
        comment = (fb.get("text")  or "").strip()
        tags    = _parse_bables(fb)

        if not pros and tags:
            pros = tags

        if not pros and not cons and not comment:
            continue

        # Фото
        photo_links = fb.get("photoLinks") or []
        photos = [p.get("fullSize") or p.get("miniSize") or p
                  for p in photo_links
                  if isinstance(p, (dict, str))]
        photos = [p for p in photos if p and isinstance(p, str)]

        # Видео
        video = fb.get("video") or {}
        video_url = ""
        if isinstance(video, dict):
            video_url = video.get("url") or video.get("link") or ""
        elif isinstance(video, str):
            video_url = video

        details = fb.get("productDetails", {})

        result.append({
            "id":              fb.get("id", ""),
            "productName":     details.get("productName", "Товар"),
            "article":         str(details.get("nmId", "—")),
            "supplierArticle": details.get("supplierArticle", "—"),
            "color":           fb.get("color") or details.get("color", ""),
            "size":            details.get("size", ""),
            "author":          (fb.get("userName") or "").strip(),
            "stars":           fb.get("productValuation", 0),
            "pros":            pros,
            "cons":            cons,
            "comment":         comment,
            "date":            _fmt_date(fb.get("createdDate", "")),
            "orderDate":       _fmt_date(fb.get("lastOrderCreatedAt", "")),
            "photos":          photos,
            "videoUrl":        video_url,
            "status":          "pending",
            "platform":        "wb",
        })

    return result


@_retry
def send_reply(feedback_id: str, text: str) -> bool:
    resp = requests.patch(
        f"{BASE_URL}/api/v1/feedbacks/answer",
        headers=_headers(),
        json={"id": feedback_id, "text": text},
        timeout=30,
    )
    resp.raise_for_status()
    return True


def check_token() -> dict:
    try:
        resp = requests.get(
            f"{BASE_URL}/api/v1/feedbacks",
            headers=_headers(),
            params={"isAnswered": "false", "take": 1, "skip": 0},
            timeout=10,
        )
        if resp.status_code == 401:
            return {"ok": False, "error": "Токен недействителен (401)"}
        if resp.status_code == 403:
            return {"ok": False, "error": "Нет доступа к Feedbacks API (403)"}
        resp.raise_for_status()
        return {"ok": True}
    except requests.RequestException as e:
        return {"ok": False, "error": str(e)}
