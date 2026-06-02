import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


class GmailIntegrationError(Exception):
    pass


@dataclass(frozen=True)
class GmailMessage:
    message_id: str
    subject: str
    sender: str
    date: str
    snippet: str


class GmailService:
    _BASE_URL = "https://gmail.googleapis.com/gmail/v1/users/me"
    _TOKEN_URL = "https://oauth2.googleapis.com/token"

    @staticmethod
    def fetch_messages(access_token: str, max_results: int = 10) -> list[GmailMessage]:
        """Читает входящие из Gmail API. Возвращает список GmailMessage."""
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        list_url = (
            f"{GmailService._BASE_URL}/messages"
            f"?maxResults={max_results}&labelIds=INBOX"
        )
        req = urllib.request.Request(list_url, headers=auth_headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 401:
                raise GmailIntegrationError("Токен доступа истёк или недействителен.")
            raise GmailIntegrationError(f"Ошибка Gmail API при получении списка: {e.code}")
        except Exception as e:
            raise GmailIntegrationError(f"Ошибка соединения с Gmail API: {e}")

        messages_raw = data.get("messages", [])
        if not messages_raw:
            return []

        result = []
        for msg in messages_raw:
            msg_id = msg["id"]
            detail_url = (
                f"{GmailService._BASE_URL}/messages/{msg_id}"
                "?format=metadata"
                "&metadataHeaders=Subject"
                "&metadataHeaders=From"
                "&metadataHeaders=Date"
            )
            req = urllib.request.Request(detail_url, headers=auth_headers)
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    msg_data = json.loads(resp.read().decode())
            except Exception:
                continue

            header_list = msg_data.get("payload", {}).get("headers", [])
            hmap = {h["name"]: h["value"] for h in header_list}
            result.append(GmailMessage(
                message_id=msg_id,
                subject=hmap.get("Subject", "(без темы)"),
                sender=hmap.get("From", "(неизвестно)"),
                date=hmap.get("Date", ""),
                snippet=msg_data.get("snippet", ""),
            ))

        return result

    @staticmethod
    def refresh_access_token(refresh_token: str, client_id: str, client_secret: str) -> dict:
        """Обменивает refresh_token на новый access_token."""
        body = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }).encode()
        req = urllib.request.Request(
            GmailService._TOKEN_URL,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            raise GmailIntegrationError(f"Ошибка обновления токена: {e.code}")
        except Exception as e:
            raise GmailIntegrationError(f"Ошибка соединения при обновлении токена: {e}")


# ── Filter ────────────────────────────────────────────────────────────────────

class GmailFilter:
    # Письма с этих доменов считаются важными
    _IMPORTANT_DOMAINS = frozenset({"nsu.ru", "fit.nsu.ru", "edu.nsu.ru", "lab.nsu.ru"})

    @staticmethod
    def _sender_domain(sender: str) -> str:
        """Извлекает домен из строки отправителя вида 'Имя <email@domain>' или 'email@domain'."""
        match = re.search(r"<([^>]+)>", sender)
        email = match.group(1) if match else sender.strip()
        return email.split("@")[-1].lower() if "@" in email else ""

    @classmethod
    def is_important(cls, msg: GmailMessage) -> bool:
        """True если отправитель входит в список важных доменов."""
        return cls._sender_domain(msg.sender) in cls._IMPORTANT_DOMAINS

    @classmethod
    def filter_important(cls, messages: list[GmailMessage]) -> list[GmailMessage]:
        """Оставляет только письма от важных отправителей."""
        return [msg for msg in messages if cls.is_important(msg)]
