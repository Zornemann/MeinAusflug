import json
import os
from typing import Iterable

import requests

try:
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account
except Exception:
    Request = None
    service_account = None


FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"


def _load_service_account_info() -> dict | None:
    raw = os.getenv("FIREBASE_SERVICE_ACCOUNT", "").strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _get_project_id() -> str | None:
    service_account_info = _load_service_account_info()
    if not service_account_info:
        return None
    return service_account_info.get("project_id")


def _get_access_token() -> str | None:
    if service_account is None or Request is None:
        return None

    service_account_info = _load_service_account_info()
    if not service_account_info:
        return None

    try:
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=[FCM_SCOPE],
        )
        credentials.refresh(Request())
        return credentials.token
    except Exception:
        return None


def _normalize_tokens(tokens: Iterable[str] | None) -> list[str]:
    if not tokens:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        token = (token or "").strip()
        if token and token not in seen:
            seen.add(token)
            out.append(token)
    return out


def send_push(tokens: Iterable[str] | None, title: str, body: str, data: dict | None = None) -> dict:
    """
    Send a push notification via Firebase Cloud Messaging HTTP v1.

    Returns a small summary dict for logging/debugging.
    Falls Firebase/Google Auth noch nicht korrekt eingerichtet ist,
    wird still nichts gesendet statt die ganze App abstürzen zu lassen.
    """
    normalized_tokens = _normalize_tokens(tokens)
    if not normalized_tokens:
        return {"sent": 0, "errors": []}

    access_token = _get_access_token()
    project_id = _get_project_id()

    if not access_token or not project_id:
        return {
            "sent": 0,
            "errors": [{"error": "Push not configured: missing google-auth, FIREBASE_SERVICE_ACCOUNT, or project_id"}],
        }

    url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }

    errors: list[dict] = []
    sent = 0

    for token in normalized_tokens:
        payload = {
            "message": {
                "token": token,
                "notification": {
                    "title": title,
                    "body": body,
                },
                "android": {
                    "priority": "high",
                    "notification": {
                        "channel_id": "default",
                        "sound": "default",
                    },
                },
            }
        }

        if data:
            payload["message"]["data"] = {str(k): str(v) for k, v in data.items()}

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            if 200 <= resp.status_code < 300:
                sent += 1
            else:
                errors.append(
                    {
                        "token": token,
                        "status_code": resp.status_code,
                        "response": resp.text[:1000],
                    }
                )
        except Exception as exc:
            errors.append({"token": token, "error": str(exc)})

    return {"sent": sent, "errors": errors}