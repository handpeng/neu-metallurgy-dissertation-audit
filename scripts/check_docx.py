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
    return item


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
    paragraphs = load_paragraphs(args.docx)
    findings = scan_text_rules(paragraphs, args.legacy_text_rules)
    findings.extend(scan_caption_sequences(paragraphs))
    findings.extend(scan_equations(inspection, args.equation_separator, args.equation_parentheses))
    reference_findings, reference_summary = scan_references(paragraphs, args.min_references, args.min_foreign_references)
    findings.extend(reference_findings)
    keyword_summary = inspect_keywords(paragraphs)
    findings.extend(check_keyword_limits(keyword_summary, args.keyword_min, args.keyword_max))
    findings.sort(key=lambda item: (int(item.get("paragraph_index", 10**9)), str(item["rule_id"]), str(item["message"])))

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
            **reference_summary,
            "keywords": keyword_summary,
        },
        "inventory": inspection["inventory"],
        "findings": findings,
        "manual_checks": [
            "Current university/school template and effective date",
            "Page layout, fonts, headers, pagination, and contents indentation",
            "Figure/table visual quality, caption pairing, borders, and whitespace",
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
