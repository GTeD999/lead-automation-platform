#!/usr/bin/env python3
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


PORT = int(os.environ.get("PORT", "8091"))
STATIC_DIR = Path(os.environ.get("STATIC_DIR", Path(__file__).resolve().parent / "dist"))
SUPABASE_URL = os.environ.get("SUPABASE_URL", "http://kong:8000").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "").strip()
APIFY_ACTOR_ID = os.environ.get("APIFY_ACTOR_ID", "").strip()
APIFY_SERP_ACTOR_ID = os.environ.get("APIFY_SERP_ACTOR_ID", "apify/google-search-scraper").strip()
APIFY_DEFAULT_CITY = os.environ.get("APIFY_DEFAULT_CITY", "Новосибирск").strip()
APIFY_DEFAULT_LIMIT = int(os.environ.get("APIFY_DEFAULT_LIMIT", "25"))
HH_AREA_ID = os.environ.get("HH_AREA_ID", "4").strip()
HH_DEFAULT_LIMIT = int(os.environ.get("HH_DEFAULT_LIMIT", "20"))
HH_DEFAULT_PERIOD_DAYS = int(os.environ.get("HH_DEFAULT_PERIOD_DAYS", "30"))
AUTO_COLLECT_ENABLED = os.environ.get("AUTO_COLLECT_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}
AUTO_COLLECT_INTERVAL_MINUTES = int(os.environ.get("AUTO_COLLECT_INTERVAL_MINUTES", "180"))
AUTO_COLLECT_START_DELAY_SECONDS = int(os.environ.get("AUTO_COLLECT_START_DELAY_SECONDS", "90"))
AUTO_COLLECT_LOOKBACK_DAYS = int(os.environ.get("AUTO_COLLECT_LOOKBACK_DAYS", "1"))


RUN_LOCK = threading.Lock()
SCHEDULER_STATE = {
    "enabled": AUTO_COLLECT_ENABLED,
    "interval_minutes": AUTO_COLLECT_INTERVAL_MINUTES,
    "lookback_days": AUTO_COLLECT_LOOKBACK_DAYS,
    "running": False,
    "last_started_at": "",
    "last_finished_at": "",
    "last_created": 0,
    "last_error": "",
}


SCENARIO_ICONS = {
    "office-tenants": "Building2",
    "warehouse": "Package",
    "retail": "ShoppingBag",
    "growth": "TrendingUp",
    "owners": "Key",
    "buyers": "Coins",
    "direct-warehouse": "Search",
    "direct-commercial": "Search",
    "direct-residential": "Search",
}

SCENARIO_QUERIES = {
    "office-tenants": ["офис менеджер", "менеджер по продажам", "руководитель отдела продаж", "call центр"],
    "warehouse": ["кладовщик", "комплектовщик", "заведующий складом", "работник склада", "логист"],
    "retail": ["продавец консультант", "администратор магазина", "управляющий магазином", "кассир продавец"],
    "growth": ["руководитель филиала", "региональный менеджер", "директор филиала", "открытие филиала"],
    "owners": ["управляющий бизнес центром", "администратор бизнес центра", "эксплуатация здания"],
    "buyers": ["инвестиционный менеджер", "аналитик инвестиций", "развитие сети"],
    "direct-warehouse": [
        "сниму склад", "нужен склад", "ищу склад", "арендую склад", "нужен теплый склад",
        "сниму теплый склад", "нужен холодный склад", "ищу склад ответственного хранения",
        "нужен склад 100 м2", "нужен склад 200 м2", "нужен склад 500 м2", "нужен склад 1000 м2",
        "сниму ангар", "ищу ангар", "нужно складское помещение", "сниму складское помещение",
        "ищу помещение под склад", "нужен склад с пандусом", "нужен склад для интернет магазина",
        "срочно нужен склад", "рассмотрю склад в аренду", "куплю склад", "ищу склад в покупку",
    ],
    "direct-commercial": [
        "сниму помещение", "нужно коммерческое помещение", "ищу офис", "сниму офис", "нужно торговое помещение",
        "ищу коммерческое помещение", "сниму коммерческое помещение", "нужно помещение под магазин",
        "ищу помещение под магазин", "сниму торговую площадь", "нужен офис продаж", "ищу офис продаж",
        "сниму офис 50 м2", "сниму офис 100 м2", "сниму помещение 100 м2", "сниму помещение 200 м2",
        "нужно помещение под салон", "нужно помещение под общепит", "ищу помещение под кафе",
        "ищу помещение на первом этаже", "куплю коммерческое помещение", "куплю офис", "куплю помещение",
        "рассмотрю помещение в аренду", "срочно нужен офис", "срочно нужно помещение",
    ],
    "direct-residential": [
        "куплю квартиру", "ищу квартиру", "сниму квартиру", "нужна квартира", "куплю дом",
        "ищу дом", "сниму дом", "нужна квартира на месяц", "куплю 1 комнатную квартиру",
        "куплю 2 комнатную квартиру", "куплю 3 комнатную квартиру", "ищу квартиру без посредников",
        "сниму квартиру без посредников", "нужна квартира семье", "срочно сниму квартиру",
        "срочно куплю квартиру", "рассмотрю квартиру", "ищу новостройку", "куплю студию",
        "сниму студию", "куплю квартиру в новосибирске", "сниму квартиру в новосибирске",
    ],
}

DIRECT_INTENT_SCENARIOS = {"direct-warehouse", "direct-commercial", "direct-residential"}

CATEGORY_BY_TARGET = {
    "office": "services",
    "warehouse": "logistics",
    "retail": "retail",
    "production": "production",
}

CATEGORY_LABELS = {
    "services": "услуги",
    "logistics": "логистика",
    "retail": "ритейл",
    "production": "производство",
    "finance": "инвесторы",
}

BLOCKED_COMPANY_KEYWORDS = [
    "агентство недвижимости",
    "агентство коммерческой недвижимости",
    "недвижимости без посредников",
    "сайт объявлений недвижимости",
    "риэлтор",
    "риелтор",
    "кадастр",
    "федерального агентства",
    "орган федеральной власти",
    "администрация",
    "жк ",
    "жилой комплекс",
    "компания-застройщик",
    "застройщик",
    "девелопмент",
    "девелопер",
    "кадровое агентство",
    "аутсорсинг персонала",
    "работа – это просто",
    "работа - это просто",
]

GENERIC_SIGNAL_DOMAINS = [
    "gorodrabot.ru",
    "jobfilter.ru",
    "jooble.org",
    "trudvsem.ru",
    "zarplata.ru",
    "superjob.ru",
]

GENERIC_SIGNAL_TITLE_PREFIXES = [
    "работа ",
    "вакансии ",
    "свежие вакансии",
    "найти работу",
]

COMPANY_STOPWORDS = [
    "headhunter",
    "hh.ru",
    "hh",
    "работа",
    "вакансия",
    "вакансии",
    "новосибирск",
    "новосибирская область",
    "сегодня",
    "откликнуться",
]

RU_MONTHS = {
    "янв": 1,
    "фев": 2,
    "мар": 3,
    "апр": 4,
    "мая": 5,
    "май": 5,
    "июн": 6,
    "июл": 7,
    "авг": 8,
    "сен": 9,
    "окт": 10,
    "ноя": 11,
    "дек": 12,
}

GROWTH_SIGNAL_KEYWORDS = [
    "расшир",
    "растёт",
    "растет",
    "новый склад",
    "нового склада",
    "новый филиал",
    "открываем",
    "открытие",
    "распределительный центр",
    "рц",
    "запуск",
    "увеличением объема",
    "увеличением объёма",
    "масштабируем",
]

ROLE_SIGNAL_KEYWORDS = {
    "warehouse": [
        "заведующий складом",
        "начальник склада",
        "руководитель склада",
        "директор склада",
        "руководитель логистики",
        "начальник логистики",
    ],
    "retail": [
        "управляющий магазином",
        "директор магазина",
        "администратор магазина",
        "территориальный управляющий",
    ],
    "office": [
        "руководитель отдела продаж",
        "директор филиала",
        "руководитель филиала",
        "региональный менеджер",
    ],
    "production": [
        "начальник производства",
        "мастер участка",
        "руководитель производства",
    ],
}

GENERIC_VACANCY_KEYWORDS = [
    "комплектовщик",
    "кладовщик",
    "грузчик",
    "работник склада",
    "сборщик заказов",
    "продавец",
    "кассир",
    "офис менеджер",
]

DIRECT_INTENT_KEYWORDS = [
    "сниму",
    "куплю",
    "ищу",
    "нужен",
    "нужна",
    "нужно",
    "арендую",
    "рассмотрю",
]

DIRECT_OBJECT_KEYWORDS = {
    "warehouse": ["склад", "ангар", "производственно-склад", "помещение под склад"],
    "retail": ["коммерческое помещение", "помещение", "офис", "торговое помещение", "псн", "стрит ритейл"],
    "office": ["офис", "кабинет", "рабочее пространство"],
    "residential": ["квартира", "дом", "апартаменты", "комната"],
}

DIRECT_NEGATIVE_KEYWORDS = [
    "сдам",
    "сдаю",
    "сдается",
    "сдаётся",
    "продам",
    "продаю",
    "продается",
    "продаётся",
    "предлагаем",
    "предлагаю",
    "риэлтор",
    "агентство",
    "без комиссии",
    "комиссия",
    "подберем",
    "подберём",
    "услуги",
    "куплю вашу",
    "выкупим",
]

DIRECT_SOURCE_QUERIES = [
    "site:vk.com",
    "site:t.me",
    "site:telegram.me",
    "site:forum.ngs.ru",
    "site:ngs.ru",
    "site:avito.ru",
    "site:youla.ru",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def days_ago_date(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=max(1, days))).date().isoformat()


def rest_request(method: str, table: str, query: str = "", payload: Any = None, prefer: str = "return=representation") -> Any:
    if not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is not configured")

    url = f"{SUPABASE_URL}/rest/v1/{table}{query}"
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": prefer,
    }
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else None
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Supabase {method} {table} failed: {error.code} {detail}") from error


def http_json(method: str, url: str, payload: Any = None, timeout: int = 180) -> Any:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else None
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {method} failed: {error.code} {detail}") from error


def http_get_json(url: str, headers: dict[str, str] | None = None, timeout: int = 60) -> Any:
    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Accept": "application/json",
            "User-Agent": "OfficeLeadIntelligence/0.1 (contact: example.com)",
            "HH-User-Agent": "OfficeLeadIntelligence/0.1 (info@example.com)",
            **(headers or {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else None
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP GET failed: {error.code} {detail}") from error


def request_label(kind: str) -> str:
    return {
        "office": "офис",
        "warehouse": "склад",
        "retail": "торговля",
        "production": "производство",
        "residential": "жилая недвижимость",
    }.get(kind, kind)


def target_label(kind: str) -> str:
    return {
        "office": "офис",
        "warehouse": "склад",
        "retail": "торговое помещение",
        "production": "производственное помещение",
        "residential": "жилой объект",
    }.get(kind, "коммерческое помещение")


def first_value(data: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = data.get(key)
        if value not in (None, "", [], {}):
            if isinstance(value, list):
                return ", ".join(str(item) for item in value[:3])
            return str(value)
    return ""


def normalize_phone(value: str) -> str:
    return " ".join(str(value or "").replace("\n", " ").split())


def normalize_website(value: str) -> str:
    value = str(value or "").strip()
    value = value.removeprefix("https://").removeprefix("http://").rstrip("/")
    return value


def extract_city(item: dict[str, Any], fallback: str) -> str:
    city = first_value(item, "city", "municipality", "locatedIn", "addressLocality")
    if city:
        return city
    address = first_value(item, "address", "street", "formattedAddress")
    for part in address.split(","):
        part = part.strip()
        if part.lower() in {"новосибирск", "москва", "санкт-петербург", "барнаул", "екатеринбург"}:
            return part
    return fallback


def score_company(company: dict[str, str], target_type: str) -> tuple[int, str]:
    score = 45
    reasons = []
    if company.get("phone"):
        score += 10
        reasons.append("есть телефон")
    if company.get("website"):
        score += 8
        reasons.append("есть сайт")
    if company.get("address"):
        score += 7
        reasons.append("есть адрес")
    category_text = f"{company.get('category_label', '')} {company.get('name', '')}".lower()
    keyword_bonus = {
        "office": ["it", "агентство", "консалт", "юрид", "финанс", "сервис"],
        "warehouse": ["логист", "дистриб", "склад", "доставка", "интернет"],
        "retail": ["магазин", "кофе", "салон", "шоурум", "ритейл"],
        "production": ["производ", "завод", "цех", "оборуд"],
    }
    if any(word in category_text for word in keyword_bonus.get(target_type, [])):
        score += 22
        reasons.append(f"профиль похож на спрос на {target_label(target_type)}")
    score = max(35, min(score, 94))
    if not reasons:
        reasons.append("найдена компания из открытого B2B-источника")
    return score, ", ".join(reasons)


def score_hh_signal(vacancy: dict[str, Any], target_type: str) -> tuple[int, str]:
    title = first_value(vacancy, "name").lower()
    snippet = vacancy.get("snippet") or {}
    signal_text = f"{title} {snippet.get('requirement') or ''} {snippet.get('responsibility') or ''}".lower()
    score = 62
    reasons = ["найдена свежая вакансия как сигнал возможного роста"]
    bonuses = {
        "warehouse": ["кладовщик", "комплектовщик", "склад", "логист", "грузчик"],
        "retail": ["продавец", "магазин", "администратор", "кассир", "управляющий"],
        "office": ["офис", "менеджер", "отдел продаж", "call", "филиал"],
        "production": ["производство", "технолог", "цех", "оператор"],
    }
    if any(word in signal_text for word in bonuses.get(target_type, [])):
        score += 18
        reasons.append(f"вакансия совпадает с потребностью под {target_label(target_type)}")
    if "филиал" in signal_text or "расшир" in signal_text or "новый" in signal_text:
        score += 10
        reasons.append("есть формулировка про рост/филиал/расширение")
    score = min(score, 92)
    return score, "; ".join(reasons)


def signal_quality(title: str, snippet: str, target_type: str, repeat_count: int = 1) -> tuple[bool, int, str, list[str]]:
    text = f"{title} {snippet}".lower()
    reasons: list[str] = []
    score = 48
    has_growth = any(keyword in text for keyword in GROWTH_SIGNAL_KEYWORDS)
    has_role = any(keyword in text for keyword in ROLE_SIGNAL_KEYWORDS.get(target_type, []))
    is_generic = any(keyword in text for keyword in GENERIC_VACANCY_KEYWORDS)

    if has_growth:
        score += 28
        reasons.append("есть формулировка роста: расширение, новый склад, филиал или запуск")
    if has_role:
        score += 18
        reasons.append("вакансия на управленческую роль, связанную с помещением")
    if repeat_count >= 2:
        score += 18
        reasons.append(f"у компании найдено {repeat_count} похожих свежих сигналов")
    if is_generic and not has_growth and not has_role and repeat_count < 2:
        reasons.append("одиночная линейная вакансия без признаков расширения")
        return False, 35, "; ".join(reasons), reasons

    actionable = has_growth or has_role or repeat_count >= 2
    if not actionable:
        reasons.append("недостаточно признаков спроса на помещение")
        return False, 35, "; ".join(reasons), reasons

    score = max(65, min(score, 92))
    return True, score, "; ".join(reasons), reasons


def is_blocked_company(company: dict[str, Any]) -> tuple[bool, str]:
    text = " ".join(str(company.get(key) or "") for key in ("name", "category_label", "website")).lower()
    for keyword in BLOCKED_COMPANY_KEYWORDS:
        if keyword in text:
            return True, f"отфильтровано: {keyword}"
    name = str(company.get("name") or "").strip()
    if company.get("source_provider") in {"HH", "Signal search"} and re.fullmatch(r"[А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+", name):
        return True, "отфильтровано: похоже на физлицо, а не компанию"
    if company.get("source_provider") not in {"HH", "Signal search"} and not company.get("phone") and not company.get("website"):
        return True, "отфильтровано: нет телефона и сайта"
    return False, ""


def normalize_hh_vacancy(vacancy: dict[str, Any], scenario: dict[str, Any]) -> dict[str, Any]:
    employer = vacancy.get("employer") or {}
    area = vacancy.get("area") or {}
    address = vacancy.get("address") or {}
    snippet = vacancy.get("snippet") or {}
    target_type = scenario["target_property_type"]
    signal_title = first_value(vacancy, "name") or "Вакансия без названия"
    signal_url = first_value(vacancy, "alternate_url", "url")
    signal_date = first_value(vacancy, "published_at", "created_at")
    signal_text = " ".join(
        value for value in [
            signal_title,
            str(snippet.get("requirement") or ""),
            str(snippet.get("responsibility") or ""),
        ] if value
    )
    actionable, quality_score, quality_reason, quality_reasons = signal_quality(signal_title, signal_text, target_type)
    company = {
        "name": employer.get("name") or "Компания из hh.ru",
        "inn": "",
        "city": area.get("name") or APIFY_DEFAULT_CITY,
        "address": address.get("raw") or "",
        "category": CATEGORY_BY_TARGET.get(target_type, "services"),
        "category_label": "работодатель hh.ru",
        "phone": "",
        "email": "",
        "website": normalize_website(employer.get("alternate_url") or ""),
        "source_url": signal_url,
        "source_provider": "HH",
        "raw_payload": {
            "source": "hh.ru",
            "signal_type": "vacancy",
            "signal_title": signal_title,
            "signal_text": signal_text,
            "signal_url": signal_url,
            "signal_date": signal_date,
            "signal_is_actionable": actionable,
            "signal_quality_reasons": quality_reasons,
            "vacancy": vacancy,
        },
    }
    date_label = signal_date[:10] if signal_date else "дата не указана"
    lead = {
        "score": quality_score,
        "status": "new",
        "target_property_type": target_type,
        "target_deal_type": "аренда",
        "ai_reason": f"{quality_reason}. Сигнал: вакансия «{signal_title}» от {date_label}.",
        "suggested_offer": f"Проверить потребность: {target_label(target_type)}. Повод: не одиночная вакансия, а признак роста/управленческой потребности.",
        "source_provider": "HH",
        "source_age_label": date_label,
    }
    return {"company": company, "lead": lead}


def normalize_apify_item(item: dict[str, Any], scenario: dict[str, Any], city: str) -> dict[str, Any]:
    target_type = scenario["target_property_type"]
    category = CATEGORY_BY_TARGET.get(target_type, "services")
    categories = first_value(item, "categoryName", "category", "categories", "types")
    company = {
        "name": first_value(item, "title", "name", "companyName") or "Компания без названия",
        "inn": first_value(item, "inn", "taxId"),
        "city": extract_city(item, city),
        "address": first_value(item, "address", "street", "formattedAddress"),
        "category": category,
        "category_label": categories or CATEGORY_LABELS.get(category, "компания"),
        "phone": normalize_phone(first_value(item, "phone", "phoneNumber", "phones", "contactPhone")),
        "email": first_value(item, "email", "emails"),
        "website": normalize_website(first_value(item, "website", "websiteUrl", "companyWebsite", "domain")),
        "source_url": first_value(item, "url", "placeUrl", "googleMapsUri"),
        "source_provider": "Apify",
        "raw_payload": item,
    }
    score, reason = score_company(company, target_type)
    lead = {
        "score": score,
        "status": "new",
        "target_property_type": target_type,
        "target_deal_type": "аренда" if target_type != "retail" else "аренда",
        "ai_reason": reason,
        "suggested_offer": f"Подобрать {target_label(target_type)} в городе {company['city']}",
        "source_provider": "Apify",
        "source_age_label": "только что",
    }
    return {"company": company, "lead": lead}


def find_existing_company(company: dict[str, Any]) -> dict[str, Any] | None:
    filters = []
    if company.get("inn"):
        filters.append(f"inn=eq.{urllib.parse.quote(company['inn'])}")
    if company.get("website"):
        filters.append(f"website=eq.{urllib.parse.quote(company['website'])}")
    if not filters and company.get("name") and company.get("city"):
        filters.append(f"name=eq.{urllib.parse.quote(company['name'])}&city=eq.{urllib.parse.quote(company['city'])}")
    for query in filters:
        rows = rest_request("GET", "li_companies", f"?select=*&{query}&limit=1") or []
        if rows:
            return rows[0]
    return None


def insert_company_lead(item: dict[str, Any], run_id: str | None = None) -> bool:
    company_payload = dict(item["company"])
    blocked, _reason = is_blocked_company(company_payload)
    if blocked:
        return False
    existing = find_existing_company(company_payload)
    if existing:
        company = rest_request("PATCH", "li_companies", f"?id=eq.{existing['id']}", payload={
            **company_payload,
            "updated_at": now_iso(),
        })[0]
    else:
        company = rest_request("POST", "li_companies", payload=company_payload)[0]
    duplicate = rest_request(
        "GET",
        "li_lead_candidates",
        f"?select=id&company_id=eq.{company['id']}&target_property_type=eq.{urllib.parse.quote(item['lead']['target_property_type'])}&status=neq.archived&limit=1",
    ) or []
    if duplicate:
        return False
    lead_payload = dict(item["lead"])
    lead_payload["company_id"] = company["id"]
    if run_id:
        lead_payload["run_id"] = run_id
    rest_request("POST", "li_lead_candidates", payload=lead_payload)
    return True


def apify_input_for(scenario: dict[str, Any], city: str, limit: int) -> dict[str, Any]:
    queries = [f"{query} {city}" for query in SCENARIO_QUERIES.get(scenario["slug"], [scenario["title"]])]
    return {
        "searchStringsArray": queries,
        "locationQuery": city,
        "maxCrawledPlacesPerSearch": max(1, limit // max(len(queries), 1)),
        "language": "ru",
        "countryCode": "ru",
    }


def fetch_apify_places(scenario: dict[str, Any], city: str, limit: int) -> list[dict[str, Any]]:
    if not APIFY_TOKEN or not APIFY_ACTOR_ID:
        raise RuntimeError("Для реального сбора нужно задать APIFY_TOKEN и APIFY_ACTOR_ID в окружении сервиса.")
    actor = urllib.parse.quote(APIFY_ACTOR_ID, safe="")
    url = f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items?token={urllib.parse.quote(APIFY_TOKEN)}"
    payload = apify_input_for(scenario, city, limit)
    rows = http_json("POST", url, payload=payload, timeout=300)
    if not isinstance(rows, list):
        raise RuntimeError("Apify вернул неожиданный формат ответа.")
    return rows[:limit]


def fetch_hh_signals(scenario: dict[str, Any], limit: int, period_days: int = HH_DEFAULT_PERIOD_DAYS) -> list[dict[str, Any]]:
    queries = SCENARIO_QUERIES.get(scenario["slug"], [scenario["title"]])
    per_query = max(1, limit // max(len(queries), 1))
    results: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for query in queries:
        params = urllib.parse.urlencode({
            "text": query,
            "area": HH_AREA_ID,
            "period": period_days,
            "per_page": per_query,
            "page": 0,
            "order_by": "publication_time",
        })
        data = http_get_json(f"https://api.hh.ru/vacancies?{params}")
        for vacancy in (data or {}).get("items", []):
            vacancy_id = str(vacancy.get("id") or "")
            if vacancy_id and vacancy_id in seen_ids:
                continue
            if vacancy_id:
                seen_ids.add(vacancy_id)
            results.append(vacancy)
            if len(results) >= limit:
                return results
    return results


def with_after_filter(query: str, after_date: str = "") -> str:
    return f"{query} after:{after_date}" if after_date else query


def apify_serp_input_for(scenario: dict[str, Any], city: str, after_date: str = "") -> dict[str, Any]:
    flat_queries = []
    for query in SCENARIO_QUERIES.get(scenario["slug"], [scenario["title"]]):
        if scenario["slug"] in DIRECT_INTENT_SCENARIOS:
            flat_queries.append(with_after_filter(f'"{query}" "{city}"', after_date))
            flat_queries.extend([with_after_filter(f'{source} "{query}" "{city}"', after_date) for source in DIRECT_SOURCE_QUERIES[:4]])
        else:
            flat_queries.extend([
                with_after_filter(f'site:hh.ru/vacancy {city} "{query}"', after_date),
                with_after_filter(f'{city} "{query}" "открываем" OR "расширяем" OR "новый филиал"', after_date),
            ])
    return {
        "queries": "\n".join(flat_queries[:36] if scenario["slug"] in DIRECT_INTENT_SCENARIOS else flat_queries[:12]),
        "resultsPerPage": 10,
        "maxPagesPerQuery": 1,
        "countryCode": "ru",
        "languageCode": "ru",
        "perplexitySearch": {"enablePerplexity": False, "returnImages": False, "returnRelatedQuestions": False},
        "chatGptSearch": {"enableChatGpt": False},
        "copilotSearch": {"enableCopilot": False},
        "maximumLeadsEnrichmentRecords": 0,
    }


def extract_serp_results(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for row in rows:
        for key in ("organicResults", "organic_results", "results"):
            value = row.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        results.append(item)
        if any(key in row for key in ("url", "link", "title")):
            results.append(row)
    return results


def is_fresh_signal_result(item: dict[str, Any]) -> bool:
    title = first_value(item, "title", "name")
    snippet = first_value(item, "description", "snippet", "text")
    url = first_value(item, "url", "link")
    text = f"{title} {snippet}".lower()
    if not title or not snippet:
        return False
    if "google." in url and "/search?" in url:
        return False
    if "в архиве" in text or "архивная" in text:
        return False
    if any(title.lower().startswith(prefix) for prefix in GENERIC_SIGNAL_TITLE_PREFIXES):
        return False
    if "hh.ru/vacancy" in url:
        return True
    if any(domain in url.lower() for domain in GENERIC_SIGNAL_DOMAINS):
        return bool(company_name_from_signal(title, snippet))
    return any(word in text for word in ["ищем", "нужен", "открываем", "расширяем", "филиал", "кладовщик", "комплектовщик", "склад"])


def is_direct_intent_result(item: dict[str, Any], target_type: str) -> bool:
    title = first_value(item, "title", "name")
    snippet = first_value(item, "description", "snippet", "text")
    url = first_value(item, "url", "link")
    text = f"{title} {snippet}".lower()
    if not title or not snippet or not url:
        return False
    if "google." in url and "/search?" in url:
        return False
    if "в архиве" in text or "архив" in text:
        return False
    if any(keyword in text for keyword in DIRECT_NEGATIVE_KEYWORDS):
        return False
    has_intent = any(keyword in text for keyword in DIRECT_INTENT_KEYWORDS)
    has_object = any(keyword in text for keyword in DIRECT_OBJECT_KEYWORDS.get(target_type, []))
    return has_intent and has_object


def clean_company_name(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", str(value or ""))
    value = " ".join(value.replace("«", "\"").replace("»", "\"").split())
    value = re.split(r"\s+(?:ищет|ищем|приглашает|требуется|открывает|расширяет)\b", value, maxsplit=1, flags=re.IGNORECASE)[0]
    value = re.split(r"\s+(?:вакансия|работа|hh\.ru|headhunter)\b", value, maxsplit=1, flags=re.IGNORECASE)[0]
    value = value.strip(" .,:;|-\"'()[]")
    value = re.sub(r"^(?:ооо|ао|зао|ип)\s+", "", value, flags=re.IGNORECASE).strip()
    if not value:
        return ""
    lowered = value.lower()
    if lowered.startswith(("активно ", "мы ", "карьерист", "вакансия")):
        return ""
    if lowered in COMPANY_STOPWORDS or any(stopword == lowered for stopword in COMPANY_STOPWORDS):
        return ""
    if len(value) < 2 or len(value) > 180:
        return ""
    return value


def company_name_from_signal(title: str, snippet: str) -> str:
    for text in (snippet, title):
        match = re.search(r"в компании\s+([^.\n|]+)", text, flags=re.IGNORECASE)
        if match:
            company_name = clean_company_name(match.group(1))
            if company_name:
                return company_name
    match = re.search(r"\s[-–—]\s([^|–—-]+?)\s[-–—]\s(?:HeadHunter|HH\.ru|hh\.ru)", title, flags=re.IGNORECASE)
    if match:
        company_name = clean_company_name(match.group(1))
        if company_name:
            return company_name
    match = re.search(r"(?:Компания|Работодатель):\s*([^.\n|]+)", snippet, flags=re.IGNORECASE)
    if match:
        company_name = clean_company_name(match.group(1))
        if company_name:
            return company_name
    return ""


def signal_date_from_text(text: str) -> str:
    text = str(text or "").lower()
    explicit = re.search(r"(\d{1,2})\s+([а-яё]{3,})\.?\s+(\d{4})", text)
    if explicit:
        day = int(explicit.group(1))
        month = RU_MONTHS.get(explicit.group(2)[:3])
        year = int(explicit.group(3))
        if month:
            return datetime(year, month, day, tzinfo=timezone.utc).isoformat()
    relative = re.search(r"(\d{1,2})\s+дн(?:я|ей|ь)\s+назад", text)
    if relative:
        return (datetime.now(timezone.utc) - timedelta(days=int(relative.group(1)))).isoformat()
    if "вчера" in text:
        return (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    if "сегодня" in text:
        return datetime.now(timezone.utc).isoformat()
    return ""


def fetch_apify_serp_signals(scenario: dict[str, Any], city: str, limit: int, after_date: str = "") -> list[dict[str, Any]]:
    if not APIFY_TOKEN:
        raise RuntimeError("hh.ru API недоступен, а для fallback-поиска нужен APIFY_TOKEN.")
    actor = urllib.parse.quote(APIFY_SERP_ACTOR_ID, safe="")
    url = f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items?token={urllib.parse.quote(APIFY_TOKEN)}"
    rows = http_json("POST", url, payload=apify_serp_input_for(scenario, city, after_date), timeout=300)
    if not isinstance(rows, list):
        raise RuntimeError("Apify search вернул неожиданный формат ответа.")
    filtered = []
    for item in extract_serp_results(rows):
        if scenario["slug"] in DIRECT_INTENT_SCENARIOS:
            if is_direct_intent_result(item, scenario["target_property_type"]):
                filtered.append(item)
            continue
        if not is_fresh_signal_result(item):
            continue
        title = first_value(item, "title", "name")
        snippet = first_value(item, "description", "snippet", "text")
        if not company_name_from_signal(title, snippet):
            continue
        filtered.append(item)
    return filtered[:limit]


def source_label_from_url(url: str) -> str:
    host = urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")
    if not host:
        return "публичный источник"
    return host


def direct_intent_score(title: str, snippet: str, target_type: str) -> tuple[int, str, list[str]]:
    text = f"{title} {snippet}".lower()
    reasons: list[str] = ["найден прямой запрос на рынке"]
    score = 74
    if any(keyword in text for keyword in ["сниму", "арендую", "нужен", "нужна", "нужно", "ищу"]):
        score += 10
        reasons.append("в тексте есть активное намерение: сниму/ищу/нужен")
    if any(keyword in text for keyword in ["срочно", "в ближайшее время", "готов", "готовы", "до конца месяца"]):
        score += 8
        reasons.append("есть признак срочности")
    if any(keyword in text for keyword in DIRECT_OBJECT_KEYWORDS.get(target_type, [])):
        score += 6
        reasons.append(f"объект совпадает со сценарием: {target_label(target_type)}")
    return min(score, 94), "; ".join(reasons), reasons


def normalize_direct_intent_signal(item: dict[str, Any], scenario: dict[str, Any], city: str) -> dict[str, Any]:
    target_type = scenario["target_property_type"]
    title = first_value(item, "title", "name") or "Прямой запрос"
    snippet = first_value(item, "description", "snippet", "text")
    url = first_value(item, "url", "link")
    signal_date = signal_date_from_text(f"{title} {snippet}") or now_iso()
    signal_date_label = signal_date[:10] if signal_date else "дата не указана"
    source_label = source_label_from_url(url)
    score, reason, reasons = direct_intent_score(title, snippet, target_type)
    display_name = f"Запрос из {source_label}: {title[:90]}"
    company = {
        "name": display_name[:180],
        "inn": "",
        "city": city,
        "address": "",
        "category": CATEGORY_BY_TARGET.get(target_type, "services"),
        "category_label": "прямой запрос",
        "phone": "",
        "email": "",
        "website": "",
        "source_url": url,
        "source_provider": "Direct demand",
        "raw_payload": {
            "source": "google/apify",
            "signal_type": "direct_intent",
            "signal_title": title,
            "signal_text": snippet,
            "signal_url": url,
            "signal_date": signal_date,
            "signal_is_actionable": True,
            "signal_quality_reasons": reasons,
            "search_result": item,
        },
    }
    lead = {
        "score": score,
        "status": "new",
        "target_property_type": target_type,
        "target_deal_type": "покупка" if "куплю" in f"{title} {snippet}".lower() else "аренда",
        "ai_reason": f"{reason}. Сигнал: «{title}».",
        "suggested_offer": f"Проверить прямой запрос и подобрать {target_label(target_type)}. Не писать автоматически, сначала ручная проверка источника.",
        "source_provider": "Direct demand",
        "source_age_label": signal_date_label,
    }
    return {"company": company, "lead": lead}


def normalize_search_signal(item: dict[str, Any], scenario: dict[str, Any], city: str) -> dict[str, Any]:
    target_type = scenario["target_property_type"]
    title = first_value(item, "title", "name") or "Публичный сигнал"
    snippet = first_value(item, "description", "snippet", "text")
    url = first_value(item, "url", "link")
    company_name = company_name_from_signal(title, snippet)
    if not company_name:
        raise RuntimeError("Signal skipped: company name was not extracted")
    signal_date = signal_date_from_text(f"{title} {snippet}") or now_iso()
    signal_date_label = signal_date[:10] if signal_date else "дата не указана"
    actionable, quality_score, quality_reason, quality_reasons = signal_quality(title, snippet, target_type)
    company = {
        "name": company_name[:180],
        "inn": "",
        "city": city,
        "address": "",
        "category": CATEGORY_BY_TARGET.get(target_type, "services"),
        "category_label": "публичный сигнал",
        "phone": "",
        "email": "",
        "website": "",
        "source_url": url,
        "source_provider": "Signal search",
        "raw_payload": {
            "source": "google/apify",
            "signal_type": "search_result",
            "signal_title": title,
            "signal_text": snippet,
            "signal_url": url,
            "signal_date": signal_date,
            "company_extracted": True,
            "signal_is_actionable": actionable,
            "signal_quality_reasons": quality_reasons,
            "search_result": item,
        },
    }
    lead = {
        "score": quality_score,
        "status": "new",
        "target_property_type": target_type,
        "target_deal_type": "аренда",
        "ai_reason": f"{quality_reason}. Компания «{company_name}». Сигнал: «{title}».",
        "suggested_offer": f"Проверить потребность: {target_label(target_type)}. Повод: признак роста/управленческой потребности, а не просто любая вакансия.",
        "source_provider": "Signal search",
        "source_age_label": signal_date_label,
    }
    return {"company": company, "lead": lead}


def aggregate_signal_items(items: list[dict[str, Any]], target_type: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        company_name = str(item["company"].get("name") or "").strip().lower()
        if not company_name:
            continue
        groups.setdefault(company_name, []).append(item)

    result: list[dict[str, Any]] = []
    for group in groups.values():
        group.sort(key=lambda item: item["lead"].get("score", 0), reverse=True)
        best = group[0]
        raw_payload = best["company"].get("raw_payload") or {}
        is_actionable = bool(raw_payload.get("signal_is_actionable"))
        if len(group) >= 2:
            title = str(raw_payload.get("signal_title") or "")
            snippet = str(raw_payload.get("signal_text") or "")
            _actionable, score, reason, reasons = signal_quality(title, snippet, target_type, repeat_count=len(group))
            best["lead"]["score"] = max(best["lead"].get("score", 0), score)
            best["lead"]["ai_reason"] = f"{reason}. Компания повторяется в нескольких свежих сигналах, поэтому это уже не похоже на случайную одиночную вакансию."
            raw_payload["signal_is_actionable"] = True
            raw_payload["signal_quality_reasons"] = reasons
            raw_payload["related_signal_count"] = len(group)
            raw_payload["related_signal_titles"] = [
                (item["company"].get("raw_payload") or {}).get("signal_title")
                for item in group[:5]
            ]
            result.append(best)
            continue
        if is_actionable:
            result.append(best)
    return result


def api_leads() -> list[dict[str, Any]]:
    candidates = rest_request(
        "GET",
        "li_lead_candidates",
        "?select=*&order=score.desc,created_at.desc&limit=200",
    ) or []
    companies = rest_request("GET", "li_companies", "?select=*") or []
    company_by_id = {item["id"]: item for item in companies}
    result = []
    for candidate in candidates:
        company = company_by_id.get(candidate["company_id"], {})
        result.append({
            "id": candidate["id"],
            "company": company.get("name", "Без названия"),
            "inn": company.get("inn") or "",
            "category": company.get("category") or "services",
            "categoryLabel": company.get("category_label") or company.get("category") or "услуги",
            "city": company.get("city") or "Не указан",
            "score": candidate["score"],
            "status": candidate["status"],
            "manager": candidate.get("assigned_manager"),
            "reason": candidate.get("ai_reason") or "",
            "phone": company.get("phone") or "",
            "site": company.get("website") or "",
            "requestType": candidate.get("target_property_type") or "office",
            "requestLabel": request_label(candidate.get("target_property_type") or "office"),
            "deal": candidate.get("target_deal_type") or "аренда",
            "source": candidate.get("source_provider") or company.get("source_provider") or "Источник",
            "age": candidate.get("source_age_label") or "только что",
            "createdAt": candidate.get("created_at") or now_iso(),
            "signalTitle": (company.get("raw_payload") or {}).get("signal_title") or "",
            "signalText": (company.get("raw_payload") or {}).get("signal_text") or "",
            "signalUrl": (company.get("raw_payload") or {}).get("signal_url") or company.get("source_url") or "",
            "signalDate": (company.get("raw_payload") or {}).get("signal_date") or "",
        })
    return result


def api_scenarios() -> list[dict[str, Any]]:
    rows = rest_request("GET", "li_search_scenarios", "?select=*&order=created_at.asc") or []
    return [{
        "id": row["slug"],
        "title": row["title"],
        "description": row.get("description") or "",
        "meta": row.get("last_run_label") or "еще не запускали",
        "icon": SCENARIO_ICONS.get(row["slug"], "Building2"),
        "isActive": bool(row.get("is_active")),
    } for row in rows]


def api_metrics(leads: list[dict[str, Any]]) -> dict[str, Any]:
    hot = [lead for lead in leads if lead["score"] >= 80]
    in_work = [lead for lead in leads if lead["status"] == "in_work"]
    return {
        "new24h": len(leads),
        "hot": len(hot),
        "inWork": len(in_work),
        "offerConversion": "11.4%",
        "hotShare": f"{round(len(hot) / max(len(leads), 1) * 100)}% от потока",
    }


def scheduler_label() -> str:
    active_count = len(active_scenario_slugs())
    if not SCHEDULER_STATE["enabled"]:
        return "выключен"
    if active_count == 0:
        return f"online · активных сценариев 0 · каждые {SCHEDULER_STATE['interval_minutes']} мин"
    if SCHEDULER_STATE["running"]:
        return f"выполняется · {active_count} активн. · каждые {SCHEDULER_STATE['interval_minutes']} мин"
    if SCHEDULER_STATE["last_finished_at"]:
        return f"online · {active_count} активн. · каждые {SCHEDULER_STATE['interval_minutes']} мин · последний запуск {SCHEDULER_STATE['last_finished_at'][:16]}"
    return f"online · {active_count} активн. · каждые {SCHEDULER_STATE['interval_minutes']} мин"


def scheduler_state_for_api() -> dict[str, Any]:
    active_count = len(active_scenario_slugs())
    return {
        "enabled": bool(SCHEDULER_STATE["enabled"]),
        "intervalMinutes": int(SCHEDULER_STATE["interval_minutes"]),
        "lookbackDays": int(SCHEDULER_STATE["lookback_days"]),
        "activeScenarios": active_count,
        "running": bool(SCHEDULER_STATE["running"]),
        "lastStartedAt": SCHEDULER_STATE["last_started_at"],
        "lastFinishedAt": SCHEDULER_STATE["last_finished_at"],
        "lastCreated": int(SCHEDULER_STATE["last_created"]),
        "lastError": SCHEDULER_STATE["last_error"],
    }


def api_bootstrap() -> dict[str, Any]:
    leads = api_leads()
    hot_count = len([lead for lead in leads if lead["score"] >= 80])
    in_work_count = len([lead for lead in leads if lead["status"] == "in_work"])
    offer_count = len(rest_request("GET", "li_lead_actions", "?select=id&action_type=eq.offer") or [])
    return {
        "leads": leads,
        "scenarios": api_scenarios(),
        "metrics": api_metrics(leads),
        "funnel": [
            {"name": "Собрано", "value": len(leads), "color": "#bfdbfe"},
            {"name": "Score 80+", "value": hot_count, "color": "#93c5fd"},
            {"name": "В Telegram", "value": 0, "color": "#60a5fa"},
            {"name": "В работе", "value": in_work_count, "color": "#3b82f6"},
            {"name": "Офер", "value": offer_count, "color": "#2563eb"},
        ],
        "integrations": [
            {"name": "hh.ru signals", "state": "online", "online": True},
            {"name": "Apify enrichment", "state": "online" if APIFY_TOKEN and APIFY_ACTOR_ID else "нужен APIFY_TOKEN", "online": bool(APIFY_TOKEN and APIFY_ACTOR_ID)},
            {"name": "Supabase", "state": "online", "online": True},
            {"name": "Telegram bot · n8n", "state": "online", "online": True},
            {"name": "Автосбор по расписанию", "state": scheduler_label(), "online": bool(SCHEDULER_STATE["enabled"])},
            {"name": "AI scoring", "state": "rule scoring", "online": True},
            {"name": "Compliance (152-ФЗ)", "state": "только белые источники", "online": False},
        ],
        "scheduler": scheduler_state_for_api(),
    }


def record_action(candidate_id: str, action_type: str) -> dict[str, Any]:
    rest_request("POST", "li_lead_actions", payload={
        "candidate_id": candidate_id,
        "action_type": action_type,
        "actor": "manager",
        "payload": {},
    })
    if action_type == "work":
        rest_request("PATCH", "li_lead_candidates", f"?id=eq.{urllib.parse.quote(candidate_id)}", payload={
            "status": "in_work",
            "assigned_manager": "Менеджер",
            "updated_at": now_iso(),
        })
    elif action_type == "trash":
        rest_request("PATCH", "li_lead_candidates", f"?id=eq.{urllib.parse.quote(candidate_id)}", payload={
            "status": "archived",
            "archived_reason": "Помечено менеджером как мусор",
            "updated_at": now_iso(),
        })
    return {"ok": True, "bootstrap": api_bootstrap()}


def _run_scenario_unlocked(slug: str, include_bootstrap: bool = True, autocollect: bool = False) -> dict[str, Any]:
    rows = rest_request("GET", "li_search_scenarios", f"?select=*&slug=eq.{urllib.parse.quote(slug)}&limit=1") or []
    if not rows:
        raise RuntimeError("Scenario not found")
    scenario = rows[0]
    city = APIFY_DEFAULT_CITY
    limit = HH_DEFAULT_LIMIT
    lookback_days = AUTO_COLLECT_LOOKBACK_DAYS if autocollect else HH_DEFAULT_PERIOD_DAYS
    after_date = days_ago_date(lookback_days) if autocollect else ""
    run = rest_request("POST", "li_search_runs", payload={
        "scenario_id": scenario["id"],
        "city": city,
        "status": "running",
        "provider": "hh",
        "query": {"slug": slug, "city": city, "limit": limit, "mode": "autocollect" if autocollect else "manual", "lookback_days": lookback_days},
        "started_at": now_iso(),
    })[0]

    if slug in DIRECT_INTENT_SCENARIOS:
        rows = fetch_apify_serp_signals(scenario, city, limit, after_date=after_date)
        normalizer = lambda row, scenario_arg: normalize_direct_intent_signal(row, scenario_arg, city)
        provider = "apify-serp"
        rest_request("PATCH", "li_search_runs", f"?id=eq.{run['id']}", payload={
            "provider": provider,
            "query": {"slug": slug, "city": city, "limit": limit, "mode": "direct-intent", "lookback_days": lookback_days, "after": after_date},
        })
    else:
        try:
            rows = fetch_hh_signals(scenario, limit, period_days=lookback_days)
            normalizer = normalize_hh_vacancy
            provider = "hh"
        except Exception:
            rows = fetch_apify_serp_signals(scenario, city, limit, after_date=after_date)
            normalizer = lambda row, scenario_arg: normalize_search_signal(row, scenario_arg, city)
            provider = "apify-serp"
            rest_request("PATCH", "li_search_runs", f"?id=eq.{run['id']}", payload={
                "provider": provider,
                "query": {"slug": slug, "city": city, "limit": limit, "fallback": "apify-serp", "lookback_days": lookback_days, "after": after_date},
            })
    normalized_items = []
    for row in rows:
        try:
            normalized_items.append(normalizer(row, scenario))
        except Exception:
            continue
    if slug not in DIRECT_INTENT_SCENARIOS:
        normalized_items = aggregate_signal_items(normalized_items, scenario["target_property_type"])
    created = 0
    for normalized in normalized_items:
        if insert_company_lead(normalized, run["id"]):
            created += 1
    rest_request("PATCH", "li_search_runs", f"?id=eq.{run['id']}", payload={
        "status": "finished",
        "finished_at": now_iso(),
    })
    rest_request("PATCH", "li_search_scenarios", f"?id=eq.{scenario['id']}", payload={
        "last_run_label": f"последний запуск: только что · {created} сигналов",
    })
    result = {"ok": True, "created": created, "slug": slug}
    if include_bootstrap:
        result["bootstrap"] = api_bootstrap()
    return result


def run_scenario(slug: str, include_bootstrap: bool = True, autocollect: bool = False) -> dict[str, Any]:
    if not RUN_LOCK.acquire(blocking=False):
        raise RuntimeError("Сбор уже выполняется. Дождитесь завершения текущего запуска.")
    try:
        return _run_scenario_unlocked(slug, include_bootstrap, autocollect=autocollect)
    finally:
        RUN_LOCK.release()


def run_scenario_group(group: str) -> dict[str, Any]:
    rows = rest_request("GET", "li_search_scenarios", "?select=slug&order=created_at.asc") or []
    direct = group == "direct"
    slugs = [
        row["slug"]
        for row in rows
        if (row["slug"] in DIRECT_INTENT_SCENARIOS) == direct
    ]
    total_created = 0
    results = []
    for slug in slugs:
        result = run_scenario(slug, include_bootstrap=False)
        total_created += int(result.get("created") or 0)
        results.append(result)
    return {
        "ok": True,
        "group": group,
        "created": total_created,
        "results": results,
        "bootstrap": api_bootstrap(),
    }


def toggle_scenario(slug: str, active: bool) -> dict[str, Any]:
    rows = rest_request("GET", "li_search_scenarios", f"?select=*&slug=eq.{urllib.parse.quote(slug)}&limit=1") or []
    if not rows:
        raise RuntimeError("Scenario not found")
    rest_request("PATCH", "li_search_scenarios", f"?id=eq.{rows[0]['id']}", payload={
        "is_active": active,
        "last_run_label": rows[0].get("last_run_label") or "еще не запускали",
    })
    return {"ok": True, "bootstrap": api_bootstrap()}


def active_scenario_slugs() -> list[str]:
    rows = rest_request(
        "GET",
        "li_search_scenarios",
        "?select=slug&is_active=eq.true&order=created_at.asc",
    ) or []
    return [str(row["slug"]) for row in rows if row.get("slug")]


def run_autocollect_once() -> None:
    if not SCHEDULER_STATE["enabled"]:
        return
    slugs = active_scenario_slugs()
    SCHEDULER_STATE["running"] = True
    SCHEDULER_STATE["last_started_at"] = now_iso()
    SCHEDULER_STATE["last_error"] = ""
    total_created = 0
    try:
        for slug in slugs:
            try:
                result = run_scenario(slug, include_bootstrap=False, autocollect=True)
                total_created += int(result.get("created") or 0)
            except Exception as error:
                SCHEDULER_STATE["last_error"] = f"{slug}: {error}"
    finally:
        SCHEDULER_STATE["running"] = False
        SCHEDULER_STATE["last_finished_at"] = now_iso()
        SCHEDULER_STATE["last_created"] = total_created


def scheduler_loop() -> None:
    if AUTO_COLLECT_START_DELAY_SECONDS > 0:
        time.sleep(AUTO_COLLECT_START_DELAY_SECONDS)
    while True:
        try:
            run_autocollect_once()
        except Exception as error:
            SCHEDULER_STATE["running"] = False
            SCHEDULER_STATE["last_error"] = str(error)
            SCHEDULER_STATE["last_finished_at"] = now_iso()
        time.sleep(max(60, AUTO_COLLECT_INTERVAL_MINUTES * 60))


def start_scheduler() -> None:
    if not AUTO_COLLECT_ENABLED:
        return
    thread = threading.Thread(target=scheduler_loop, name="lead-autocollect", daemon=True)
    thread.start()


def import_companies(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload.get("companies") or []
    if not isinstance(rows, list):
        raise RuntimeError("companies должен быть массивом")
    created = 0
    scenario = {"target_property_type": payload.get("target_property_type") or "office"}
    city = payload.get("city") or APIFY_DEFAULT_CITY
    for row in rows[:500]:
        if not isinstance(row, dict):
            continue
        normalized = normalize_apify_item(row, scenario, city)
        insert_company_lead(normalized)
        created += 1
    return {"ok": True, "created": created, "bootstrap": api_bootstrap()}


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: Any) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    if length <= 0:
        return {}
    return json.loads(handler.rfile.read(length).decode("utf-8"))


def content_type(path: Path) -> str:
    if path.suffix == ".html":
        return "text/html; charset=utf-8"
    if path.suffix == ".js":
        return "application/javascript; charset=utf-8"
    if path.suffix == ".css":
        return "text/css; charset=utf-8"
    if path.suffix == ".svg":
        return "image/svg+xml"
    return "application/octet-stream"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/health":
            json_response(self, 200, {
                "status": "ok",
                "service": "lead-intelligence",
                "scheduler": scheduler_state_for_api(),
            })
            return
        if parsed.path == "/api/bootstrap":
            try:
                json_response(self, 200, api_bootstrap())
            except Exception as error:
                json_response(self, 500, {"error": str(error)})
            return
        self.serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        try:
            if parsed.path == "/api/scenarios/run-group":
                payload = read_json(self)
                group = "direct" if payload.get("group") == "direct" else "signals"
                json_response(self, 200, run_scenario_group(group))
                return
            if parsed.path.startswith("/api/leads/") and parsed.path.endswith("/action"):
                candidate_id = parsed.path.split("/")[3]
                payload = read_json(self)
                json_response(self, 200, record_action(candidate_id, payload.get("action", "note")))
                return
            if parsed.path.startswith("/api/scenarios/") and parsed.path.endswith("/run"):
                slug = parsed.path.split("/")[3]
                json_response(self, 200, run_scenario(slug))
                return
            if parsed.path.startswith("/api/scenarios/") and parsed.path.endswith("/toggle"):
                slug = parsed.path.split("/")[3]
                payload = read_json(self)
                json_response(self, 200, toggle_scenario(slug, bool(payload.get("active"))))
                return
            if parsed.path == "/api/import/companies":
                json_response(self, 200, import_companies(read_json(self)))
                return
            json_response(self, 404, {"error": "Not found"})
        except Exception as error:
            json_response(self, 500, {"error": str(error)})

    def serve_static(self, url_path: str) -> None:
        if url_path in {"", "/"}:
            file_path = STATIC_DIR / "index.html"
        else:
            relative = Path(urllib.parse.unquote(url_path.lstrip("/")))
            file_path = (STATIC_DIR / relative).resolve()
            if STATIC_DIR.resolve() not in file_path.parents and file_path != STATIC_DIR.resolve():
                self.send_error(403)
                return
            if not file_path.exists():
                file_path = STATIC_DIR / "index.html"
        if not file_path.exists():
            self.send_error(404)
            return
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type(file_path))
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main() -> None:
    start_scheduler()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Lead Intelligence listening on :{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
