#!/usr/bin/env python3
import asyncio
import base64
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from urllib.parse import urlparse

PHONE_RE = re.compile(r"(?:\+7|8|7)?[\s\-\(\)]*\d{3}[\s\-\(\)]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}")
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b", re.IGNORECASE)
TELEGRAM_RE = re.compile(r"(?:https?://t\.me/|t\.me/|(?<![A-Za-z0-9._%+\-])@)([A-Za-z0-9_]{5,32})")
VK_RE = re.compile(r"https?://(?:www\.)?vk\.com/[A-Za-z0-9_.]+", re.IGNORECASE)

INTENT_KEYWORDS = {
    "buy": ["куплю", "купим", "хочу купить", "ищу купить", "планирую купить", "приобрету", "приобретем"],
    "sell": ["продам", "продать", "продаю", "собственник продает"],
    "rent": [
        "сниму", "снимем", "арендую", "арендуем", "хочу снять", "ищу помещение",
        "ищем помещение", "нужен офис", "нужен склад", "нужно помещение",
        "требуется помещение", "ищу квартиру", "рассмотрю варианты",
    ],
    "lease_out": ["сдам", "сдается", "сдаётся", "сдаю", "аренда от собственника"],
    "invest": ["инвест", "доходность", "готовый арендный бизнес", "габ"],
}

DEMAND_KEYWORDS = [
    "куплю", "купим", "хочу купить", "ищу купить", "планирую купить", "приобрету",
    "сниму", "снимем", "арендую", "арендуем", "хочу снять", "ищу помещение",
    "ищем помещение", "ищу офис", "ищем офис", "ищу склад", "ищем склад",
    "ищу квартиру", "ищем квартиру", "нужен офис", "нужен склад", "нужно помещение",
    "требуется помещение", "требуется офис", "требуется склад", "подберу помещение",
    "подбираю помещение", "рассмотрю варианты",
]

SUPPLY_KEYWORDS = [
    "продам", "продаю", "продается", "продаётся", "сдам", "сдаю", "сдается", "сдаётся",
    "объект #", "#продажа", "#аренда", "цена:", "цена аренды", "₽/м", "руб/м",
    "от собственника", "риелторский", "готовый бизнес", "арендный бизнес",
]

SPAM_KEYWORDS = [
    "реклама", "smm", "предложить новость", "поддержка", "подпишитесь", "описание канала",
    "строим дома", "строительство", "монтаж отопления", "ставим все виды заборов",
    "кондиционер", "строительные услуги", "скидки", "консультация бесплатно",
    "ищем уборщика", "зарплата", "вакансия", "работа",
]

COMMERCIAL_KEYWORDS = [
    "коммерчес", "офис", "склад", "помещение", "ритейл", "магазин", "псн", "общепит",
    "кофей", "производство", "арендный бизнес", "габ", "торгов",
]

RESIDENTIAL_KEYWORDS = [
    "квартир", "дом", "таунхаус", "апартамент", "студ", "жк", "комнат",
]


@dataclass
class Config:
    api_id: int
    api_hash: str
    phone: str
    sources: list[str]
    supabase_url: str
    service_role_key: str
    dry_run: bool
    limit_per_source: int
    session_path: str
    proxy_url: Optional[str]
    bot_token: Optional[str]
    notify_chat_id: Optional[str]
    notify_max_per_run: int
    max_message_age_days: int


def get_config() -> Config:
    required = ["TELEGRAM_API_ID", "TELEGRAM_API_HASH", "TELEGRAM_PHONE", "SUPABASE_SERVICE_ROLE_KEY"]
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        raise SystemExit(f"Missing environment variables: {', '.join(missing)}")

    return Config(
        api_id=int(os.environ["TELEGRAM_API_ID"]),
        api_hash=os.environ["TELEGRAM_API_HASH"],
        phone=os.environ["TELEGRAM_PHONE"],
        sources=[item.strip() for item in os.environ.get("TELEGRAM_SOURCES", "").split(",") if item.strip()],
        supabase_url=os.environ.get("SUPABASE_URL", "http://kong:8000").rstrip("/"),
        service_role_key=os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        dry_run=os.environ.get("COLLECTOR_DRY_RUN", "true").lower() == "true",
        limit_per_source=int(os.environ.get("TELEGRAM_LIMIT_PER_SOURCE", "50")),
        session_path=os.environ.get("TELEGRAM_SESSION_PATH", "/data/novactiv-telegram"),
        proxy_url=os.environ.get("TELEGRAM_PROXY") or None,
        bot_token=os.environ.get("TELEGRAM_BOT_TOKEN") or None,
        notify_chat_id=os.environ.get("TELEGRAM_NOTIFY_CHAT_ID") or None,
        notify_max_per_run=int(os.environ.get("TELEGRAM_NOTIFY_MAX_PER_RUN", "5")),
        max_message_age_days=int(os.environ.get("TELEGRAM_MAX_MESSAGE_AGE_DAYS", "30")),
    )


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_recent_message(message_date: Optional[datetime], max_age_days: int) -> bool:
    if not message_date:
        return False
    if message_date.tzinfo is None:
        message_date = message_date.replace(tzinfo=timezone.utc)
    return message_date >= datetime.now(timezone.utc) - timedelta(days=max_age_days)


def normalize_phone(value: str) -> Optional[str]:
    digits = re.sub(r"\D+", "", value)
    if len(digits) == 11 and digits[0] in ("7", "8"):
        return "+7" + digits[1:]
    if len(digits) == 10:
        return "+7" + digits
    return None


def extract_contacts(text: str) -> dict[str, list[str]]:
    phones = sorted({phone for phone in (normalize_phone(m.group(0)) for m in PHONE_RE.finditer(text)) if phone})
    emails = sorted({m.group(0).strip().lower() for m in EMAIL_RE.finditer(text)})
    telegram = sorted({m.group(1).strip().lower() for m in TELEGRAM_RE.finditer(text)})
    vk = sorted({m.group(0).strip().rstrip("/").lower() for m in VK_RE.finditer(text)})
    return {"phones": phones, "emails": emails, "telegram_usernames": telegram, "vk_urls": vk}


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def detect_intent(text: str) -> str:
    low = text.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(keyword in low for keyword in keywords):
            return intent
    return "unknown"


def detect_segment(text: str) -> Optional[str]:
    low = text.lower()
    commercial = any(keyword in low for keyword in COMMERCIAL_KEYWORDS)
    residential = any(keyword in low for keyword in RESIDENTIAL_KEYWORDS)
    if commercial and residential:
        return "mixed"
    if commercial:
        return "commercial"
    if residential:
        return "residential"
    return None


def has_demand_intent(text: str) -> bool:
    low = text.lower()
    return any(keyword in low for keyword in DEMAND_KEYWORDS)


def is_noise_or_supply(text: str) -> bool:
    low = text.lower()
    if any(keyword in low for keyword in SPAM_KEYWORDS):
        return True
    if any(keyword in low for keyword in SUPPLY_KEYWORDS) and not has_demand_intent(text):
        return True
    return False


def is_candidate(text: str) -> bool:
    low = text.lower()
    has_contact = any(extract_contacts(text).values())
    has_real_estate = detect_segment(text) is not None or "недвиж" in low or "аренд" in low
    return has_contact and has_real_estate and has_demand_intent(text) and not is_noise_or_supply(text)


def supabase_request(config: Config, method: str, path: str, payload: Any = None) -> Any:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{config.supabase_url}/rest/v1/{path}",
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json",
            "apikey": config.service_role_key,
            "Authorization": f"Bearer {config.service_role_key}",
            "Prefer": "return=representation",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8")
        raise RuntimeError(f"Supabase error {error.code}: {detail}") from error


def lead_exists(config: Config, source_external_id: str) -> bool:
    encoded = source_external_id.replace(",", "%2C").replace(":", "%3A")
    rows = supabase_request(config, "GET", f"leads?select=id&source_external_id=eq.{encoded}&limit=1")
    return bool(rows)


def telegram_bot_request(config: Config, method: str, payload: dict[str, Any]) -> Any:
    if not config.bot_token:
        return None
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{config.bot_token}/{method}",
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read().decode("utf-8")
            result = json.loads(raw) if raw else {}
            if not result.get("ok"):
                raise RuntimeError(result.get("description") or "Telegram API error")
            return result.get("result")
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8")
        raise RuntimeError(f"Telegram API error {error.code}: {detail}") from error


def resolve_notify_chat_id(config: Config) -> Optional[str]:
    if config.notify_chat_id:
        return config.notify_chat_id
    updates = telegram_bot_request(config, "getUpdates", {"limit": 10, "allowed_updates": ["message"]}) or []
    for update in reversed(updates):
        message = update.get("message") or {}
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        if chat_id:
            return str(chat_id)
    return None


def format_lead_notification(lead: dict[str, Any], contacts: dict[str, list[str]], lead_id: str) -> str:
    contact_parts = []
    if contacts.get("phones"):
        contact_parts.append(f"тел: {contacts['phones'][0]}")
    if contacts.get("telegram_usernames"):
        contact_parts.append(f"tg: @{contacts['telegram_usernames'][0]}")
    if contacts.get("emails"):
        contact_parts.append(f"email: {contacts['emails'][0]}")
    text = (lead.get("raw_text") or "").strip()
    if len(text) > 700:
        text = text[:700].rstrip() + "..."
    return "\n".join([
        "Новый лид из Telegram",
        f"Сегмент: {lead.get('property_segment') or 'не определен'}",
        f"Намерение: {lead.get('intent') or 'unknown'}",
        f"Контакты: {', '.join(contact_parts) if contact_parts else 'не найдены'}",
        f"Источник: {lead.get('source_url') or 'без ссылки'}",
        f"ID: {lead_id}",
        "",
        text,
    ])


def notify_lead(config: Config, lead: dict[str, Any], contacts: dict[str, list[str]], lead_id: str) -> None:
    if not config.bot_token:
        return
    chat_id = resolve_notify_chat_id(config)
    if not chat_id:
        print("telegram notification skipped: no chat id; send /start to the bot")
        return
    telegram_bot_request(config, "sendMessage", {
        "chat_id": chat_id,
        "text": format_lead_notification(lead, contacts, lead_id),
        "disable_web_page_preview": True,
    })
    time.sleep(1.2)


def source_from_row(row: dict[str, Any]) -> Optional[str]:
    username = str(row.get("username") or "").strip()
    if username:
        return username if username.startswith("@") else f"@{username}"
    url = str(row.get("url") or "").strip()
    match = re.search(r"(?:https?://t\.me/|t\.me/|@)([A-Za-z0-9_]{5,64})", url)
    if match:
        return f"@{match.group(1)}"
    return None


def load_monitoring_sources(config: Config) -> list[str]:
    rows = supabase_request(
        config,
        "GET",
        "source_discovery?select=username,url&platform=eq.telegram&status=eq.monitoring&order=created_at.desc&limit=200",
    ) or []
    if not rows:
        rows = supabase_request(
            config,
            "GET",
            "source_discovery?select=username,url&platform=eq.telegram&status=in.(new,approved)&order=created_at.desc&limit=200",
        ) or []
    sources = []
    seen = set()
    for row in rows:
        source = source_from_row(row)
        if not source or source.lower() in seen:
            continue
        seen.add(source.lower())
        sources.append(source)
    return sources


def parse_proxy(proxy_url: Optional[str]) -> tuple[Any, Any]:
    if not proxy_url:
        return None, None
    parsed = urlparse(proxy_url)
    if parsed.netloc == "t.me" and parsed.path == "/proxy":
        from telethon.network.connection.tcpmtproxy import (
            ConnectionTcpMTProxyIntermediate,
            ConnectionTcpMTProxyRandomizedIntermediate,
        )
        from urllib.parse import parse_qs

        query = parse_qs(parsed.query)
        server = query.get("server", [""])[0]
        port = int(query.get("port", ["0"])[0])
        secret = query.get("secret", [""])[0]
        if not server or not port or not secret:
            raise ValueError("Telegram MTProto proxy link must include server, port and secret")
        normalized_secret = normalize_mtproxy_secret(secret)
        connection = (
            ConnectionTcpMTProxyRandomizedIntermediate
            if normalized_secret.startswith("dd")
            else ConnectionTcpMTProxyIntermediate
        )
        return connection, (server, port, normalized_secret)

    import socks

    scheme_map = {
        "socks5": socks.SOCKS5,
        "socks4": socks.SOCKS4,
        "http": socks.HTTP,
        "https": socks.HTTP,
    }
    proxy_type = scheme_map.get(parsed.scheme.lower())
    if not proxy_type or not parsed.hostname or not parsed.port:
        raise ValueError("TELEGRAM_PROXY must look like socks5://user:pass@host:1080 or http://host:8080")
    return None, (
        proxy_type,
        parsed.hostname,
        parsed.port,
        True,
        parsed.username,
        parsed.password,
    )


def normalize_mtproxy_secret(secret: str) -> str:
    cleaned = secret.strip()
    if re.fullmatch(r"[0-9a-fA-F]+", cleaned):
        return cleaned.lower()
    padded = cleaned + "=" * (-len(cleaned) % 4)
    return base64.urlsafe_b64decode(padded).hex()


async def collect() -> None:
    from telethon import TelegramClient

    config = get_config()
    sources = config.sources or load_monitoring_sources(config)
    if not sources:
        raise SystemExit("No Telegram sources configured. Add sources with monitoring status in the lead UI.")

    connection, proxy = parse_proxy(config.proxy_url)
    client_options = {"proxy": proxy}
    if connection:
        client_options["connection"] = connection
    client = TelegramClient(config.session_path, config.api_id, config.api_hash, **client_options)
    await client.start(phone=config.phone)
    sent_notifications = 0

    for source in sources:
        entity = await client.get_entity(source)
        async for message in client.iter_messages(entity, limit=config.limit_per_source):
            if not is_recent_message(message.date, config.max_message_age_days):
                break
            text = message.message or ""
            if not text or not is_candidate(text):
                continue

            contacts = extract_contacts(text)
            source_url = None
            if getattr(entity, "username", None):
                source_url = f"https://t.me/{entity.username}/{message.id}"

            lead = {
                "source_url": source_url,
                "source_external_id": f"telegram:{getattr(entity, 'id', source)}:{message.id}",
                "raw_text": text,
                "person_name": None,
                "company_name": None,
                "phone_raw": contacts["phones"][0] if contacts["phones"] else None,
                "phone_normalized": contacts["phones"][0] if contacts["phones"] else None,
                "email": contacts["emails"][0] if contacts["emails"] else None,
                "telegram_username": contacts["telegram_usernames"][0] if contacts["telegram_usernames"] else None,
                "vk_url": contacts["vk_urls"][0] if contacts["vk_urls"] else None,
                "property_segment": detect_segment(text),
                "intent": detect_intent(text),
                "confidence": 0.78,
                "score": 65,
                "score_reason": "Telegram message with real estate intent and contact",
                "status": "new",
                "collected_at": message.date.isoformat() if message.date else now(),
            }

            record = {
                "source_url": source_url,
                "source_url_hash": stable_hash(source_url) if source_url else None,
                "source_external_id": lead["source_external_id"],
                "raw_text": text,
                "raw_payload": {
                    "source": source,
                    "chat_id": getattr(entity, "id", None),
                    "message_id": message.id,
                    "date": message.date.isoformat() if message.date else None,
                },
                "extracted_contacts": contacts,
                "parser_name": "telegram_user_collector",
                "parser_version": "0.1.0",
                "extraction_confidence": 0.78,
                "legal_basis_note": "telegram account accessible source",
                "published_at": message.date.isoformat() if message.date else None,
                "collected_at": now(),
            }

            if config.dry_run:
                print(json.dumps({"lead": lead, "record": record}, ensure_ascii=False))
                continue

            if lead_exists(config, lead["source_external_id"]):
                continue

            created = supabase_request(config, "POST", "leads", lead)
            record["lead_id"] = created[0]["id"]
            supabase_request(config, "POST", "lead_source_records", record)
            if sent_notifications < config.notify_max_per_run:
                try:
                    notify_lead(config, lead, contacts, created[0]["id"])
                    sent_notifications += 1
                except Exception as error:
                    print(f"telegram notification skipped: {error}")
            print(f"saved {created[0]['id']} from {source}")


if __name__ == "__main__":
    asyncio.run(collect())
