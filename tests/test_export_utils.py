import tempfile
import unittest
from pathlib import Path

from export_utils import write_simple_text_pdf


class ExportUtilsTests(unittest.TestCase):
    def test_write_simple_text_pdf_creates_pdf_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "oppskrift.pdf"
            write_simple_text_pdf("Linje 1\nLinje 2", path, title="Test")

            data = path.read_bytes()
            self.assertTrue(data.startswith(b"%PDF-1.4"))
            self.assertIn(b"/Type /Catalog", data)
            self.assertGreater(len(data), 200)


if __name__ == "__main__":
    unittest.main()
