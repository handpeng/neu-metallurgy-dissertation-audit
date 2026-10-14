#!/usr/bin/env python3
"""Inventory image and table layout evidence in a dissertation DOCX."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import inspect_docx


NS = {
    **inspect_docx.NS,
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
}
EMU_PER_CM = 360000
TWIPS_PER_CM = 567
DEFAULT_FONT_POINTS = 10.5


def wattr(element: ET.Element | None, local: str) -> str | None:
    if element is None:
        return None
    return element.get(f"{{{NS['w']}}}{local}")


def integer(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def round_or_none(value: float | None, digits: int = 2) -> float | None:
    return round(value, digits) if value is not None else None


def text_units(text: str) -> float:
    units = 0.0
    for character in text:
        if character.isspace():
            continue
        if "\u3400" <= character <= "\u9fff":
            units += 1.0
        elif character.isalnum():
            units += 0.55
        else:
            units += 0.5
    return units


def paragraph_font_points(paragraph: ET.Element) -> float:
    sizes = [
        integer(node.get(f"{{{NS['w']}}}val"))
        for node in paragraph.findall(".//w:rPr/w:sz", NS)
    ]
    points = [size / 2 for size in sizes if size]
    return max(points, default=DEFAULT_FONT_POINTS)


def page_metrics(document: ET.Element) -> dict[str, object]:
    sections = document.findall(".//w:sectPr", NS)
    section = sections[-1] if sections else None
    page_size = section.find("w:pgSz", NS) if section is not None else None
    margins = section.find("w:pgMar", NS) if section is not None else None
    width = integer(wattr(page_size, "w"))
    height = integer(wattr(page_size, "h"))
    left = integer(wattr(margins, "left")) or 0
    right = integer(wattr(margins, "right")) or 0
    usable = width - left - right if width else None
    return {
        "section_count": len(sections),
        "page_width_twips": width,
        "page_height_twips": height,
        "orientation": wattr(page_size, "orient") or "portrait",
        "margin_left_twips": left if margins is not None else None,
        "margin_right_twips": right if margins is not None else None,
        "usable_width_twips": usable,
        "usable_width_cm": round_or_none(usable / TWIPS_PER_CM if usable else None),
        "basis": "last section; section-specific rendering is required when multiple sections differ",
    }


def ancestors(element: ET.Element, parent_map: dict[ET.Element, ET.Element]):
    current = parent_map.get(element)
    while current is not None:
        yield current
        current = parent_map.get(current)


def ancestor_cell(element: ET.Element, parent_map: dict[ET.Element, ET.Element]) -> ET.Element | None:
    return next((node for node in ancestors(element, parent_map) if node.tag == f"{{{NS['w']}}}tc"), None)


def image_extents(paragraph: ET.Element) -> list[dict[str, float | int]]:
    extents: list[dict[str, float | int]] = []
    for extent in paragraph.findall(".//wp:extent", NS):
        cx = integer(extent.get("cx"))
        cy = integer(extent.get("cy"))
        if cx and cy:
            extents.append(
                {
                    "width_emu": cx,
                    "height_emu": cy,
                    "width_cm": round(cx / EMU_PER_CM, 2),
                    "height_cm": round(cy / EMU_PER_CM, 2),
                }
            )
    return extents


def image_inventory(
    document: ET.Element,
    relationships: dict[str, dict[str, str]],
    parent_map: dict[ET.Element, ET.Element],
    paragraph_indices: dict[ET.Element, int],
    cell_positions: dict[ET.Element, dict[str, int]],
    usable_width_twips: int | None,
) -> list[dict[str, object]]:
    images: list[dict[str, object]] = []
    paragraphs_by_index = {index: paragraph for paragraph, index in paragraph_indices.items()}
    for paragraph, paragraph_index in paragraph_indices.items():
        drawings = paragraph.findall(".//w:drawing", NS)
        legacy_pictures = paragraph.findall(".//w:pict", NS)
        visual_count = len(drawings) + len(legacy_pictures)
        if not visual_count:
            continue
        text = inspect_docx.visible_text(paragraph)
        cell = ancestor_cell(paragraph, parent_map)
        cell_text = inspect_docx.visible_text(cell) if cell is not None else ""
        cell_visual_count = (
            len(cell.findall(".//w:drawing", NS)) + len(cell.findall(".//w:pict", NS))
            if cell is not None
            else 0
        )
        extents = image_extents(paragraph)
        usable_width_emu = usable_width_twips * 635 if usable_width_twips else None
        images.append(
            {
                "paragraph_index": paragraph_index,
                "text_in_same_paragraph": text,
                "previous_paragraph_text": inspect_docx.visible_text(paragraphs_by_index[paragraph_index - 1]) if paragraph_index > 1 else "",
                "next_paragraph_text": inspect_docx.visible_text(paragraphs_by_index[paragraph_index + 1]) if paragraph_index < len(paragraphs_by_index) else "",
                "visual_count": visual_count,
                "inline_count": len(paragraph.findall(".//wp:inline", NS)),
                "floating_anchor_count": len(paragraph.findall(".//wp:anchor", NS)),
                "legacy_picture_count": len(legacy_pictures),
                "alignment": inspect_docx.attr(paragraph.find("w:pPr/w:jc", NS), "val"),
                "standalone_paragraph": not bool(text),
                "inside_table_cell": cell is not None,
                "table_cell": cell_positions.get(cell) if cell is not None else None,
                "dedicated_image_cell": bool(cell is not None and not cell_text and cell_visual_count > 0),
                "single_image_cell": bool(cell is not None and not cell_text and cell_visual_count == 1),
                "cell_text": cell_text if cell is not None else "",
                "cell_visual_count": cell_visual_count,
                "extents": extents,
                "exceeds_usable_width": bool(
                    usable_width_emu
                    and any(int(extent["width_emu"]) > usable_width_emu * 1.02 for extent in extents)
                ),
                "relationships": [
                    relation
                    for relation in inspect_docx.related_objects(paragraph, relationships)
                    if relation["type"] == "image"
                ],
            }
        )
    return images


def cell_width_twips(cell: ET.Element, grid_widths: list[int], grid_column: int, span: int) -> int | None:
    width = cell.find("w:tcPr/w:tcW", NS)
    width_type = wattr(width, "type")
    width_value = integer(wattr(width, "w"))
    if width_value and width_type in {None, "dxa"}:
        return width_value
    selected = grid_widths[grid_column : grid_column + span]
    return sum(selected) if selected else None


def table_inventory(
    document: ET.Element,
    paragraph_indices: dict[ET.Element, int],
    usable_width_twips: int | None,
) -> list[dict[str, object]]:
    tables: list[dict[str, object]] = []
    for table_index, table in enumerate(document.findall(".//w:tbl", NS), start=1):
        grid_widths = [
            value
            for value in (integer(wattr(column, "w")) for column in table.findall("w:tblGrid/w:gridCol", NS))
            if value is not None
        ]
        grid_total = sum(grid_widths) if grid_widths else None
        table_width = table.find("w:tblPr/w:tblW", NS)
        table_indent = table.find("w:tblPr/w:tblInd", NS)
        indent_twips = integer(wattr(table_indent, "w")) if wattr(table_indent, "type") in {None, "dxa"} else None
        cells: list[dict[str, object]] = []
        max_logical_columns = 0
        for row_index, row in enumerate(table.findall("w:tr", NS), start=1):
            grid_column = 0
            for cell_index, cell in enumerate(row.findall("w:tc", NS), start=1):
                span = integer(wattr(cell.find("w:tcPr/w:gridSpan", NS), "val")) or 1
                width_twips = cell_width_twips(cell, grid_widths, grid_column, span)
                paragraphs = cell.findall(".//w:p", NS)
                text = inspect_docx.visible_text(cell)
                font_points = max((paragraph_font_points(paragraph) for paragraph in paragraphs), default=DEFAULT_FONT_POINTS)
                capacity = width_twips / 20 / font_points if width_twips else None
                units = text_units(text)
                explicit_breaks = len(cell.findall(".//w:br", NS)) + len(cell.findall(".//w:cr", NS))
                nonempty_paragraphs = sum(bool(inspect_docx.visible_text(paragraph)) for paragraph in paragraphs)
                no_wrap = cell.find("w:tcPr/w:noWrap", NS) is not None
                fit_text = cell.find("w:tcPr/w:tcFitText", NS) is not None
                content_pressure = units / capacity if capacity else None
                cells.append(
                    {
                        "row": row_index,
                        "cell": cell_index,
                        "logical_column": grid_column + 1,
                        "grid_span": span,
                        "width_twips": width_twips,
                        "width_cm": round_or_none(width_twips / TWIPS_PER_CM if width_twips else None),
                        "text": text,
                        "text_units": round(units, 2),
                        "font_points_estimate": font_points,
                        "single_line_capacity_estimate": round_or_none(capacity),
                        "content_pressure_estimate": round_or_none(content_pressure),
                        "explicit_break_count": explicit_breaks,
                        "nonempty_paragraph_count": nonempty_paragraphs,
                        "no_wrap": no_wrap,
                        "fit_text": fit_text,
                        "likely_automatic_wrap": bool(
                            text
                            and content_pressure
                            and content_pressure > 1.05
                            and not no_wrap
                            and not fit_text
                            and explicit_breaks == 0
                            and nonempty_paragraphs <= 1
                        ),
                        "fit_or_clipping_review": bool(
                            text
                            and content_pressure
                            and content_pressure > 1.05
                            and (no_wrap or fit_text)
                        ),
                        "image_count": len(cell.findall(".//w:drawing", NS)) + len(cell.findall(".//w:pict", NS)),
                        "first_paragraph_index": paragraph_indices.get(paragraphs[0]) if paragraphs else None,
                    }
                )
                grid_column += span
            max_logical_columns = max(max_logical_columns, grid_column)

        column_loads = []
        for column_index in range(1, len(grid_widths) + 1):
            column_cells = [cell for cell in cells if cell["logical_column"] == column_index and cell["grid_span"] == 1]
            column_loads.append(max((float(cell["text_units"]) for cell in column_cells), default=0.0))
        total_column_load = sum(column_loads)

        columns: list[dict[str, object]] = []
        for column_index, width in enumerate(grid_widths, start=1):
            column_cells = [cell for cell in cells if cell["logical_column"] == column_index and cell["grid_span"] == 1]
            max_text_units = column_loads[column_index - 1]
            width_share = width / grid_total if grid_total else None
            load_share = max_text_units / total_column_load if total_column_load else None
            columns.append(
                {
                    "column": column_index,
                    "width_twips": width,
                    "width_cm": round(width / TWIPS_PER_CM, 2),
                    "share_of_table": round_or_none(width_share, 3),
                    "max_text_units": max_text_units,
                    "content_load_share_estimate": round_or_none(load_share, 3),
                    "disproportionate_width_candidate": bool(
                        width_share
                        and load_share
                        and max_text_units >= 8
                        and load_share - width_share > 0.2
                    ),
                    "likely_wrap_cells": sum(bool(cell["likely_automatic_wrap"]) for cell in column_cells),
                }
            )

        table_paragraphs = table.findall(".//w:p", NS)
        tables.append(
            {
                "table_index": table_index,
                "first_paragraph_index": paragraph_indices.get(table_paragraphs[0]) if table_paragraphs else None,
                "rows": len(table.findall("w:tr", NS)),
                "logical_columns": max_logical_columns,
                "layout": wattr(table.find("w:tblPr/w:tblLayout", NS), "type") or "autofit-or-style-default",
                "alignment": wattr(table.find("w:tblPr/w:jc", NS), "val"),
                "indent_twips": indent_twips,
                "indent_cm": round_or_none(indent_twips / TWIPS_PER_CM if indent_twips else None),
                "declared_width_type": wattr(table_width, "type"),
                "declared_width_value": integer(wattr(table_width, "w")),
                "grid_total_twips": grid_total,
                "grid_total_cm": round_or_none(grid_total / TWIPS_PER_CM if grid_total else None),
                "usable_width_ratio": round_or_none(grid_total / usable_width_twips if grid_total and usable_width_twips else None, 3),
                "exceeds_usable_width": bool(grid_total and usable_width_twips and grid_total > usable_width_twips * 1.02),
                "columns": columns,
                "cells": cells,
            }
        )
    return tables


def inspect(path: Path) -> dict[str, object]:
    if path.suffix.lower() != ".docx":
        raise ValueError("input must be a .docx file")
    if not path.is_file():
        raise FileNotFoundError(path)
    with zipfile.ZipFile(path) as archive:
        if "word/document.xml" not in archive.namelist():
            raise ValueError("DOCX does not contain word/document.xml")
        document = ET.fromstring(archive.read("word/document.xml"))
        relationships = inspect_docx.relationship_map(archive)

    parent_map = {child: parent for parent in document.iter() for child in parent}
    paragraphs = document.findall(".//w:p", NS)
    paragraph_indices = {paragraph: index for index, paragraph in enumerate(paragraphs, start=1)}
    cell_positions: dict[ET.Element, dict[str, int]] = {}
    for table_index, table in enumerate(document.findall(".//w:tbl", NS), start=1):
        for row_index, row in enumerate(table.findall("w:tr", NS), start=1):
            for cell_index, cell in enumerate(row.findall("w:tc", NS), start=1):
                cell_positions[cell] = {"table": table_index, "row": row_index, "cell": cell_index}

    page = page_metrics(document)
    images = image_inventory(
        document,
        relationships,
        parent_map,
        paragraph_indices,
        cell_positions,
        page["usable_width_twips"],
    )
    tables = table_inventory(document, paragraph_indices, page["usable_width_twips"])
    return {
        "input": str(path.resolve()),
        "page": page,
        "summary": {
            "image_paragraphs": len(images),
            "non_standalone_image_paragraphs": sum(not bool(image["standalone_paragraph"]) for image in images),
            "images_in_table_cells": sum(bool(image["inside_table_cell"]) for image in images),
            "images_in_single_image_cells": sum(bool(image["single_image_cell"]) for image in images),
            "non_dedicated_image_cells": sum(bool(image["inside_table_cell"] and not image["dedicated_image_cell"]) for image in images),
            "tables": len(tables),
            "tables_exceeding_usable_width": sum(bool(table["exceeds_usable_width"]) for table in tables),
            "cells_with_explicit_breaks": sum(cell["explicit_break_count"] > 0 for table in tables for cell in table["cells"]),
            "cells_with_multiple_paragraphs": sum(cell["nonempty_paragraph_count"] > 1 for table in tables for cell in table["cells"]),
            "cells_with_likely_wrap": sum(bool(cell["likely_automatic_wrap"]) for table in tables for cell in table["cells"]),
            "cells_requiring_fit_or_clipping_review": sum(bool(cell["fit_or_clipping_review"]) for table in tables for cell in table["cells"]),
            "columns_with_disproportionate_width_candidates": sum(bool(column["disproportionate_width_candidate"]) for table in tables for column in table["columns"]),
        },
        "images": images,
        "tables": tables,
        "limitations": [
            "Automatic line wrapping is not stored explicitly in DOCX; likely_automatic_wrap is a width/font heuristic.",
            "The usable width is based on the last section; multi-section documents require section-aware rendering.",
            "VML image dimensions and crop quality may require rendered-page inspection.",
            "Column-width suitability depends on semantic content and must be confirmed visually.",
            "Nested tables are inventoried separately, while an outer cell's content metrics may include its nested table.",
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
    except (FileNotFoundError, ValueError, zipfile.BadZipFile, ET.ParseError, KeyError) as exc:
        print(f"inspect_layout.py: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
