#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Optional


PHONE_RE = re.compile(r"(?:\+7|8|7)?[\s\-\(\)]*\d{3}[\s\-\(\)]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}")
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b", re.IGNORECASE)
TELEGRAM_RE = re.compile(r"(?:https?://t\.me/|t\.me/|(?<![A-Za-z0-9._%+\-])@)([A-Za-z0-9_]{5,32})")
VK_RE = re.compile(r"https?://(?:www\.)?vk\.com/[A-Za-z0-9_.]+", re.IGNORECASE)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_phone(value: str) -> Optional[str]:
    digits = re.sub(r"\D+", "", value)
    if len(digits) == 11 and digits[0] in ("7", "8"):
        return "+7" + digits[1:]
    if len(digits) == 10:
        return "+7" + digits
    return None


def normalize_email(value: str) -> str:
    return value.strip().lower()


def normalize_telegram(value: str) -> str:
    username = value.strip().lstrip("@")
    username = re.sub(r"^https?://t\.me/", "", username, flags=re.IGNORECASE)
    username = re.sub(r"^t\.me/", "", username, flags=re.IGNORECASE)
    return username.lower()


def normalize_vk(value: str) -> str:
    return value.strip().rstrip("/").lower()


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def extract_contacts(text: str) -> dict[str, list[str]]:
    phones = sorted({phone for phone in (normalize_phone(m.group(0)) for m in PHONE_RE.finditer(text)) if phone})
    emails = sorted({normalize_email(m.group(0)) for m in EMAIL_RE.finditer(text)})
    telegram = sorted({normalize_telegram(m.group(1)) for m in TELEGRAM_RE.finditer(text)})
    vk = sorted({normalize_vk(m.group(0)) for m in VK_RE.finditer(text)})
    return {
        "phones": phones,
        "emails": emails,
        "telegram_usernames": telegram,
        "vk_urls": vk,
    }


def build_candidate(args: argparse.Namespace) -> dict[str, Any]:
    contacts = extract_contacts(args.text)
    source_key = args.external_id or args.source_url or args.text[:120]
    return {
        "source_type": args.source_type,
        "source_name": args.source_name,
        "source_url": args.source_url,
        "external_id": args.external_id,
        "source_url_hash": stable_hash(args.source_url) if args.source_url else None,
        "idempotency_key": stable_hash(f"{args.source_type}:{args.source_name}:{source_key}"),
        "collected_at": utc_now(),
        "published_at": args.published_at,
        "raw_text": args.text,
        "parser_name": "manual_text_v1",
        "parser_version": "0.1.0",
        "extraction_confidence": 0.75 if any(contacts.values()) else 0.0,
        "contact_candidates": contacts,
        "legal_basis_note": args.legal_basis_note,
        "dry_run": args.dry_run,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a lead candidate from source text.")
    parser.add_argument("--source-type", required=True)
    parser.add_argument("--source-name", required=True)
    parser.add_argument("--source-url")
    parser.add_argument("--external-id")
    parser.add_argument("--published-at")
    parser.add_argument("--legal-basis-note", default="manual review")
    parser.add_argument("--text", required=True)
    parser.add_argument("--dry-run", action="store_true", default=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(build_candidate(args), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
