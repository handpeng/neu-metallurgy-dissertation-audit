from __future__ import annotations

import argparse
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_docx  # noqa: E402
from docx_factory import ole_paragraph, text_paragraph, write_docx  # noqa: E402


def arguments(path: Path, **overrides: object) -> argparse.Namespace:
    values: dict[str, object] = {
        "docx": path,
        "output": None,
        "legacy_text_rules": False,
        "min_references": None,
        "min_foreign_references": None,
        "keyword_min": None,
        "keyword_max": None,
        "equation_separator": "any",
        "equation_parentheses": "any",
    }
    values.update(overrides)
    return argparse.Namespace(**values)


class CheckDocxTests(unittest.TestCase):
    def test_detects_mechanical_issues_without_heading_false_positive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "issues.docx"
            write_docx(
                path,
                [
                    text_paragraph("1.2.1 正确标题"),
                    text_paragraph("1.2.2错误标题"),
                    text_paragraph("图2.1 正确图题"),
                    text_paragraph("图2.2错误图题"),
                    text_paragraph("钢坯成份为15kg，强度为20Mpa，范围为0.01~0.02%，见上图。"),
                    text_paragraph("由式（3-1）可知。"),
                    ole_paragraph(),
                ],
                include_ole=True,
            )
            result = check_docx.run_checks(arguments(path))
            rules = [item["rule_id"] for item in result["findings"]]

            for expected in ("L11", "L23", "L44", "L46", "L47", "L51", "L35", "L29", "L30"):
                self.assertIn(expected, rules)
            l11_evidence = [item.get("evidence") for item in result["findings"] if item["rule_id"] == "L11"]
            self.assertNotIn("1.2.1 正确标题", l11_evidence)

    def test_legacy_rules_are_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy.docx"
            write_docx(path, [text_paragraph("浓度为10 ppm，范围见图2.1-图2.2。")])
            default = check_docx.run_checks(arguments(path))
            legacy = check_docx.run_checks(arguments(path, legacy_text_rules=True))

            self.assertNotIn("L48", [item["rule_id"] for item in default["findings"]])
            self.assertIn("L48", [item["rule_id"] for item in legacy["findings"]])
            self.assertIn("L49", [item["rule_id"] for item in legacy["findings"]])

    def test_reference_sequence_and_confirmed_thresholds(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "references.docx"
            write_docx(
                path,
                [
                    text_paragraph("参考文献"),
                    text_paragraph("[1] 张三. 中文文献[J]."),
                    text_paragraph("[3] SMITH A. English article[J]."),
                    text_paragraph("致谢"),
                ],
            )
            result = check_docx.run_checks(arguments(path, min_references=3, min_foreign_references=2))
            rules = [item["rule_id"] for item in result["findings"]]

            self.assertIn("L53", rules)
            self.assertIn("L57", rules)
            self.assertTrue(result["summary"]["reference_section_found"])
            self.assertEqual(result["summary"]["detected_references"], 2)
            self.assertEqual(result["summary"]["estimated_foreign_references"], 1)

    def test_keyword_limits_are_configurable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "keywords.docx"
            write_docx(path, [text_paragraph("关键词：炼钢；夹杂物")])
            result = check_docx.run_checks(arguments(path, keyword_min=3, keyword_max=5))
            self.assertIn("L06", [item["rule_id"] for item in result["findings"]])
            self.assertEqual(result["summary"]["keywords"]["count"], 2)


if __name__ == "__main__":
    unittest.main()
