from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import inspect_layout  # noqa: E402
from docx_factory import (  # noqa: E402
    cell_paragraph,
    drawing_paragraph,
    section_properties,
    table_xml,
    write_docx,
)


class InspectLayoutTests(unittest.TestCase):
    def test_image_placement_and_extent_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "images.docx"
            dedicated_cell = drawing_paragraph(2000000) + drawing_paragraph(2000000)
            mixed_cell = drawing_paragraph(2000000) + cell_paragraph("图内说明")
            write_docx(
                path,
                [
                    drawing_paragraph(6000000),
                    drawing_paragraph(2000000, text="同段正文"),
                    drawing_paragraph(2000000, floating=True),
                    table_xml([4000, 4000], [[dedicated_cell, mixed_cell]]),
                ],
                include_image=True,
                section_xml=section_properties(page_width=10000, left_margin=1000, right_margin=1000),
            )
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            result = inspect_layout.inspect(path)
            after = hashlib.sha256(path.read_bytes()).hexdigest()

            self.assertEqual(before, after)
            self.assertTrue(result["images"][0]["standalone_paragraph"])
            self.assertTrue(result["images"][0]["exceeds_usable_width"])
            self.assertFalse(result["images"][1]["standalone_paragraph"])
            self.assertEqual(result["images"][2]["floating_anchor_count"], 1)
            dedicated = [image for image in result["images"] if image["table_cell"] == {"table": 1, "row": 1, "cell": 1}]
            mixed = [image for image in result["images"] if image["table_cell"] == {"table": 1, "row": 1, "cell": 2}]
            self.assertEqual(len(dedicated), 2)
            self.assertTrue(all(image["dedicated_image_cell"] for image in dedicated))
            self.assertTrue(all(not image["single_image_cell"] for image in dedicated))
            self.assertFalse(mixed[0]["dedicated_image_cell"])

    def test_table_width_breaks_and_wrap_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tables.docx"
            long_text = "非常狭窄的第一列包含较长表头和连续内容"
            table = table_xml(
                [1000, 9000],
                [
                    [cell_paragraph("强制换行", explicit_break=True), cell_paragraph("短")],
                    [cell_paragraph(long_text), cell_paragraph("值") + cell_paragraph("单位")],
                ],
            )
            write_docx(
                path,
                [table],
                section_xml=section_properties(page_width=10000, left_margin=1000, right_margin=1000),
            )
            result = inspect_layout.inspect(path)
            inspected = result["tables"][0]

            self.assertTrue(inspected["exceeds_usable_width"])
            self.assertEqual(result["summary"]["cells_with_explicit_breaks"], 1)
            self.assertEqual(result["summary"]["cells_with_multiple_paragraphs"], 1)
            self.assertGreaterEqual(result["summary"]["cells_with_likely_wrap"], 1)
            self.assertTrue(inspected["columns"][0]["disproportionate_width_candidate"])
            self.assertIn("heuristic", result["limitations"][0])


if __name__ == "__main__":
    unittest.main()
