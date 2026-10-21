import tempfile
import unittest
from pathlib import Path

from docx import Document
from pypdf import PdfWriter

from fs_tools import list_files, read_file, search_in_file, write_file


class FileSystemToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_read_text_returns_content_and_metadata(self):
        path = self.root / "resume.txt"
        path.write_text("Python developer", encoding="utf-8")

        result = read_file(str(path))

        self.assertTrue(result["success"])
        self.assertEqual(result["content"], "Python developer")
        self.assertEqual(result["metadata"]["name"], "resume.txt")
        self.assertIn("modified_at", result["metadata"])

    def test_read_missing_file_returns_failure(self):
        result = read_file(str(self.root / "missing.txt"))

        self.assertFalse(result["success"])
        self.assertIn("does not exist", result["error"])

    def test_read_missing_docx_returns_failure(self):
        result = read_file(str(self.root / "missing.docx"))

        self.assertFalse(result["success"])
        self.assertIn("does not exist", result["error"])

    def test_read_docx_extracts_paragraph_text(self):
        path = self.root / "resume.docx"
        document = Document()
        document.add_paragraph("Python developer")
        document.save(path)

        result = read_file(str(path))

        self.assertTrue(result["success"])
        self.assertIn("Python developer", result["content"])

    def test_read_pdf_handles_valid_document(self):
        path = self.root / "resume.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        with path.open("wb") as pdf_file:
            writer.write(pdf_file)

        result = read_file(str(path))

        self.assertTrue(result["success"])
        self.assertEqual(result["content"], "")

    def test_read_invalid_documents_returns_failure(self):
        invalid_pdf = self.root / "invalid.pdf"
        invalid_docx = self.root / "invalid.docx"
        invalid_pdf.write_text("not a PDF", encoding="utf-8")
        invalid_docx.write_text("not a DOCX", encoding="utf-8")

        self.assertFalse(read_file(str(invalid_pdf))["success"])
        self.assertFalse(read_file(str(invalid_docx))["success"])

    def test_list_files_filters_extensions_case_insensitively(self):
        (self.root / "resume.PDF").write_bytes(b"pdf")
        (self.root / "notes.txt").write_text("notes", encoding="utf-8")

        results = list_files(str(self.root), ".pdf")

        self.assertEqual([item["name"] for item in results], ["resume.PDF"])
        self.assertEqual(results[0]["size_bytes"], 3)

    def test_write_file_creates_parent_directories(self):
        path = self.root / "generated" / "summary.txt"

        result = write_file(str(path), "Summary")

        self.assertTrue(result["success"])
        self.assertEqual(path.read_text(encoding="utf-8"), "Summary")

    def test_search_returns_case_insensitive_matches_with_context(self):
        path = self.root / "resume.txt"
        path.write_text("Python and python", encoding="utf-8")

        result = search_in_file(str(path), "PYTHON")

        self.assertTrue(result["success"])
        self.assertEqual(result["match_count"], 2)
        self.assertEqual([match["position"] for match in result["matches"]], [0, 11])

    def test_search_rejects_empty_keyword(self):
        result = search_in_file(str(self.root / "resume.txt"), "")

        self.assertFalse(result["success"])
        self.assertIn("must not be empty", result["error"])


if __name__ == "__main__":
    unittest.main()
