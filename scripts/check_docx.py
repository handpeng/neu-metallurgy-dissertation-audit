#!/usr/bin/env python3
"""Run conservative, evidence-backed checks against a dissertation DOCX."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

import inspect_docx
import inspect_layout


CJK_RE = re.compile(r"[\u3400-\u9fff]")
CAPTION_RE = re.compile(r"^(图|表)\s*(\d+)[.\-](\d+)")
REFERENCE_ENTRY_RE = re.compile(r"^\s*(?:\[(\d+)\]|(\d+)[.、])\s*(.+)")
REFERENCE_END_RE = re.compile(r"^(?:致谢|作者简介|个人简历|攻读学位期间|附录)\s*$")
NUMBER_UNIT_RE = re.compile(
    r"(?<![A-Za-z0-9_.])(\d+(?:\.\d+)?)(MPa|GPa|kPa|mg|kg|km|mm|cm|μm|um|mL|L|min|mol|Pa|K|g|m|s|h)(?![A-Za-z])"
)
PERCENT_RANGE_RE = re.compile(r"(?<![%\d])(\d+(?:\.\d+)?)\s*[~～\-–—]\s*(\d+(?:\.\d+)?)%")
REFERENCE_LIKE_CAPTION_SUFFIXES = ("中", "为", "所示", "可见", "显示", "表明", "给出")


def evidence(text: str, limit: int = 180) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    return compact if len(compact) <= limit else compact[: limit - 3] + "..."


def finding(
    rule_id: str,
    severity: str,
    check_type: str,
    message: str,
    suggestion: str,
    *,
    paragraph_index: int | None = None,
    observed: str = "",
    confidence: str = "high",
    evidence_layer: str | None = None,
    modification_disposition: str | None = None,
    modification_risk: str | None = None,
    verification_required: str | None = None,
    location: dict[str, object] | None = None,
) -> dict[str, object]:
    item: dict[str, object] = {
        "rule_id": rule_id,
        "severity": severity,
        "check_type": check_type,
        "confidence": confidence,
        "message": message,
        "suggestion": suggestion,
    }
    if paragraph_index is not None:
        item["paragraph_index"] = paragraph_index
    if observed:
        item["evidence"] = evidence(observed)
    if evidence_layer:
        item["evidence_layer"] = evidence_layer
    if modification_disposition:
        item["modification_disposition"] = modification_disposition
    if modification_risk:
        item["modification_risk"] = modification_risk
    if verification_required:
        item["verification_required"] = verification_required
    if location:
        item["location"] = location
    return item


def layout_finding(
    rule_id: str,
    severity: str,
    check_type: str,
    message: str,
    suggestion: str,
    evidence_layer: str,
    disposition: str,
    risk: str,
    verification: str,
    **kwargs: object,
) -> dict[str, object]:
    return finding(
        rule_id,
        severity,
        check_type,
        message,
        suggestion,
        evidence_layer=evidence_layer,
        modification_disposition=disposition,
        modification_risk=risk,
        verification_required=verification,
        **kwargs,
    )


def scan_layout(layout: dict[str, object]) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    composite_locations: set[tuple[object, ...]] = set()
    for image in layout["images"]:
        paragraph_index = int(image["paragraph_index"])
        cell_location = image["table_cell"]
        location = {"paragraph_index": paragraph_index}
        if cell_location:
            location["table_cell"] = cell_location
        if image["text_in_same_paragraph"]:
            findings.append(
                layout_finding(
                    "IMG01", "warning", "deterministic", "An image shares a paragraph with visible text.",
                    "Separate the figure object from body or caption text after confirming the intended grouping.",
                    "structural", "manual-only", "medium",
                    "Render the changed page and verify figure-caption association, object order, and cross-references.",
                    paragraph_index=paragraph_index, observed=str(image["text_in_same_paragraph"]), location=location,
                )
            )
        if image["inside_table_cell"] and not image["dedicated_image_cell"]:
            findings.append(
                layout_finding(
                    "IMG02", "review", "deterministic", "An image is in a table cell that also contains visible text.",
                    "Determine whether the table is an intentional figure layout before separating the image or text.",
                    "structural", "manual-only", "high",
                    "Render the entire figure/table and verify composite-panel labels, captions, and reading order.",
                    paragraph_index=paragraph_index, observed=str(image["cell_text"]), location=location,
                )
            )
        if image["floating_anchor_count"]:
            findings.append(
                layout_finding(
                    "IMG03", "review", "visual", "A floating image anchor may move or wrap differently across renderers.",
                    "Inspect its rendered placement; convert to inline only when that matches the confirmed template and intent.",
                    "structural", "do-not-change", "high",
                    "Compare Microsoft Word or identified-renderer output before and after any anchor change.",
                    paragraph_index=paragraph_index, observed=f"floating anchors: {image['floating_anchor_count']}", location=location,
                )
            )
        if image["exceeds_usable_width"]:
            findings.append(
                layout_finding(
                    "IMG04", "warning", "deterministic", "An image extent exceeds the estimated usable page width.",
                    "Confirm the applicable section, then resize proportionally or revise the page layout on a copy.",
                    "structural", "auto-assisted", "high",
                    "Render adjacent pages and verify legibility, aspect ratio, caption placement, and pagination.",
                    paragraph_index=paragraph_index, observed=str(image["extents"]), location=location,
                )
            )
        if int(image["visual_count"]) > 1 or int(image["cell_visual_count"]) > 1:
            key = (
                "cell",
                str(cell_location),
            ) if cell_location else ("paragraph", paragraph_index)
            if key not in composite_locations:
                composite_locations.add(key)
                findings.append(
                    layout_finding(
                        "IMG05", "review", "semantic", "Multiple visual objects may form a composite figure.",
                        "Confirm that the panels belong to one numbered figure and that panel labels and alignment are intentional.",
                        "structural", "manual-only", "high",
                        "Inspect the rendered composite figure together with its caption and first in-text reference.",
                        paragraph_index=paragraph_index,
                        observed=f"paragraph visuals: {image['visual_count']}; cell visuals: {image['cell_visual_count']}",
                        confidence="medium", location=location,
                    )
                )

    for table in layout["tables"]:
        table_index = int(table["table_index"])
        paragraph_index = table["first_paragraph_index"]
        table_location = {"table": table_index}
        if table["exceeds_usable_width"]:
            findings.append(
                layout_finding(
                    "TBL01", "warning", "deterministic", "A table grid exceeds the estimated usable page width.",
                    "Confirm the section geometry, then adjust selected columns, orientation, or table structure on a copy.",
                    "structural", "auto-assisted", "high",
                    "Render the full table and adjacent pages; verify all text, borders, captions, notes, and pagination.",
                    paragraph_index=paragraph_index, observed=f"grid width: {table['grid_total_cm']} cm; usable-width ratio: {table['usable_width_ratio']}", location=table_location,
                )
            )
        for cell in table["cells"]:
            cell_location = {
                "table": table_index,
                "row": cell["row"],
                "cell": cell["cell"],
                "logical_column": cell["logical_column"],
            }
            cell_paragraph = cell["first_paragraph_index"]
            observed = f"width: {cell['width_cm']} cm; text: {cell['text']}"
            if cell["explicit_break_count"]:
                findings.append(
                    layout_finding(
                        "TBL02", "review", "deterministic", "A table cell contains an explicit line break.",
                        "Confirm whether the forced break is intentional; remove it only when the header or value should remain unbroken.",
                        "structural", "manual-only", "medium",
                        "Render the row before and after any edit and verify row height, meaning, and neighboring columns.",
                        paragraph_index=cell_paragraph, observed=observed, location=cell_location,
                    )
                )
            if int(cell["nonempty_paragraph_count"]) > 1:
                findings.append(
                    layout_finding(
                        "TBL03", "review", "deterministic", "A table cell contains multiple non-empty paragraphs.",
                        "Confirm whether the paragraph separation is semantically required before merging or restructuring it.",
                        "structural", "manual-only", "medium",
                        "Render the complete row and verify paragraph spacing, row height, and reading order.",
                        paragraph_index=cell_paragraph, observed=observed, location=cell_location,
                    )
                )
            if cell["likely_automatic_wrap"]:
                findings.append(
                    layout_finding(
                        "TBL04", "review", "semantic", "Cell content is likely to wrap automatically based on width and font estimates.",
                        "Confirm the actual line break in a rendered document, then adjust selected widths or wording if the wrap harms readability.",
                        "estimated", "auto-assisted", "medium",
                        "Render with the target Word environment and compare the full table before and after any width change.",
                        paragraph_index=cell_paragraph, observed=observed,
                        confidence="medium", location=cell_location,
                    )
                )
            if cell["fit_or_clipping_review"]:
                findings.append(
                    layout_finding(
                        "TBL06", "review", "visual", "A no-wrap or fit-text cell may compress or clip content.",
                        "Inspect the rendered cell before changing no-wrap, fit-text, font size, or column width settings.",
                        "estimated", "do-not-change", "high",
                        "Use the target Word renderer and verify that the complete value remains legible.",
                        paragraph_index=cell_paragraph, observed=observed, location=cell_location,
                    )
                )
        for column in table["columns"]:
            if column["disproportionate_width_candidate"]:
                column_location = {"table": table_index, "logical_column": column["column"]}
                findings.append(
                    layout_finding(
                        "TBL05", "review", "semantic", "A column may be narrow relative to its estimated content load.",
                        "Confirm header/data semantics and rendered wrapping before redistributing selected column widths.",
                        "estimated", "auto-assisted", "medium",
                        "Render the complete table and compare headers, data alignment, wrapping, and total table width.",
                        paragraph_index=paragraph_index,
                        observed=f"width: {column['width_cm']} cm; width share: {column['share_of_table']}; content-load share: {column['content_load_share_estimate']}",
                        confidence="medium", location=column_location,
                    )
                )
    return findings


def load_paragraphs(path: Path) -> list[dict[str, object]]:
    with zipfile.ZipFile(path) as archive:
        document = ET.fromstring(archive.read("word/document.xml"))
        relationships = inspect_docx.relationship_map(archive)
    return [
        inspect_docx.paragraph_record(index, paragraph, relationships)
        for index, paragraph in enumerate(document.findall(".//w:p", inspect_docx.NS), start=1)
    ]


def scan_text_rules(paragraphs: list[dict[str, object]], legacy_text_rules: bool) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for paragraph in paragraphs:
        index = int(paragraph["paragraph_index"])
        text = str(paragraph["text"])
        if not text:
            continue

        if "成份" in text:
            findings.append(
                finding("L44", "warning", "deterministic", "Nonstandard lexical form `成份` found.", "Use `成分` unless quoting a source.", paragraph_index=index, observed=text)
            )
        if re.search(r"(?<![A-Za-z])(?:Kg|Km|Mpa)(?![A-Za-z])", text):
            findings.append(
                finding("L47", "warning", "deterministic", "A commonly mis-capitalized SI unit symbol was found.", "Use the contextually correct symbol, such as `kg`, `km`, or `MPa`.", paragraph_index=index, observed=text)
            )
        if "％" in text:
            findings.append(
                finding("L50", "review", "deterministic", "A full-width percent sign was found.", "Confirm the current template; use `%` when the half-width form is required.", paragraph_index=index, observed=text)
            )
        if NUMBER_UNIT_RE.search(text):
            findings.append(
                finding("L46", "warning", "deterministic", "A number appears directly adjacent to a unit symbol.", "Insert the required space between the numerical value and unit symbol.", paragraph_index=index, observed=text)
            )
        if PERCENT_RANGE_RE.search(text):
            findings.append(
                finding("L51", "warning", "deterministic", "The first endpoint of a percentage range appears to omit `%`.", "Write the percent sign at both endpoints when both values are percentages.", paragraph_index=index, observed=text)
            )
        if re.search(r"(?:上图|下图|上表|下表)", text):
            findings.append(
                finding("L35", "warning", "deterministic", "A relative figure/table reference was found.", "Refer to the object by its explicit number.", paragraph_index=index, observed=text)
            )
        if re.search(r"见[图表]\s*\d+(?:[.\-]\d+)?\s*[：:]", text):
            findings.append(
                finding("L52", "review", "deterministic", "A short `见图/见表` reference is followed by a colon.", "Confirm sentence intent and use the required terminal punctuation.", paragraph_index=index, observed=text)
            )
        if re.search(r"(?:[碳硫磷氧氮氢]含量|含[碳硫磷氧氮氢]量)", text):
            findings.append(
                finding("L38", "review", "semantic", "An element `含量` expression may need a precise quantity name.", "Determine whether mass fraction, amount fraction, concentration, or another quantity is intended.", paragraph_index=index, observed=text, confidence="medium")
            )
        if re.search(r"[\u3400-\u9fff][,:;][\u3400-\u9fff]", text):
            findings.append(
                finding("L17", "review", "deterministic", "Half-width punctuation appears between Chinese characters.", "Confirm whether full-width Chinese punctuation is required here.", paragraph_index=index, observed=text, confidence="medium")
            )
        if CJK_RE.search(text) and re.search(r"\(\d+\)", text):
            findings.append(
                finding("L18", "review", "deterministic", "Half-width parentheses are used for body numbering in Chinese text.", "Confirm and apply the parenthesis width required by the current template.", paragraph_index=index, observed=text, confidence="medium")
            )

        heading_match = re.match(r"^(\d+(?:\.\d+){1,3})(?![.\d])(\S)", text)
        if heading_match:
            findings.append(
                finding("L11", "warning", "deterministic", "A numbered heading appears to lack a space after its number.", "Insert one template-compliant space between the heading number and title.", paragraph_index=index, observed=text)
            )

        caption_match = re.match(r"^(图|表)\s*(\d+(?:[.\-]\d+))(?![.\d])(\S)", text)
        if (
            caption_match
            and caption_match.group(3) not in "~～-–—"
            and not caption_match.group(3).startswith(REFERENCE_LIKE_CAPTION_SUFFIXES)
        ):
            findings.append(
                finding("L23", "warning", "deterministic", "A Chinese caption appears to lack a space between its number and title.", "Insert the caption spacing required by the current template.", paragraph_index=index, observed=text)
            )
        if re.match(r"^Fig\.(?=\d)", text):
            findings.append(
                finding("L23", "warning", "deterministic", "`Fig.` is not followed by a space.", "Insert one half-width space after `Fig.`.", paragraph_index=index, observed=text)
            )
        english_caption = re.match(r"^(Fig\.|Table)\s+(\d+(?:[.\-]\d+))(?![.\d])(\S)", text)
        if english_caption:
            findings.append(
                finding("L23", "warning", "deterministic", "An English caption appears to lack a space between its number and title.", "Insert the caption spacing required by the current template.", paragraph_index=index, observed=text)
            )

        if legacy_text_rules:
            if re.search(r"\bppm\b", text, re.IGNORECASE):
                findings.append(
                    finding("L48", "review", "deterministic", "`ppm` was found under the legacy adviser rule.", "Confirm the applicable quantity standard before replacing it with `×10^-6`.", paragraph_index=index, observed=text)
                )
            if re.search(r"(?:图|表)\s*\d+(?:\.\d+)?\s*-\s*(?:图|表)\s*\d+", text):
                findings.append(
                    finding("L49", "review", "deterministic", "A hyphen joins a figure/table range under the legacy adviser rule.", "Use the range connector required by the current template.", paragraph_index=index, observed=text)
                )
    return findings


def scan_caption_sequences(paragraphs: list[dict[str, object]]) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    groups: dict[tuple[str, int], list[tuple[int, int, str]]] = defaultdict(list)
    for paragraph in paragraphs:
        text = str(paragraph["text"])
        match = CAPTION_RE.match(text)
        if match:
            suffix = text[match.end() :].lstrip()
            if suffix.startswith(REFERENCE_LIKE_CAPTION_SUFFIXES):
                continue
            groups[(match.group(1), int(match.group(2)))].append((int(match.group(3)), int(paragraph["paragraph_index"]), text))

    for (kind, chapter), entries in sorted(groups.items()):
        counts = Counter(sequence for sequence, _, _ in entries)
        for sequence, count in sorted(counts.items()):
            if count > 1:
                first = next(entry for entry in entries if entry[0] == sequence)
                findings.append(
                    finding("L24", "warning", "deterministic", f"Duplicate {kind}{chapter}.{sequence} caption candidates were found.", "Inspect the duplicates and renumber the affected captions and references.", paragraph_index=first[1], observed=first[2])
                )
        unique = sorted(counts)
        for previous, current in zip(unique, unique[1:]):
            if current != previous + 1:
                first = next(entry for entry in entries if entry[0] == current)
                findings.append(
                    finding("L24", "review", "deterministic", f"Possible gap in {kind} numbering between {chapter}.{previous} and {chapter}.{current}.", "Confirm whether an object is missing or intentionally omitted.", paragraph_index=first[1], observed=first[2], confidence="medium")
                )
    return findings


def scan_equations(
    inspection: dict[str, object], separator: str, parentheses: str
) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    diagnostics = inspection["diagnostics"]
    for duplicate in diagnostics["duplicate_equation_numbers"]:
        findings.append(
            finding("L24", "warning", "deterministic", f"Duplicate equation number candidate {duplicate['chapter']}.{duplicate['sequence']} was found.", "Inspect formula labels and update dependent references.")
        )
    if diagnostics["mixed_equation_number_separators"]:
        findings.append(
            finding("L29", "review", "deterministic", "Mixed equation-number separators were found.", "Confirm the current template and use one separator consistently.", observed=str(diagnostics["mixed_equation_number_separators"]))
        )

    labels = {(item["chapter"], item["sequence"]) for item in inspection["equation_numbers"]}
    for reference in inspection["equation_references"]:
        key = (reference["chapter"], reference["sequence"])
        if key not in labels:
            findings.append(
                finding("L29", "warning", "deterministic", f"Equation reference {reference['text']} has no detected label.", "Check the formula number and refresh or repair the cross-reference.", paragraph_index=reference["paragraph_index"], observed=reference["text"], confidence="medium")
            )

    for item in inspection["equation_numbers"]:
        text = str(item["text"])
        if separator == "dot" and item["separator"] != ".":
            findings.append(finding("L29", "warning", "deterministic", "Equation number does not use the configured dot separator.", "Use the confirmed equation-number pattern.", paragraph_index=item["paragraph_index"], observed=text))
        if separator == "dash" and item["separator"] not in {"-", "–", "—"}:
            findings.append(finding("L29", "warning", "deterministic", "Equation number does not use the configured dash separator.", "Use the confirmed equation-number pattern.", paragraph_index=item["paragraph_index"], observed=text))
        if parentheses == "fullwidth" and not (text.startswith("（") and text.endswith("）")):
            findings.append(finding("L29", "warning", "deterministic", "Equation number does not use configured full-width parentheses.", "Use the confirmed equation-number delimiters.", paragraph_index=item["paragraph_index"], observed=text))
        if parentheses == "halfwidth" and not (text.startswith("(") and text.endswith(")")):
            findings.append(finding("L29", "warning", "deterministic", "Equation number does not use configured half-width parentheses.", "Use the confirmed equation-number delimiters.", paragraph_index=item["paragraph_index"], observed=text))

    opaque_count = int(inspection["inventory"]["ole_objects"])
    if opaque_count:
        findings.append(
            finding("L30", "review", "manual", f"{opaque_count} embedded OLE object(s) require visual or application-level inspection.", "Verify formula content, typography, editability, and rendering in the authoring application.", confidence="high")
        )
    return findings


def scan_references(
    paragraphs: list[dict[str, object]], min_references: int | None, min_foreign: int | None
) -> tuple[list[dict[str, object]], dict[str, int | None]]:
    findings: list[dict[str, object]] = []
    in_references = False
    reference_section_found = False
    entries: list[tuple[int, int, str]] = []
    for paragraph in paragraphs:
        text = str(paragraph["text"]).strip()
        if not in_references and re.match(r"^参考文献\s*$", text):
            in_references = True
            reference_section_found = True
            continue
        if in_references and REFERENCE_END_RE.match(text):
            break
        if in_references:
            match = REFERENCE_ENTRY_RE.match(text)
            if match:
                number = int(match.group(1) or match.group(2))
                entries.append((number, int(paragraph["paragraph_index"]), match.group(3)))

    foreign = sum(1 for _, _, text in entries if not CJK_RE.search(text) and re.search(r"[A-Za-z]", text))
    if entries:
        actual = [number for number, _, _ in entries]
        expected = list(range(1, len(entries) + 1))
        if actual != expected:
            findings.append(
                finding("L53", "warning", "deterministic", "Reference-list numbering is not a continuous first-to-last sequence.", "Renumber entries and refresh in-text citations.", paragraph_index=entries[0][1], observed=str(actual[:20]))
            )
    if min_references is not None and len(entries) < min_references:
        findings.append(finding("L57", "review", "deterministic", f"Detected {len(entries)} references, below the configured minimum of {min_references}.", "Confirm reference extraction and the current program threshold."))
    if min_foreign is not None and foreign < min_foreign:
        findings.append(finding("L57", "review", "semantic", f"Detected approximately {foreign} foreign-language references, below the configured minimum of {min_foreign}.", "Verify language classification manually and confirm the program threshold.", confidence="medium"))
    return findings, {
        "reference_section_found": reference_section_found,
        "detected_references": len(entries),
        "estimated_foreign_references": foreign if entries else None,
    }


def inspect_keywords(paragraphs: list[dict[str, object]]) -> dict[str, object] | None:
    for paragraph in paragraphs:
        text = str(paragraph["text"])
        match = re.search(r"关键词\s*[：:]\s*(.+)", text)
        if match:
            values = [value.strip() for value in re.split(r"[；;，,、]", match.group(1)) if value.strip()]
            return {"paragraph_index": paragraph["paragraph_index"], "count": len(values), "values": values}
    return None


def check_keyword_limits(
    keyword_summary: dict[str, object] | None, minimum: int | None, maximum: int | None
) -> list[dict[str, object]]:
    if minimum is None and maximum is None:
        return []
    if keyword_summary is None:
        return [
            finding("L06", "review", "deterministic", "No keyword line was detected.", "Confirm the keyword label, location, and configured count requirement.", confidence="medium")
        ]
    count = int(keyword_summary["count"])
    if (minimum is not None and count < minimum) or (maximum is not None and count > maximum):
        bounds = f"{minimum if minimum is not None else 'unbounded'}-{maximum if maximum is not None else 'unbounded'}"
        return [
            finding("L06", "warning", "deterministic", f"Detected {count} keywords outside the configured range {bounds}.", "Revise the keyword list or confirm the current program requirement.", paragraph_index=int(keyword_summary["paragraph_index"]), observed="; ".join(str(value) for value in keyword_summary["values"]))
        ]
    return []


def run_checks(args: argparse.Namespace) -> dict[str, object]:
    for name in ("min_references", "min_foreign_references", "keyword_min", "keyword_max"):
        value = getattr(args, name)
        if value is not None and value < 0:
            raise ValueError(f"{name.replace('_', '-')} must be non-negative")
    if args.keyword_min is not None and args.keyword_max is not None and args.keyword_min > args.keyword_max:
        raise ValueError("keyword-min cannot exceed keyword-max")

    inspection = inspect_docx.inspect(args.docx)
    layout = inspect_layout.inspect(args.docx)
    paragraphs = load_paragraphs(args.docx)
    findings = scan_text_rules(paragraphs, args.legacy_text_rules)
    findings.extend(scan_caption_sequences(paragraphs))
    findings.extend(scan_equations(inspection, args.equation_separator, args.equation_parentheses))
    reference_findings, reference_summary = scan_references(paragraphs, args.min_references, args.min_foreign_references)
    findings.extend(reference_findings)
    keyword_summary = inspect_keywords(paragraphs)
    findings.extend(check_keyword_limits(keyword_summary, args.keyword_min, args.keyword_max))
    findings.extend(scan_layout(layout))
    findings.sort(key=lambda item: (int(item.get("paragraph_index", 10**9)), str(item["rule_id"]), str(item["message"])))
    layout_findings = [item for item in findings if str(item["rule_id"]).startswith(("IMG", "TBL"))]

    return {
        "input": str(args.docx.resolve()),
        "configuration": {
            "legacy_text_rules": args.legacy_text_rules,
            "equation_separator": args.equation_separator,
            "equation_parentheses": args.equation_parentheses,
            "min_references": args.min_references,
            "min_foreign_references": args.min_foreign_references,
            "keyword_min": args.keyword_min,
            "keyword_max": args.keyword_max,
        },
        "summary": {
            "finding_count": len(findings),
            "by_severity": dict(sorted(Counter(str(item["severity"]) for item in findings).items())),
            "layout_finding_count": len(layout_findings),
            "layout_modification_dispositions": dict(
                sorted(Counter(str(item["modification_disposition"]) for item in layout_findings).items())
            ),
            **reference_summary,
            "keywords": keyword_summary,
        },
        "inventory": inspection["inventory"],
        "layout": layout,
        "findings": findings,
        "manual_checks": [
            "Current university/school template and effective date",
            "Page layout, fonts, headers, pagination, and contents indentation",
            "Rendered confirmation of estimated table wrapping, column balance, clipping, caption pairing, borders, and whitespace",
            "Equation centering, typography, OLE/image content, and symbol-definition closure",
            "Abstract completeness, contribution claims, and academic-content quality",
            "Citation metadata and citation-style conformance",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path, help="DOCX file to check")
    parser.add_argument("--output", type=Path, help="write JSON to this path instead of stdout")
    parser.add_argument("--legacy-text-rules", action="store_true", help="enable adviser-level ppm and range checks")
    parser.add_argument("--min-references", type=int, help="confirmed minimum reference count")
    parser.add_argument("--min-foreign-references", type=int, help="confirmed minimum foreign-language reference count")
    parser.add_argument("--keyword-min", type=int, help="confirmed minimum keyword count")
    parser.add_argument("--keyword-max", type=int, help="confirmed maximum keyword count")
    parser.add_argument("--equation-separator", choices=("any", "dot", "dash"), default="any")
    parser.add_argument("--equation-parentheses", choices=("any", "fullwidth", "halfwidth"), default="any")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = run_checks(args)
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        return 0
    except (FileNotFoundError, ValueError, zipfile.BadZipFile, ET.ParseError, KeyError) as exc:
        print(f"check_docx.py: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
