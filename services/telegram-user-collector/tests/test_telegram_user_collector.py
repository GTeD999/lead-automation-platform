import importlib.util
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "telegram_user_collector.py"
SPEC = importlib.util.spec_from_file_location("telegram_user_collector", MODULE_PATH)
collector = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(collector)


class TelegramUserCollectorTest(unittest.TestCase):
    def test_candidate_with_real_estate_intent_and_contact(self) -> None:
        text = "Нужен офис в центре, бюджет до 150 тыс, писать @office_buyer"
        self.assertTrue(collector.is_candidate(text))
        self.assertEqual(collector.detect_segment(text), "commercial")
        self.assertEqual(collector.detect_intent(text), "rent")

    def test_rejects_sale_listing_with_contact(self) -> None:
        text = "Объект #1 Продам офис 120 м2, цена 4 200 000, звоните +7 913 456-70-90 #Продажа"
        self.assertFalse(collector.is_candidate(text))

    def test_rejects_services_ad(self) -> None:
        text = "Монтаж отопления, консультация бесплатно, звоните 8-914-270-53-47"
        self.assertFalse(collector.is_candidate(text))

    def test_accepts_buyer_request(self) -> None:
        text = "Куплю коммерческое помещение под магазин в Новосибирске, рассмотрю варианты, связь @buyer_nsk"
        self.assertTrue(collector.is_candidate(text))
        self.assertEqual(collector.detect_intent(text), "buy")

    def test_recent_message_filter(self) -> None:
        self.assertTrue(collector.is_recent_message(datetime.now(timezone.utc), 30))
        self.assertFalse(collector.is_recent_message(datetime.now(timezone.utc) - timedelta(days=365), 30))

    def test_email_does_not_create_telegram(self) -> None:
        contacts = collector.extract_contacts("Почта user@example.com")
        self.assertEqual(contacts["telegram_usernames"], [])

    def test_source_from_discovery_row_prefers_username(self) -> None:
        self.assertEqual(
            collector.source_from_row({"username": "realty_nsk", "url": "https://t.me/other"}),
            "@realty_nsk",
        )

    def test_source_from_discovery_row_falls_back_to_url(self) -> None:
        self.assertEqual(
            collector.source_from_row({"url": "https://t.me/commercial_nsk"}),
            "@commercial_nsk",
        )

    def test_parse_proxy_empty(self) -> None:
        self.assertEqual(collector.parse_proxy(None), (None, None))

    @unittest.skipIf(importlib.util.find_spec("socks") is None, "proxy dependency unavailable")
    def test_parse_proxy_socks5(self) -> None:
        connection, proxy = collector.parse_proxy("socks5://user:pass@example.com:1080")
        self.assertIsNone(connection)
        self.assertEqual(proxy[1:], ("example.com", 1080, True, "user", "pass"))

    @unittest.skipIf(importlib.util.find_spec("telethon") is None, "telethon dependency unavailable")
    def test_parse_mtproxy_link(self) -> None:
        connection, proxy = collector.parse_proxy(
            "https://t.me/proxy?server=91.212.107.71&port=443&secret=abc"
        )
        self.assertIsNotNone(connection)
        self.assertEqual(proxy, ("91.212.107.71", 443, "69b7"))

    def test_normalize_mtproxy_secret_keeps_hex(self) -> None:
        self.assertEqual(collector.normalize_mtproxy_secret("AABBcc"), "aabbcc")

    def test_normalize_mtproxy_secret_decodes_urlsafe_base64(self) -> None:
        secret = "7rw87NWJ9n8ow3lz6rjCZEZyYmMucnU"
        self.assertEqual(
            collector.normalize_mtproxy_secret(secret),
            "eebc3cecd589f67f28c37973eab8c264467262632e7275",
        )


if __name__ == "__main__":
    unittest.main()
