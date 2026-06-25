import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "presentation_generator.py"
SPEC = importlib.util.spec_from_file_location("presentation_generator", MODULE_PATH)
generator = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(generator)


class PresentationGeneratorTest(unittest.TestCase):
    def test_normalize_payload_accepts_wordpress_like_fields(self) -> None:
        data = generator.normalize_payload({
            "id": 123,
            "title": "Офис на Красном проспекте",
            "area": 120,
            "images": ["https://example.com/1.jpg"],
        })

        self.assertEqual(data["external_id"], 123)
        self.assertEqual(data["area_m2"], 120)
        self.assertEqual(data["photos"][0]["url"], "https://example.com/1.jpg")

    def test_save_presentation_writes_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_dir = generator.OUTPUT_DIR
            generator.OUTPUT_DIR = Path(tmp)
            try:
                result = generator.save_presentation({"title": "Склад 500 м2", "description": "Тест"})
                path = Path(tmp) / result["slug"] / "index.html"
                self.assertTrue(path.exists())
                self.assertIn("Склад 500 м2", path.read_text(encoding="utf-8"))
            finally:
                generator.OUTPUT_DIR = old_dir


if __name__ == "__main__":
    unittest.main()
