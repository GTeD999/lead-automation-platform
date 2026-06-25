import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "lead_collector.py"
SPEC = importlib.util.spec_from_file_location("lead_collector", MODULE_PATH)
lead_collector = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(lead_collector)


class LeadCollectorTest(unittest.TestCase):
    def test_extract_contacts(self) -> None:
        text = "Call +7 913 123-45-67, email Test@Example.COM, tg @manager_test, https://vk.com/id123"
        contacts = lead_collector.extract_contacts(text)

        self.assertEqual(contacts["phones"], ["+79131234567"])
        self.assertEqual(contacts["emails"], ["test@example.com"])
        self.assertEqual(contacts["telegram_usernames"], ["manager_test"])
        self.assertEqual(contacts["vk_urls"], ["https://vk.com/id123"])

    def test_normalize_phone_from_local_format(self) -> None:
        self.assertEqual(lead_collector.normalize_phone("8 (913) 123-45-67"), "+79131234567")


if __name__ == "__main__":
    unittest.main()
