from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import inspect_docx  # noqa: E402
from docx_factory import math_paragraph, ole_paragraph, text_paragraph, write_docx  # noqa: E402


class InspectDocxTests(unittest.TestCase):
    def test_mixed_equations_and_reference_disambiguation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mixed.docx"
            write_docx(
                path,
                [
                    math_paragraph("x=1", "（2.1）"),
                    text_paragraph("由式（2.1）可知结果成立。"),
                    ole_paragraph(),
                ],
                include_ole=True,
            )
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            result = inspect_docx.inspect(path)
            after = hashlib.sha256(path.read_bytes()).hexdigest()

            self.assertEqual(before, after)
            self.assertEqual(result["inventory"]["native_omml_equations"], 1)
            self.assertEqual(result["inventory"]["ole_objects"], 1)
            self.assertEqual(len(result["equation_numbers"]), 1)
            self.assertEqual(len(result["equation_references"]), 1)
            self.assertEqual(result["diagnostics"]["duplicate_equation_numbers"], [])
            self.assertEqual(len(result["formula_paragraphs"]), 2)

    def test_rejects_non_docx_input(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be a .docx"):
            inspect_docx.inspect(Path("example.doc"))


if __name__ == "__main__":
    unittest.main()
