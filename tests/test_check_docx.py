from __future__ import annotations

import argparse
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_docx  # noqa: E402
from docx_factory import (  # noqa: E402
    cell_paragraph,
    drawing_paragraph,
    math_paragraph,
    ole_paragraph,
    section_properties,
    table_xml,
    text_paragraph,
    write_docx,
)


def arguments(path: Path, **overrides: object) -> argparse.Namespace:
    values: dict[str, object] = {
        "docx": path,
        "output": None,
        "legacy_text_rules": False,
        "legacy_formula_definition_style": False,
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

    def test_exact_reference_profile_accepts_supported_layouts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "references.docx"
            write_docx(
                path,
                [
                    text_paragraph("正文依次引用[1]和[2-3]，随后见文献[4]。"),
                    text_paragraph("参考文献"),
                    text_paragraph("[1] 张三, 李四, 王五, 等. 论文题名[J]. 冶金学报, 2024, 10(2): 1-9."),
                    text_paragraph("[2] W Y Cha, D S Kim, Y D Lee. Thermodynamic Study [J]. ISIJ International, 2004, 44(7): 1134-1139."),
                    text_paragraph("[3] 张三. 炼钢原理[M]. 北京: 冶金工业出版社, 2020, 1-20."),
                    text_paragraph("[4] 张三. 转炉炼钢研究[D]. 沈阳: 东北大学, 2026."),
                    text_paragraph("致谢"),
                ],
            )
            result = check_docx.run_checks(arguments(path))
            rules = [item["rule_id"] for item in result["findings"]]

            self.assertFalse({"L53", "L54", "L55"} & set(rules))
            self.assertTrue(result["summary"]["reference_section_found"])
            self.assertEqual(result["summary"]["detected_references"], 4)
            self.assertEqual(result["summary"]["detected_in_text_citations"], 4)
            self.assertEqual(result["summary"]["first_citation_order"], [1, 2, 3, 4])
            self.assertEqual(result["summary"]["reference_profile"], "self-check-first")
            self.assertEqual(result["reference_coverage"]["displayed_authors"]["status"], "passed")
            self.assertEqual(result["reference_coverage"]["punctuation_and_structure"]["status"], "passed")

    def test_reference_profile_reports_author_punctuation_and_marker_errors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reference-errors.docx"
            write_docx(
                path,
                [
                    text_paragraph("正文引用［1］、[2]和[3]。"),
                    text_paragraph("参考文献"),
                    text_paragraph("［1］ 张三，李四，王五，等。题名［J］。期刊，2024，1（2）：3-4。"),
                    text_paragraph("[2] A A, B B, C C, D D. English Title[J]. Journal, 2024, 1(2): 3-4."),
                    text_paragraph("[3] 张三, 李四, 等. 题名[J]. 期刊, 2024, 1(2): 3-4."),
                    text_paragraph("致谢"),
                ],
            )
            result = check_docx.run_checks(arguments(path))
            rules = [item["rule_id"] for item in result["findings"]]

            self.assertIn("L54", rules)
            self.assertIn("L55", rules)
            self.assertEqual(result["reference_coverage"]["displayed_authors"]["status"], "findings")
            self.assertEqual(result["reference_coverage"]["punctuation_and_structure"]["status"], "findings")

    def test_reference_linkage_and_wrapped_entries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reference-linkage.docx"
            write_docx(
                path,
                [
                    text_paragraph("先引用[2]，再引用[1]。"),
                    text_paragraph("参考文献"),
                    text_paragraph("[1] W Y Cha, D S Kim, Y D Lee. Thermodynamic Study [J]. ISIJ"),
                    text_paragraph("International, 2004, 44(7): 1134-1139."),
                    text_paragraph("[2] 张三. 论文题名[J]. 冶金学报, 2024, 10(2): 1-9."),
                    text_paragraph("[3] 李四. 另一题名[J]. 钢铁, 2025, 11(3): 10-18."),
                    text_paragraph("致谢"),
                ],
            )
            result = check_docx.run_checks(arguments(path))
            l53 = [item for item in result["findings"] if item["rule_id"] == "L53"]
            l55 = [item for item in result["findings"] if item["rule_id"] == "L55"]

            self.assertTrue(any("first-citation order" in str(item["message"]) for item in l53))
            self.assertTrue(any("not cited" in str(item["message"]) for item in l53))
            self.assertFalse(l55)
            self.assertEqual(result["summary"]["detected_references"], 3)

    def test_keyword_limits_are_configurable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "keywords.docx"
            write_docx(path, [text_paragraph("关键词：炼钢；夹杂物")])
            result = check_docx.run_checks(arguments(path, keyword_min=3, keyword_max=5))
            self.assertIn("L06", [item["rule_id"] for item in result["findings"]])
            self.assertEqual(result["summary"]["keywords"]["count"], 2)

    def test_layout_findings_include_evidence_and_modification_assessment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "layout.docx"
            write_docx(
                path,
                [
                    drawing_paragraph(6000000, text="与图片同段"),
                    table_xml([1000, 9000], [[cell_paragraph("很长的窄列内容很可能发生自动换行"), cell_paragraph("值")]]),
                ],
                include_image=True,
                section_xml=section_properties(page_width=10000, left_margin=1000, right_margin=1000),
            )
            result = check_docx.run_checks(arguments(path))
            layout_findings = [item for item in result["findings"] if item["rule_id"].startswith(("IMG", "TBL"))]

            self.assertTrue(layout_findings)
            self.assertIn("IMG01", [item["rule_id"] for item in layout_findings])
            self.assertIn("IMG04", [item["rule_id"] for item in layout_findings])
            self.assertIn("TBL01", [item["rule_id"] for item in layout_findings])
            self.assertIn("TBL04", [item["rule_id"] for item in layout_findings])
            for item in layout_findings:
                self.assertIn(item["evidence_layer"], {"structural", "estimated", "rendered"})
                self.assertIn(item["modification_disposition"], {"auto-safe", "auto-assisted", "manual-only", "do-not-change"})
                self.assertIn("modification_risk", item)
                self.assertIn("verification_required", item)
                self.assertIn("location", item)
            wrap = next(item for item in layout_findings if item["rule_id"] == "TBL04")
            self.assertEqual(wrap["evidence_layer"], "estimated")
            self.assertIn("likely", wrap["message"].lower())
            self.assertNotIn("confirmed", wrap["message"].lower())
            self.assertEqual(result["summary"]["layout_finding_count"], len(layout_findings))
            self.assertEqual(sum(result["summary"]["layout_modification_dispositions"].values()), len(layout_findings))

    def test_legacy_formula_definition_style_is_opt_in_and_coverage_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "formula-definitions.docx"
            write_docx(
                path,
                [
                    math_paragraph("f_H=w[%H]", "（2.1）"),
                    text_paragraph("其中，fH: 氢在钢液中的相互作用系数；"),
                    text_paragraph("T: 钢液温度，K。", left_indent=0, first_line_indent=0),
                ],
            )
            default = check_docx.run_checks(arguments(path))
            strict = check_docx.run_checks(arguments(path, legacy_formula_definition_style=True))

            self.assertNotIn("L40", [item["rule_id"] for item in default["findings"]])
            self.assertEqual(default["formula_coverage"]["definition_style"]["status"], "not-checked")
            self.assertEqual(default["formula_coverage"]["symbol_definition_closure"]["status"], "manual-review")
            strict_l40 = [item for item in strict["findings"] if item["rule_id"] == "L40"]
            self.assertTrue(strict_l40)
            messages = " ".join(str(item["message"]) for item in strict_l40)
            self.assertIn("`其中`", messages)
            self.assertIn("same paragraph", messages)
            self.assertIn("ASCII colon", messages)
            self.assertEqual(strict["formula_coverage"]["definition_style"]["status"], "findings")


if __name__ == "__main__":
    unittest.main()
