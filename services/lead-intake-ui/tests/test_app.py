import importlib.util
import os
import unittest
from pathlib import Path


os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test")

MODULE_PATH = Path(__file__).resolve().parents[1] / "app.py"
SPEC = importlib.util.spec_from_file_location("lead_intake_ui", MODULE_PATH)
app = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(app)


class LeadIntakeUiTest(unittest.TestCase):
    def test_extract_contacts(self) -> None:
        contacts = app.extract_contacts("Call 8 (913) 123-45-67, email user@example.com, tg @office_test")

        self.assertEqual(contacts["phones"], ["+79131234567"])
        self.assertEqual(contacts["emails"], ["user@example.com"])
        self.assertEqual(contacts["telegram_usernames"], ["office_test"])

    def test_email_does_not_create_telegram_username(self) -> None:
        contacts = app.extract_contacts("user@example.com")

        self.assertEqual(contacts["telegram_usernames"], [])

    def test_normalize_vk_source(self) -> None:
        source = app.normalize_source("https://vk.com/novosibirsk_realty")

        self.assertIsNotNone(source)
        assert source is not None
        self.assertEqual(source["platform"], "vk")
        self.assertEqual(source["url"], "https://vk.com/novosibirsk_realty")

    def test_source_queries_include_selected_platform_links(self) -> None:
        queries = app.source_queries("Новосибирск", "commercial", "vk")

        self.assertTrue(queries)
        self.assertEqual({item["platform"] for item in queries}, {"vk"})
        self.assertTrue(any(link["label"] == "VK" for link in queries[0]["links"]))


if __name__ == "__main__":
    unittest.main()
