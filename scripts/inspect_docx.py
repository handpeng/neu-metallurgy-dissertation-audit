#!/usr/bin/env python3
"""Inventory dissertation structure and equation representations in a DOCX."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "o": "urn:schemas-microsoft-com:office:office",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "v": "urn:schemas-microsoft-com:vml",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def qname(prefix: str, local: str) -> str:
    return f"{{{NS[prefix]}}}{local}"


def attr(element: ET.Element | None, name: str) -> str | None:
    if element is None:
        return None
    return element.get(qname("w", name))


def visible_text(element: ET.Element) -> str:
    pieces: list[str] = []
    for node in element.iter():
        if node.tag in {qname("w", "t"), qname("m", "t")} and node.text:
            pieces.append(node.text)
        elif node.tag == qname("w", "tab"):
            pieces.append("\t")
        elif node.tag in {qname("w", "br"), qname("w", "cr")}:
            pieces.append("\n")
    return "".join(pieces).strip()


def enabled_property(element: ET.Element | None, local: str) -> bool:
    if element is None:
        return False
    prop = element.find(f"w:{local}", NS)
    if prop is None:
        return False
    return attr(prop, "val") not in {"0", "false", "off"}


def formatted_word_runs(paragraph: ET.Element) -> list[dict[str, object]]:
    runs: list[dict[str, object]] = []
    for run in paragraph.findall(".//w:r", NS):
        text = visible_text(run)
        if not text:
            continue
        rpr = run.find("w:rPr", NS)
        vert_align = attr(rpr.find("w:vertAlign", NS) if rpr is not None else None, "val")
        fonts = rpr.find("w:rFonts", NS) if rpr is not None else None
        runs.append(
            {
                "text": text,
                "italic": enabled_property(rpr, "i"),
                "bold": enabled_property(rpr, "b"),
                "vertical_alignment": vert_align,
                "font_ascii": attr(fonts, "ascii"),
                "font_east_asia": attr(fonts, "eastAsia"),
            }
        )
    return runs


def formatted_math_runs(paragraph: ET.Element) -> list[dict[str, str | None]]:
    runs: list[dict[str, str | None]] = []
    math_val = f"{{{NS['m']}}}val"
    for run in paragraph.findall(".//m:r", NS):
        text = visible_text(run)
        if not text:
            continue
        style = run.find("m:rPr/m:sty", NS)
        runs.append({"text": text, "math_style": style.get(math_val) if style is not None else None})
    return runs


def relationship_map(archive: zipfile.ZipFile) -> dict[str, dict[str, str]]:
    name = "word/_rels/document.xml.rels"
    if name not in archive.namelist():
        return {}
    root = ET.fromstring(archive.read(name))
    relationships: dict[str, dict[str, str]] = {}
    for rel in root.findall(f"{{{PKG_REL_NS}}}Relationship"):
        rel_id = rel.get("Id")
        if rel_id:
            relationships[rel_id] = {
                "target": rel.get("Target", ""),
                "type": rel.get("Type", "").rsplit("/", 1)[-1],
            }
    return relationships


def related_objects(element: ET.Element, relationships: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for node in element.iter():
        for key, value in node.attrib.items():
            if key in {qname("r", "id"), qname("o", "relid")}:
                relation = relationships.get(value, {})
                item = {
                    "relationship_id": value,
                    "type": relation.get("type", "unknown"),
                    "target": relation.get("target", ""),
                }
                marker = (value, item["target"])
                if marker not in seen:
                    seen.add(marker)
                    found.append(item)
    return found


NUMBER_RE = re.compile(r"[（(]\s*(\d+)\s*([.\-\u2013\u2014])\s*(\d+)\s*[）)]")
REFERENCE_RE = re.compile(r"(?:式|公式)\s*[（(]?\s*(\d+)\s*([.\-\u2013\u2014])\s*(\d+)\s*[）)]?")
DEFINITION_MARKER_RE = re.compile(
    r"^[ \t\u3000]*(式中|其中)[ \t\u3000]*([，,:：]?)[ \t\u3000]*(.*)$", re.DOTALL
)


def paragraph_record(index: int, paragraph: ET.Element, relationships: dict[str, dict[str, str]]) -> dict[str, object]:
    ppr = paragraph.find("w:pPr", NS)
    style = attr(ppr.find("w:pStyle", NS) if ppr is not None else None, "val")
    alignment = attr(ppr.find("w:jc", NS) if ppr is not None else None, "val")
    tabs: list[dict[str, str | None]] = []
    if ppr is not None:
        for tab in ppr.findall("w:tabs/w:tab", NS):
            tabs.append({"alignment": attr(tab, "val"), "position": attr(tab, "pos")})
    indentation_node = ppr.find("w:ind", NS) if ppr is not None else None
    indentation = {
        "left": attr(indentation_node, "left"),
        "first_line": attr(indentation_node, "firstLine"),
        "hanging": attr(indentation_node, "hanging"),
    }

    text = visible_text(paragraph)
    math_nodes = paragraph.findall(".//m:oMath", NS)
    ole_nodes = paragraph.findall(".//w:object", NS)
    drawing_nodes = paragraph.findall(".//w:drawing", NS)
    pict_nodes = paragraph.findall(".//w:pict", NS)
    field_instructions = [
        node.text.strip()
        for node in paragraph.findall(".//w:instrText", NS)
        if node.text and node.text.strip()
    ]
    word_runs = formatted_word_runs(paragraph)
    math_runs = formatted_math_runs(paragraph)
    scripted_runs = [
        run for run in word_runs if run["vertical_alignment"] in {"subscript", "superscript"}
    ]
    reference_spans = [match.span() for match in REFERENCE_RE.finditer(text)]
    number_matches = [
        {"chapter": int(match.group(1)), "separator": match.group(2), "sequence": int(match.group(3)), "text": match.group(0)}
        for match in NUMBER_RE.finditer(text)
        if not any(start <= match.start() and match.end() <= end for start, end in reference_spans)
    ]
    reference_matches = [
        {"chapter": int(match.group(1)), "separator": match.group(2), "sequence": int(match.group(3)), "text": match.group(0)}
        for match in REFERENCE_RE.finditer(text)
    ]
    return {
        "paragraph_index": index,
        "text": text,
        "style": style,
        "alignment": alignment,
        "tabs": tabs,
        "indentation": indentation,
        "native_math_count": len(math_nodes),
        "native_math_text": [visible_text(node) for node in math_nodes],
        "ole_object_count": len(ole_nodes),
        "drawing_count": len(drawing_nodes),
        "legacy_pict_count": len(pict_nodes),
        "field_instructions": field_instructions,
        "formatted_word_runs": word_runs,
        "formatted_math_runs": math_runs,
        "scripted_word_runs": scripted_runs,
        "equation_numbers": number_matches,
        "equation_references": reference_matches,
        "relationships": related_objects(paragraph, relationships),
    }


def inspect(path: Path) -> dict[str, object]:
    if path.suffix.lower() != ".docx":
        raise ValueError("input must be a .docx file")
    if not path.is_file():
        raise FileNotFoundError(path)

    with zipfile.ZipFile(path) as archive:
        if "word/document.xml" not in archive.namelist():
            raise ValueError("DOCX does not contain word/document.xml")
        document = ET.fromstring(archive.read("word/document.xml"))
        relationships = relationship_map(archive)
        paragraphs = [
            paragraph_record(index, paragraph, relationships)
            for index, paragraph in enumerate(document.findall(".//w:p", NS), start=1)
        ]
        formula_paragraphs = [
            paragraph
            for paragraph in paragraphs
            if paragraph["native_math_count"]
            or paragraph["ole_object_count"]
            or paragraph["scripted_word_runs"]
            or any(instruction.lstrip().upper().startswith("EQ ") for instruction in paragraph["field_instructions"])
        ]
        definition_paragraphs: list[dict[str, object]] = []
        for position, paragraph in enumerate(paragraphs):
            marker_match = DEFINITION_MARKER_RE.match(str(paragraph["text"]))
            if not marker_match:
                continue
            associated_formula_index: int | None = None
            for previous in reversed(paragraphs[max(0, position - 3) : position]):
                if not str(previous["text"]) and not previous["native_math_count"] and not previous["ole_object_count"]:
                    continue
                if previous in formula_paragraphs:
                    associated_formula_index = int(previous["paragraph_index"])
                break
            following: list[dict[str, object]] = []
            for candidate in paragraphs[position + 1 : position + 13]:
                candidate_text = str(candidate["text"])
                if not candidate_text:
                    if following:
                        break
                    continue
                if (candidate["native_math_count"] or candidate["ole_object_count"]) and candidate["equation_numbers"]:
                    break
                if DEFINITION_MARKER_RE.match(candidate_text):
                    break
                if re.match(r"^(?:图|表)\s*\d|^\d+(?:\.\d+)*\s+", candidate_text):
                    break
                has_symbol_delimiter = bool(re.search(r"[：:—－-]", candidate_text[:80]))
                if following and not has_symbol_delimiter:
                    break
                following.append(
                    {
                        "paragraph_index": candidate["paragraph_index"],
                        "text": candidate_text,
                        "indentation": candidate["indentation"],
                        "native_math_count": candidate["native_math_count"],
                        "ole_object_count": candidate["ole_object_count"],
                    }
                )
                if not has_symbol_delimiter:
                    break
            definition_paragraphs.append(
                {
                    "paragraph_index": paragraph["paragraph_index"],
                    "text": paragraph["text"],
                    "marker": marker_match.group(1),
                    "marker_delimiter": marker_match.group(2),
                    "same_line_remainder": marker_match.group(3).strip(),
                    "indentation": paragraph["indentation"],
                    "associated_formula_paragraph_index": associated_formula_index,
                    "following_paragraphs": following,
                }
            )
        equation_references = [
            {"paragraph_index": paragraph["paragraph_index"], **reference}
            for paragraph in paragraphs
            for reference in paragraph["equation_references"]
        ]
        equation_numbers = [
            {"paragraph_index": paragraph["paragraph_index"], **number}
            for paragraph in paragraphs
            for number in paragraph["equation_numbers"]
        ]
        number_keys = [(item["chapter"], item["sequence"]) for item in equation_numbers]
        duplicate_numbers = [
            {"chapter": chapter, "sequence": sequence, "occurrences": count}
            for (chapter, sequence), count in sorted(Counter(number_keys).items())
            if count > 1
        ]
        package_names = archive.namelist()
        embedded_files = sorted(name for name in package_names if name.startswith("word/embeddings/"))
        media_files = sorted(name for name in package_names if name.startswith("word/media/"))

    field_equations = sum(
        1
        for paragraph in paragraphs
        for instruction in paragraph["field_instructions"]
        if instruction.lstrip().upper().startswith("EQ ")
    )
    scripted_text_candidates = sum(bool(paragraph["scripted_word_runs"]) for paragraph in paragraphs)

    separators = sorted({item["separator"] for item in equation_numbers})
    return {
        "input": str(path.resolve()),
        "inventory": {
            "paragraphs": len(paragraphs),
            "tables": len(document.findall(".//w:tbl", NS)),
            "native_omml_equations": len(document.findall(".//m:oMath", NS)),
            "ole_objects": len(document.findall(".//w:object", NS)),
            "legacy_eq_fields": field_equations,
            "scripted_text_candidates": scripted_text_candidates,
            "drawings": len(document.findall(".//w:drawing", NS)),
            "legacy_pictures": len(document.findall(".//w:pict", NS)),
            "embedded_files": embedded_files,
            "media_files": media_files,
        },
        "formula_paragraphs": formula_paragraphs,
        "definition_paragraphs": definition_paragraphs,
        "equation_numbers": equation_numbers,
        "equation_references": equation_references,
        "diagnostics": {
            "duplicate_equation_numbers": duplicate_numbers,
            "mixed_equation_number_separators": separators if len(separators) > 1 else [],
        },
        "limitations": [
            "Paragraph indices are not rendered page numbers.",
            "OLE and image content is inventoried but not mathematically interpreted.",
            "Alignment and typography require rendered-page and run-level review.",
            "Direct paragraph indentation is reported when present; inherited style indentation remains unknown.",
            "Definition-block association is a conservative proximity heuristic and does not prove symbol-definition closure.",
            "A number-shaped text match is a candidate until context confirms it labels an equation.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path, help="DOCX file to inspect")
    parser.add_argument("--output", type=Path, help="write JSON to this path instead of stdout")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = inspect(args.docx)
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        return 0
    except (FileNotFoundError, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(f"inspect_docx.py: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
