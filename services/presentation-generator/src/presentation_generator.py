#!/usr/bin/env python3
import hashlib
import html
import json
import mimetypes
import os
import re
import shutil
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional, Union
from urllib.parse import unquote, urlparse


PORT = int(os.environ.get("PORT", "8090"))
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://45.92.174.232").rstrip("/")
OUTPUT_DIR = Path(os.environ.get("PRESENTATION_OUTPUT_DIR", "/data/generated"))
ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-zа-я0-9]+", "-", value, flags=re.IGNORECASE).strip("-")
    return value[:80] or "property"


def money(value: Any, currency: str = "RUB") -> str:
    if value in (None, ""):
        return "по запросу"
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return str(value)
    suffix = "₽" if currency == "RUB" else currency
    return f"{amount:,.0f}".replace(",", " ") + f" {suffix}"


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def strip_html(value: Any) -> str:
    value = re.sub(r"<[^>]+>", " ", str(value or ""))
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def yes(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "да", "y"}


def compact(items: list[tuple[str, Any]]) -> list[tuple[str, str]]:
    result = []
    for label, value in items:
        if value in (None, "", [], {}, "0", 0):
            continue
        result.append((label, str(value)))
    return result


def first_scalar(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}, "0", 0):
            return value
    return ""


def number_or_none(value: Any) -> Optional[Union[int, float]]:
    if value in (None, ""):
        return None
    try:
        amount = float(str(value).replace(" ", "").replace(",", "."))
    except ValueError:
        return None
    return int(amount) if amount.is_integer() else amount


def period_code(value: Any) -> str:
    text = str(value or "").lower()
    if "год" in text or text == "year":
        return "year"
    if "сут" in text or "день" in text or text == "day":
        return "day"
    if "мес" in text or text == "month":
        return "month"
    return text


def zero_blank(value: Any) -> Any:
    return "" if value in (None, "", "0", 0) else value


def category_code(value: Any, segment: Any) -> str:
    text = f"{value or ''} {segment or ''}".lower()
    if "коммер" in text or "commercial" in text:
        return "commercial"
    return "residential"


def deal_code(value: Any) -> str:
    text = str(value or "").lower()
    if "аренд" in text or "rent" in text:
        return "rent"
    if "прод" in text or "sale" in text or "sell" in text:
        return "sale"
    return text or "sale"


def presentation_data(data: dict[str, Any]) -> dict[str, Any]:
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    result = {}
    for key, value in meta.items():
        if key.startswith("property_"):
            result[key.removeprefix("property_")] = value

    result.update({
        "title": data.get("title"),
        "description": strip_html(data.get("description")),
        "category": category_code(data.get("category"), data.get("segment")),
        "property_type": deal_code(data.get("deal_type") or data.get("property_type")),
        "commercial_type": data.get("commercial_type"),
        "source_url": data.get("source_url"),
        "quickdeal_id": data.get("quickdeal_id") or data.get("external_id"),
        "internal_id": data.get("internal_id"),
        "published_at": data.get("published_at"),
        "updated_at": data.get("updated_at"),
        "price": number_or_none(data.get("price")),
        "currency": data.get("currency") or "RUB",
        "price_period": period_code(data.get("price_period")),
        "price_unit": data.get("price_unit"),
        "commission": zero_blank(data.get("commission")),
        "prepayment": zero_blank(data.get("prepayment")),
        "security_payment": zero_blank(data.get("security_payment")),
        "area_m2": number_or_none(data.get("area_m2")),
        "area_unit": data.get("area_unit") or "м²",
        "living_space": number_or_none(data.get("living_space")),
        "kitchen_space": number_or_none(data.get("kitchen_space")),
        "rooms": number_or_none(data.get("rooms")) if data.get("segment") == "residential" else None,
        "floor": number_or_none(data.get("floor")),
        "floors_total": number_or_none(data.get("floors_total")),
        "ceiling_height": number_or_none(data.get("ceiling_height")),
        "city": data.get("city"),
        "region": data.get("region"),
        "district": data.get("district"),
        "sub_locality_name": first_scalar(meta.get("property_sub_locality_name")),
        "address": data.get("address"),
        "full_address": data.get("address"),
        "latitude": number_or_none(data.get("latitude")),
        "longitude": number_or_none(data.get("longitude")),
        "photos": data.get("photos") or [],
        "video_review": first_scalar(data.get("video_review")),
        "virtual_tour": first_scalar(data.get("virtual_tour")),
        "renovation": data.get("renovation"),
        "quality": first_scalar(meta.get("property_quality")),
        "building_type": data.get("building_type"),
        "commercial_building_type": first_scalar(meta.get("property_commercial_building_type")),
        "building_name": data.get("building_name"),
        "built_year": number_or_none(meta.get("property_built_year")),
        "cadastral_number": meta.get("property_cadastral_number"),
        "office_class": meta.get("property_office_class"),
        "parking": first_scalar(meta.get("property_parking"), meta.get("property_free_parking"), meta.get("property_parking_guest")),
        "parking_places": number_or_none(first_scalar(meta.get("property_parking_places"), meta.get("property_parking_guest_places"))),
        "security": yes(meta.get("property_security")) or yes(meta.get("property_has_hour_security")),
        "twenty_four_seven": yes(meta.get("property_twenty_four_seven")),
        "internet": first_scalar(meta.get("property_internet")),
        "air_conditioner": first_scalar(meta.get("property_air_conditioner")),
        "ventilation": first_scalar(meta.get("property_ventilation")),
        "fire_alarm": yes(meta.get("property_fire_alarm")),
        "electric_capacity": first_scalar(meta.get("property_electric_capacity")),
        "freight_elevator": yes(meta.get("property_freight_elevator")),
        "truck_entrance": yes(meta.get("property_truck_entrance")),
        "ramp": yes(meta.get("property_ramp")),
        "railway": yes(meta.get("property_railway")),
        "open_area": number_or_none(meta.get("property_open_area")),
        "responsible_storage": yes(meta.get("property_responsible_storage")),
        "service_three_pl": yes(meta.get("property_service_three_pl")),
        "water_supply": yes(meta.get("property_water_supply")),
        "gas_supply": yes(meta.get("property_gas_supply")),
        "sewerage_supply": yes(meta.get("property_sewerage_supply")),
        "heating_supply": yes(meta.get("property_heating_supply")),
        "electricity_supply": yes(meta.get("property_electricity_supply")),
        "manager": data.get("manager") or {},
        "features": data.get("features") or [],
    })

    metro = []
    for item in data.get("metro") or []:
        if isinstance(item, dict):
            metro.append({
                "name": item.get("name"),
                "walk_min": number_or_none(first_scalar(item.get("walk_min"), item.get("time_on_foot"), item.get("time-on-foot"))),
                "transport_min": number_or_none(first_scalar(item.get("transport_min"), item.get("time_on_transport"), item.get("time-on-transport"))),
                "line": item.get("line") or "#2a9d8f",
            })
    result["metro"] = metro
    return {key: value for key, value in result.items() if value not in (None, "")}


def render_design_html(title: str) -> str:
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{esc(title)} · Office</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Fraunces:wght@400;500;600&family=Inter:wght@300;400;500;600&family=Manrope:wght@300;400;500;600&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css">
</head>
<body>
<div id="root"></div>
<script src="https://unpkg.com/react@18.3.1/umd/react.development.js" crossorigin="anonymous"></script>
<script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js" crossorigin="anonymous"></script>
<script src="https://unpkg.com/@babel/standalone@7.29.0/babel.min.js" crossorigin="anonymous"></script>
<script src="data.js"></script>
<script type="text/babel" src="tweaks-panel.jsx"></script>
<script type="text/babel" src="app.jsx"></script>
</body>
</html>"""


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("property") or payload
    meta = raw.get("meta") if isinstance(raw.get("meta"), dict) else {}
    photos = raw.get("photos") or raw.get("images") or raw.get("media") or []
    normalized_photos = []
    for item in photos:
        if isinstance(item, str):
            normalized_photos.append({"url": item, "caption": ""})
        elif isinstance(item, dict) and item.get("url"):
            normalized_photos.append({
                "url": item.get("url"),
                "caption": item.get("caption") or item.get("alt") or item.get("tag") or "",
                "is_plan": item.get("is_plan") or item.get("is_floor_plan") or item.get("is_scheme"),
            })

    features = raw.get("features") or raw.get("advantages") or []
    if isinstance(features, str):
        features = [part.strip() for part in re.split(r"[\n;]+", features) if part.strip()]

    manager = raw.get("manager") or {}
    if not manager:
        manager = {
            "name": meta.get("property_agent_name"),
            "phone": meta.get("property_agent_phone_single"),
            "email": meta.get("property_agent_email"),
            "organization": meta.get("property_agent_organization"),
        }

    return {
        "external_id": raw.get("id") or raw.get("external_id") or raw.get("wordpress_id"),
        "title": raw.get("title") or raw.get("name") or "Объект недвижимости",
        "segment": raw.get("segment") or raw.get("property_segment") or "commercial",
        "deal_type": raw.get("deal_type") or raw.get("type") or "sale",
        "city": raw.get("city") or "",
        "address": raw.get("address") or raw.get("location") or "",
        "district": raw.get("district") or meta.get("property_sub_locality_name") or meta.get("property_district") or "",
        "region": raw.get("region") or meta.get("property_region") or "",
        "latitude": raw.get("latitude") or meta.get("property_latitude") or "",
        "longitude": raw.get("longitude") or meta.get("property_longitude") or "",
        "area_m2": raw.get("area_m2") or raw.get("area") or "",
        "area_unit": raw.get("area_unit") or "",
        "rooms": raw.get("rooms") or "",
        "floor": raw.get("floor") or "",
        "floors_total": raw.get("floors_total") or "",
        "price": raw.get("price") or raw.get("cost") or "",
        "currency": raw.get("currency") or "RUB",
        "price_period": raw.get("price_period") or "",
        "price_unit": raw.get("price_unit") or "",
        "category": raw.get("category") or "",
        "property_type": raw.get("property_type") or "",
        "commercial_type": raw.get("commercial_type") or "",
        "building_type": raw.get("building_type") or "",
        "building_name": raw.get("building_name") or "",
        "renovation": raw.get("renovation") or "",
        "ceiling_height": raw.get("ceiling_height") or "",
        "description": strip_html(raw.get("description") or raw.get("content") or ""),
        "features": features[:8],
        "photos": normalized_photos[:18],
        "metro": raw.get("metro") or [],
        "railway_station": raw.get("railway_station") or [],
        "purpose": raw.get("purpose") or [],
        "purpose_warehouse": raw.get("purpose_warehouse") or [],
        "video_review": raw.get("video_review") or [],
        "virtual_tour": raw.get("virtual_tour") or [],
        "discount": raw.get("discount") or [],
        "manager": manager,
        "published_at": raw.get("published_at") or "",
        "updated_at": raw.get("updated_at") or "",
        "source_url": raw.get("source_url") or "",
        "meta": meta,
    }


def presentation_id(data: dict[str, Any]) -> str:
    base = f"{data.get('external_id') or ''}:{data.get('title')}:{datetime.now(timezone.utc).date().isoformat()}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]


FIELD_LABELS = {
    "property_qd_id": "QuickDeal ID",
    "property_internal_id": "Внутренний ID",
    "property_type": "Тип сделки",
    "property_category": "Категория",
    "property_price": "Цена",
    "property_currency": "Валюта",
    "property_price_period": "Период цены",
    "property_area": "Площадь",
    "property_area_unit": "Ед. площади",
    "property_floor": "Этаж",
    "property_floors_total": "Этажей",
    "property_full_address": "Полный адрес",
    "property_address": "Адрес",
    "property_region": "Регион",
    "property_locality_name": "Город",
    "property_sub_locality_name": "Район",
    "property_latitude": "Широта",
    "property_longitude": "Долгота",
    "property_agent_name": "Агент",
    "property_agent_phone_single": "Телефон агента",
    "property_agent_email": "Email агента",
    "property_agent_organization": "Организация",
    "property_commercial_type": "Тип коммерции",
    "property_renovation": "Ремонт",
    "property_quality": "Качество",
    "property_images": "Изображения",
    "property_metro": "Метро",
    "property_raw_data": "Сырые данные",
}


def field_label(key: str) -> str:
    if key in FIELD_LABELS:
        return FIELD_LABELS[key]
    key = key.replace("property_", "").replace("_", " ")
    return key[:1].upper() + key[1:]


def display_value(value: Any) -> str:
    if isinstance(value, bool):
        return "Да" if value else "Нет"
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict):
                parts.append(", ".join(f"{field_label(str(k))}: {display_value(v)}" for k, v in item.items() if v not in ("", None, [], {}, "0", 0, False)))
            elif item not in ("", None, [], {}, "0", 0, False):
                parts.append(str(item))
        return "; ".join(part for part in parts if part)
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            if item in ("", None, [], {}, "0", 0, False):
                continue
            parts.append(f"{field_label(str(key))}: {display_value(item)}")
        return "; ".join(parts)
    return strip_html(value)


def is_present(value: Any) -> bool:
    return display_value(value) not in ("", "0", "Нет")


def metric_cards(data: dict[str, Any]) -> list[tuple[str, str, str]]:
    floor = ""
    if data.get("floor") and data.get("floors_total"):
        floor = f"{data.get('floor')}/{data.get('floors_total')}"
    elif data.get("floor"):
        floor = str(data.get("floor"))
    return [
        ("Площадь", str(data.get("area_m2") or "—"), data.get("area_unit") or "м²"),
        ("Стоимость", money(data.get("price"), data.get("currency")), data.get("price_period") or "условия"),
        ("Этаж", floor or "—", "расположение"),
        ("Тип", str(data.get("property_type") or data.get("commercial_type") or data.get("deal_type") or "—"), str(data.get("category") or data.get("segment") or "")),
    ]


def fact_groups(data: dict[str, Any]) -> dict[str, list[tuple[str, Any]]]:
    manager = data.get("manager") or {}
    meta = data.get("meta") or {}
    return {
        "Сделка": [
            ("Тип сделки", data.get("property_type") or data.get("deal_type")),
            ("Цена", money(data.get("price"), data.get("currency")) if data.get("price") else ""),
            ("Период", data.get("price_period")),
            ("Комиссия", data.get("commission")),
            ("Предоплата", data.get("prepayment")),
            ("Обеспечительный платеж", data.get("security_payment")),
        ],
        "Объект": [
            ("Категория", data.get("category")),
            ("Коммерческий тип", data.get("commercial_type")),
            ("Площадь", f"{data.get('area_m2')} {data.get('area_unit') or 'м²'}" if data.get("area_m2") else ""),
            ("Этаж", f"{data.get('floor')}/{data.get('floors_total')}" if data.get("floor") and data.get("floors_total") else data.get("floor")),
            ("Комнаты", data.get("rooms")),
            ("Ремонт", data.get("renovation")),
            ("Потолки", data.get("ceiling_height")),
            ("Качество", meta.get("property_quality")),
        ],
        "Локация": [
            ("Адрес", data.get("address")),
            ("Район", data.get("district")),
            ("Регион", data.get("region")),
            ("Координаты", f"{data.get('latitude')}, {data.get('longitude')}" if data.get("latitude") and data.get("longitude") else ""),
        ],
        "Контакт": [
            ("Менеджер", manager.get("name")),
            ("Телефон", manager.get("phone")),
            ("Email", manager.get("email")),
            ("Организация", manager.get("organization")),
        ],
    }


def render_fact_group(title: str, items: list[tuple[str, Any]]) -> str:
    rows = [(label, display_value(value)) for label, value in items if is_present(value)]
    if not rows:
        return ""
    body = "\n".join(f'<div class="fact"><span>{esc(label)}</span><strong>{esc(value)}</strong></div>' for label, value in rows)
    return f'<article class="fact-group reveal"><h3>{esc(title)}</h3>{body}</article>'


def render_all_fields(data: dict[str, Any]) -> str:
    rows = []
    skip = {"property_raw_data"}
    for key, value in sorted((data.get("meta") or {}).items()):
        if key in skip or not is_present(value):
            continue
        rendered = display_value(value)
        if not rendered:
            continue
        rows.append(f'<tr><th>{esc(field_label(key))}</th><td>{esc(rendered)}</td></tr>')
    for key in ("purpose", "purpose_warehouse", "metro", "railway_station", "video_review", "virtual_tour", "discount"):
        value = data.get(key)
        if is_present(value):
            rows.append(f'<tr><th>{esc(field_label(key))}</th><td>{esc(display_value(value))}</td></tr>')
    if not rows:
        return ""
    return f'<section id="fields"><div class="section-head"><p>Все поля</p><h2>Полная карта объекта</h2></div><div class="data-table reveal"><table>{"".join(rows)}</table></div></section>'


def render_html(data: dict[str, Any]) -> str:
    title = esc(data["title"])
    address = data.get("address") or ", ".join(part for part in [data.get("city"), data.get("district")] if part)
    cover = data["photos"][0]["url"] if data["photos"] else "https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=1800&q=85"
    gallery = data["photos"][:12]
    manager = data.get("manager") or {}
    features = data.get("features") or []
    generated_at = datetime.now().strftime("%d.%m.%Y %H:%M")
    deal_label = {"sale": "Продажа", "rent": "Аренда"}.get(str(data.get("deal_type") or "").lower(), data.get("deal_type") or "Сделка")
    segment_label = {"commercial": "Коммерческая недвижимость", "residential": "Жилая недвижимость"}.get(str(data.get("segment") or ""), data.get("segment") or "Недвижимость")
    commercial_types = {
        "office": "Офис",
        "warehouse": "Склад",
        "retail": "Торговое помещение",
        "free purpose": "Свободное назначение",
        "manufacturing": "Производство",
    }
    object_type = commercial_types.get(str(data.get("commercial_type") or "").lower(), data.get("commercial_type") or data.get("category") or "Объект")
    period = f" / {data.get('price_period')}" if data.get("price_period") else ""
    price_label = money(data.get("price"), data.get("currency")) + period if data.get("price") not in (None, "") else "по запросу"

    stats = compact([
        ("Стоимость", price_label),
        ("Площадь", f"{data.get('area_m2')} м²" if data.get("area_m2") else ""),
        ("Этаж", f"{data.get('floor')}/{data.get('floors_total')}" if data.get("floor") and data.get("floors_total") else data.get("floor")),
        ("Тип", object_type),
        ("Сделка", deal_label),
        ("Ремонт", data.get("renovation")),
    ])
    details = compact([
        ("Адрес", address),
        ("Район", data.get("district")),
        ("Регион", data.get("region")),
        ("Метро", ", ".join(item.get("name", "") for item in data.get("metro", []) if isinstance(item, dict) and item.get("name"))),
        ("Площадь", f"{data.get('area_m2')} {data.get('area_unit') or 'м²'}" if data.get("area_m2") else ""),
        ("Этажность", f"{data.get('floor')} из {data.get('floors_total')}" if data.get("floor") and data.get("floors_total") else ""),
        ("Комиссия", money(data.get("commission"), data.get("currency")) if data.get("commission") not in (None, "", "0", 0) else ""),
        ("Обеспечительный платеж", money(data.get("security_payment"), data.get("currency")) if data.get("security_payment") not in (None, "", "0", 0) else ""),
        ("Высота потолка", f"{data.get('ceiling_height')} м" if data.get("ceiling_height") not in (None, "", "0", 0) else ""),
        ("ID QuickDeal", data.get("external_id")),
    ])
    raw_meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    tech_details = compact([
        ("Интернет", "Да" if yes(raw_meta.get("property_internet")) else ""),
        ("Парковка", "Да" if yes(raw_meta.get("property_parking")) or yes(raw_meta.get("property_parking_guest")) else ""),
        ("Охрана", "Да" if yes(raw_meta.get("property_security")) or yes(raw_meta.get("property_has_hour_security")) else ""),
        ("24/7", "Да" if yes(raw_meta.get("property_twenty_four_seven")) else ""),
        ("Кондиционер", "Да" if yes(raw_meta.get("property_air_conditioner")) else ""),
        ("Вентиляция", "Да" if yes(raw_meta.get("property_ventilation")) else ""),
        ("Пожарная сигнализация", "Да" if yes(raw_meta.get("property_fire_alarm")) else ""),
        ("Электрическая мощность", f"{raw_meta.get('property_electric_capacity')} кВт" if raw_meta.get("property_electric_capacity") not in (None, "", "0", 0) else ""),
    ])

    gallery_html = "\n".join(
        f'<figure class="photo photo-{index + 1}" style="--i:{index}"><img src="{esc(item["url"])}" alt="{esc(item.get("caption"))}"><figcaption>{esc(item.get("caption") or ("Планировка" if item.get("is_plan") else title))}</figcaption></figure>'
        for index, item in enumerate(gallery)
    )
    if not gallery_html:
        gallery_html = '<div class="empty">Фотографии пока не переданы</div>'

    features_html = "\n".join(f'<li style="--i:{index}"><span>{esc(item)}</span></li>' for index, item in enumerate(features))
    if not features_html:
        features_html = "<li><span>Данные объекта собраны автоматически</span></li><li><span>Презентация доступна по ссылке</span></li>"

    stats_html = "\n".join(f'<div class="metric" style="--i:{index}"><span>{esc(label)}</span><strong>{esc(value)}</strong></div>' for index, (label, value) in enumerate(stats[:6]))
    details_html = "\n".join(f"<tr><th>{esc(label)}</th><td>{esc(value)}</td></tr>" for label, value in details)
    tech_html = "\n".join(f'<div class="chip">{esc(label)}<strong>{esc(value)}</strong></div>' for label, value in tech_details)
    metro_html = "\n".join(
        f'<div class="metro-item"><strong>{esc(item.get("name"))}</strong><span>{esc(item.get("time_on_transport") or item.get("time-on-transport") or "")} мин. транспортом</span></div>'
        for item in data.get("metro", []) if isinstance(item, dict) and item.get("name")
    )
    coordinates = ", ".join(part for part in [data.get("latitude"), data.get("longitude")] if part)
    media_links = []
    for label, key in [("Видеообзор", "video_review"), ("Виртуальный тур", "virtual_tour")]:
        values = data.get(key) or []
        if isinstance(values, str):
            values = [values]
        for value in values:
            url = value.get("url") if isinstance(value, dict) else value
            if url:
                media_links.append(f'<a class="ghost-link" href="{esc(url)}" target="_blank" rel="noopener">{esc(label)}</a>')
    media_html = "\n".join(media_links)
    contact_bits = [manager.get("name"), manager.get("phone") or manager.get("telegram"), manager.get("email")]
    contact = " · ".join(str(bit) for bit in contact_bits if bit)
    full_fields_html = render_all_fields(data)

    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f4f6f3;
      --panel: #ffffff;
      --ink: #17201b;
      --muted: #657069;
      --line: #dde4dc;
      --accent: #b88332;
      --green: #174f43;
      --sage: #dfe9df;
      --black: #101511;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{ margin: 0; font-family: "Inter", "Manrope", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--ink); }}
    body::before {{ content:""; position: fixed; inset:0; pointer-events:none; background: linear-gradient(120deg, rgba(23,79,67,.08), transparent 35%, rgba(184,131,50,.08)); }}
    .topbar {{ position: sticky; top: 0; z-index: 20; display:flex; justify-content:space-between; align-items:center; gap:18px; padding: 14px clamp(18px, 4vw, 48px); background: rgba(244,246,243,.82); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(221,228,220,.82); }}
    .brand {{ font-weight: 900; color: var(--green); }}
    .nav {{ display:flex; gap:18px; flex-wrap:wrap; font-size:14px; }}
    .nav a {{ color: var(--muted); text-decoration:none; }}
    .hero {{ min-height: calc(100vh - 62px); display:grid; grid-template-columns:minmax(0,.86fr) minmax(460px,1.14fr); background: var(--black); color:#fff; overflow:hidden; }}
    .hero-copy {{ padding: clamp(28px, 6vw, 88px); display:flex; flex-direction:column; justify-content:center; gap:28px; position:relative; }}
    .kicker {{ display:flex; flex-wrap:wrap; gap:8px; }}
    .pill {{ display:inline-flex; align-items:center; min-height:30px; border:1px solid rgba(255,255,255,.18); border-radius:999px; padding:6px 12px; color:rgba(255,255,255,.78); font-size:12px; background:rgba(255,255,255,.07); }}
    h1 {{ margin:0; max-width:920px; font-size: clamp(40px, 6.1vw, 86px); line-height:.97; letter-spacing:0; animation: rise .7s ease both; }}
    .lead {{ max-width:760px; color:rgba(255,255,255,.72); font-size: clamp(17px, 1.5vw, 21px); line-height:1.62; animation: rise .7s ease .08s both; }}
    .hero-media {{ min-height:620px; position:relative; background:url("{esc(cover)}") center/cover; isolation:isolate; animation: reveal 1.1s ease both; }}
    .hero-media::before {{ content:""; position:absolute; inset:0; background:linear-gradient(90deg, rgba(16,21,17,.72), rgba(16,21,17,.08) 45%, rgba(16,21,17,.18)); z-index:1; }}
    .metrics {{ display:grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap:10px; animation: rise .7s ease .15s both; }}
    .metric {{ min-height:96px; padding:16px; border:1px solid rgba(255,255,255,.16); border-radius:8px; background:rgba(255,255,255,.08); backdrop-filter:blur(14px); }}
    .metric span {{ display:block; color:rgba(255,255,255,.56); font-size:12px; margin-bottom:10px; }}
    .metric strong {{ display:block; font-size:clamp(20px, 2.1vw, 30px); line-height:1.05; overflow-wrap:anywhere; }}
    section {{ max-width:1240px; margin:0 auto; padding:72px clamp(18px, 4vw, 42px); position:relative; }}
    .section-head {{ display:grid; grid-template-columns:minmax(0,.72fr) minmax(280px,.28fr); gap:28px; align-items:end; margin-bottom:28px; }}
    h2 {{ margin:0; font-size:clamp(30px, 4vw, 58px); line-height:1; letter-spacing:0; }}
    .note {{ color:var(--muted); line-height:1.6; }}
    .description {{ max-width:930px; font-size:20px; line-height:1.78; color:#38423c; }}
    .features {{ list-style:none; padding:0; margin:0; display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap:12px; }}
    .features li {{ min-height:126px; border:1px solid var(--line); border-radius:8px; background:var(--panel); padding:18px; display:flex; align-items:flex-end; animation: rise .7s ease calc(var(--i) * .06s) both; }}
    .features span {{ font-size:17px; line-height:1.35; }}
    .spec-grid {{ display:grid; grid-template-columns:minmax(0, .95fr) minmax(360px, .55fr); gap:14px; align-items:start; }}
    .spec-card, .contact-card {{ border:1px solid var(--line); border-radius:8px; background:rgba(255,255,255,.82); padding:24px; box-shadow:0 24px 70px rgba(26,39,32,.08); }}
    .data-table {{ border:1px solid var(--line); border-radius:8px; background:rgba(255,255,255,.86); padding:6px 24px; box-shadow:0 24px 70px rgba(26,39,32,.08); overflow:hidden; }}
    table {{ width:100%; border-collapse:collapse; }}
    th, td {{ padding:16px 0; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }}
    th {{ width:34%; color:var(--muted); font-weight:650; }}
    td {{ color:var(--ink); font-weight:720; }}
    .chips {{ display:flex; flex-wrap:wrap; gap:10px; }}
    .chip {{ display:inline-flex; gap:10px; align-items:center; border:1px solid var(--line); border-radius:999px; padding:10px 14px; background:#fff; color:var(--muted); }}
    .chip strong {{ color:var(--green); }}
    .gallery {{ display:grid; grid-template-columns:repeat(6,1fr); grid-auto-rows:150px; gap:12px; }}
    figure {{ margin:0; border-radius:8px; overflow:hidden; position:relative; background:#dfe4df; animation: rise .7s ease calc(var(--i) * .04s) both; }}
    .photo-1 {{ grid-column:span 3; grid-row:span 3; }}
    .photo-2 {{ grid-column:span 3; grid-row:span 2; }}
    .photo-3, .photo-4, .photo-5, .photo-6 {{ grid-column:span 2; grid-row:span 2; }}
    figure img {{ width:100%; height:100%; object-fit:cover; display:block; transition:transform .7s ease; }}
    figure:hover img {{ transform:scale(1.045); }}
    figcaption {{ position:absolute; left:12px; bottom:12px; max-width:calc(100% - 24px); padding:8px 10px; border-radius:6px; background:rgba(16,21,17,.72); color:#fff; font-size:12px; opacity:0; transform:translateY(8px); transition:.25s ease; }}
    figure:hover figcaption {{ opacity:1; transform:translateY(0); }}
    .location-grid {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(320px,.45fr); gap:14px; }}
    .map-card {{ min-height:380px; border-radius:8px; border:1px solid var(--line); background:linear-gradient(135deg,#e4ebe4,#f9faf7); position:relative; overflow:hidden; }}
    .map-card::before {{ content:""; position:absolute; inset:28px; background:linear-gradient(90deg, transparent 48%, rgba(23,79,67,.16) 49%, rgba(23,79,67,.16) 51%, transparent 52%), linear-gradient(0deg, transparent 48%, rgba(184,131,50,.18) 49%, rgba(184,131,50,.18) 51%, transparent 52%); background-size:92px 92px; opacity:.7; }}
    .pin {{ position:absolute; left:50%; top:50%; width:22px; height:22px; border-radius:50%; background:var(--green); box-shadow:0 0 0 12px rgba(23,79,67,.14), 0 18px 44px rgba(23,79,67,.34); animation:pulse 2.4s ease infinite; }}
    .metro-item {{ display:flex; justify-content:space-between; gap:12px; padding:14px 0; border-bottom:1px solid var(--line); }}
    .ghost-link {{ display:inline-flex; text-decoration:none; color:var(--green); border:1px solid var(--line); border-radius:999px; padding:10px 14px; background:#fff; }}
    .contact-band {{ background:var(--black); color:#fff; }}
    .contact-inner {{ max-width:1240px; margin:0 auto; padding:64px clamp(18px,4vw,42px); display:grid; grid-template-columns:minmax(0,1fr) minmax(320px,.42fr); gap:28px; align-items:end; }}
    .contact-inner h2 {{ color:#fff; }}
    .contact-line {{ color:rgba(255,255,255,.72); line-height:1.7; }}
    .empty {{ border:1px dashed var(--line); border-radius:8px; padding:28px; color:var(--muted); background:#fff; }}
    @keyframes rise {{ from {{ opacity:0; transform:translateY(22px); }} to {{ opacity:1; transform:translateY(0); }} }}
    @keyframes reveal {{ from {{ opacity:0; transform:scale(1.025); }} to {{ opacity:1; transform:scale(1); }} }}
    @keyframes pulse {{ 0%,100% {{ transform:translate(-50%,-50%) scale(1); }} 50% {{ transform:translate(-50%,-50%) scale(1.12); }} }}
    @media (max-width: 900px) {{
      .topbar {{ position:static; }}
      .hero, .section-head, .spec-grid, .location-grid, .contact-inner {{ grid-template-columns:1fr; }}
      .hero-media {{ min-height:390px; order:-1; }}
      .metrics, .features {{ grid-template-columns:1fr; }}
      .gallery {{ grid-template-columns:1fr; grid-auto-rows:260px; }}
      .photo-1, .photo-2, .photo-3, .photo-4, .photo-5, .photo-6 {{ grid-column:auto; grid-row:auto; }}
      th, td {{ display:block; width:100%; padding:8px 0; }}
    }}
  </style>
</head>
<body>
  <header class="topbar">
    <div class="brand">NOVACTIV</div>
    <nav class="nav">
      <a href="#overview">Описание</a>
      <a href="#specs">Параметры</a>
      <a href="#gallery">Галерея</a>
      <a href="#location">Локация</a>
      <a href="#fields">Все поля</a>
    </nav>
  </header>
  <main>
    <div class="hero" id="top">
      <div class="hero-copy">
        <div class="kicker"><span class="pill">{esc(deal_label)}</span><span class="pill">{esc(segment_label)}</span><span class="pill">{esc(object_type)}</span></div>
        <h1>{title}</h1>
        <div class="lead">{esc(address) or "Адрес уточняется"}</div>
        <div class="metrics">{stats_html}</div>
      </div>
      <div class="hero-media"></div>
    </div>
    <section id="overview">
      <div class="section-head">
        <h2>Объект в фокусе</h2>
        <div class="note">Данные подтянуты из WordPress и QuickDeal. Блоки презентации адаптируются под заполненные поля объекта.</div>
      </div>
      <div class="description">{esc(data.get("description") or "Описание объекта будет подтянуто из WordPress.")}</div>
    </section>
    <section>
      <div class="section-head">
        <h2>Ключевые преимущества</h2>
        <div class="note">Короткие тезисы для первого просмотра клиентом.</div>
      </div>
      <ul class="features">{features_html}</ul>
    </section>
    <section id="specs">
      <div class="section-head">
        <h2>Параметры сделки</h2>
        <div class="note">Главные характеристики, финансовые условия и технические опции.</div>
      </div>
      <div class="spec-grid">
        <div class="spec-card"><table>{details_html}</table></div>
        <div class="contact-card">
          <h3>Дополнительно</h3>
          <div class="chips">{tech_html or '<span class="note">Дополнительные параметры не заполнены</span>'}</div>
          <div style="margin-top:18px; display:flex; gap:10px; flex-wrap:wrap;">{media_html}</div>
        </div>
      </div>
    </section>
    <section id="gallery">
      <div class="section-head">
        <h2>Визуальный обзор</h2>
        <div class="note">Фото автоматически раскладываются в адаптивную галерею.</div>
      </div>
      <div class="gallery">{gallery_html}</div>
    </section>
    <section id="location">
      <div class="section-head">
        <h2>Локация</h2>
        <div class="note">{esc(coordinates) if coordinates else "Координаты появятся, если они переданы в объекте."}</div>
      </div>
      <div class="location-grid">
        <div class="map-card"><div class="pin"></div></div>
        <div class="spec-card">
          <h3>Адрес</h3>
          <p class="note">{esc(address) or "Уточняется"}</p>
          {metro_html}
        </div>
      </div>
    </section>
    {full_fields_html}
    <div class="contact-band">
      <div class="contact-inner">
        <div>
          <h2>Готово к обсуждению</h2>
          <div class="contact-line">Создано: {esc(generated_at)}<br>{esc(contact or "Office")}</div>
        </div>
        <div class="contact-line">Источник: {esc(data.get("source_url") or "WordPress")}<br>Office</div>
      </div>
    </div>
  </main>
</body>
</html>"""


def save_presentation(payload: dict[str, Any]) -> dict[str, Any]:
    data = normalize_payload(payload)
    pid = presentation_id(data)
    slug = f"{slugify(data['title'])}-{pid}"
    directory = OUTPUT_DIR / slug
    directory.mkdir(parents=True, exist_ok=True)
    for asset_name in ("styles.css", "app.jsx", "tweaks-panel.jsx"):
        shutil.copyfile(ASSETS_DIR / asset_name, directory / asset_name)
    design_data = presentation_data(data)
    data_js = "window.PROPERTIES = " + json.dumps({"generated": design_data}, ensure_ascii=False, indent=2) + ";\n"
    (directory / "data.js").write_text(data_js, encoding="utf-8")
    (directory / "index.html").write_text(render_design_html(data["title"]), encoding="utf-8")
    return {
        "presentation_id": pid,
        "slug": slug,
        "url": f"{PUBLIC_BASE_URL}/presentations/generated/{slug}/",
        "status": "ready",
    }


def json_response(handler: BaseHTTPRequestHandler, status: int, body: dict[str, Any]) -> None:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = unquote(urlparse(self.path).path)
        if path in ("/", "/presentations", "/presentations/"):
            json_response(self, 200, {"status": "ok", "service": "presentation-generator"})
            return
        prefix = "/presentations/generated/"
        if path.startswith(prefix):
            relative = path[len(prefix):].strip("/") or "index.html"
            if "/" not in relative:
                relative = f"{relative}/index.html"
            file_path = (OUTPUT_DIR / relative).resolve()
            if OUTPUT_DIR.resolve() not in file_path.parents and file_path != OUTPUT_DIR.resolve():
                json_response(self, 403, {"error": "Forbidden"})
                return
            if file_path.is_dir():
                file_path = file_path / "index.html"
            if not file_path.exists():
                json_response(self, 404, {"error": "Not found"})
                return
            data = file_path.read_bytes()
            content_type, _ = mimetypes.guess_type(str(file_path))
            if file_path.suffix == ".jsx":
                content_type = "text/babel; charset=utf-8"
            elif file_path.suffix == ".js":
                content_type = "application/javascript; charset=utf-8"
            elif file_path.suffix == ".css":
                content_type = "text/css; charset=utf-8"
            elif file_path.suffix == ".html":
                content_type = "text/html; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", content_type or "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        json_response(self, 404, {"error": "Not found"})

    def do_POST(self) -> None:
        try:
            path = urlparse(self.path).path
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
            if path.endswith("/presentations/api/generate"):
                result = save_presentation(payload)
                json_response(self, 201, result)
                return
            json_response(self, 404, {"error": "Not found"})
        except Exception as error:
            json_response(self, 500, {"error": str(error)})


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
