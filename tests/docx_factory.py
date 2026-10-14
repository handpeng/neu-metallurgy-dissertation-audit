from __future__ import annotations

import html
import zipfile
from pathlib import Path


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
O_NS = "urn:schemas-microsoft-com:office:office"
V_NS = "urn:schemas-microsoft-com:vml"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


def text_paragraph(
    text: str,
    *,
    left_indent: int | None = None,
    first_line_indent: int | None = None,
    hanging_indent: int | None = None,
) -> str:
    indentation = ""
    attributes = []
    if left_indent is not None:
        attributes.append(f'w:left="{left_indent}"')
    if first_line_indent is not None:
        attributes.append(f'w:firstLine="{first_line_indent}"')
    if hanging_indent is not None:
        attributes.append(f'w:hanging="{hanging_indent}"')
    if attributes:
        indentation = "<w:pPr><w:ind " + " ".join(attributes) + "/></w:pPr>"
    return f"<w:p>{indentation}<w:r><w:t>{html.escape(text)}</w:t></w:r></w:p>"


def math_paragraph(expression: str, label: str = "") -> str:
    label_xml = f"<w:r><w:t>{html.escape(label)}</w:t></w:r>" if label else ""
    return (
        "<w:p><m:oMath><m:r><m:t>"
        + html.escape(expression)
        + "</m:t></m:r></m:oMath>"
        + label_xml
        + "</w:p>"
    )


def ole_paragraph() -> str:
    return (
        '<w:p><w:r><w:object><v:shape><v:imagedata r:id="rIdImage"/>'
        '</v:shape><o:OLEObject r:id="rIdOle"/></w:object></w:r></w:p>'
    )


def drawing_paragraph(
    width_emu: int,
    *,
    height_emu: int = 1800000,
    text: str = "",
    floating: bool = False,
) -> str:
    container = "wp:anchor" if floating else "wp:inline"
    text_xml = f"<w:r><w:t>{html.escape(text)}</w:t></w:r>" if text else ""
    return (
        "<w:p><w:pPr><w:jc w:val=\"center\"/></w:pPr>"
        + text_xml
        + f'<w:r><w:drawing><{container}><wp:extent cx="{width_emu}" cy="{height_emu}"/>'
        + '<a:graphic><a:graphicData><a:blip r:embed="rIdImage"/></a:graphicData></a:graphic>'
        + f"</{container}></w:drawing></w:r></w:p>"
    )


def cell_paragraph(text: str, *, explicit_break: bool = False) -> str:
    escaped = html.escape(text)
    if explicit_break:
        midpoint = max(1, len(escaped) // 2)
        escaped = escaped[:midpoint] + "</w:t><w:br/><w:t>" + escaped[midpoint:]
    return f"<w:p><w:r><w:t>{escaped}</w:t></w:r></w:p>"


def table_xml(grid_widths: list[int], rows: list[list[str]]) -> str:
    grid = "".join(f'<w:gridCol w:w="{width}"/>' for width in grid_widths)
    row_xml: list[str] = []
    for row in rows:
        cells = []
        for index, content in enumerate(row):
            width = grid_widths[min(index, len(grid_widths) - 1)]
            cells.append(f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/></w:tcPr>{content}</w:tc>')
        row_xml.append("<w:tr>" + "".join(cells) + "</w:tr>")
    return '<w:tbl><w:tblPr><w:tblLayout w:type="fixed"/></w:tblPr><w:tblGrid>' + grid + "</w:tblGrid>" + "".join(row_xml) + "</w:tbl>"


def section_properties(
    *,
    page_width: int = 11906,
    page_height: int = 16838,
    left_margin: int = 1440,
    right_margin: int = 1440,
) -> str:
    return (
        f'<w:sectPr><w:pgSz w:w="{page_width}" w:h="{page_height}"/>'
        f'<w:pgMar w:left="{left_margin}" w:right="{right_margin}"/></w:sectPr>'
    )


def write_docx(
    path: Path,
    paragraphs: list[str],
    include_ole: bool = False,
    include_image: bool = False,
    section_xml: str = "<w:sectPr/>",
) -> Path:
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W_NS}" xmlns:m="{M_NS}" xmlns:r="{R_NS}" '
        f'xmlns:o="{O_NS}" xmlns:v="{V_NS}" xmlns:wp="{WP_NS}" xmlns:a="{A_NS}"><w:body>'
        + "".join(paragraphs)
        + section_xml
        + "</w:body></w:document>"
    )
    relationships = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    )
    if include_ole or include_image:
        relationships += (
            '<Relationship Id="rIdImage" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png"/>'
        )
    if include_ole:
        relationships += '<Relationship Id="rIdOle" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject" Target="embeddings/oleObject1.bin"/>'
    relationships += "</Relationships>"

    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document)
        archive.writestr("word/_rels/document.xml.rels", relationships)
        if include_ole or include_image:
            archive.writestr("word/media/image1.png", b"image")
        if include_ole:
            archive.writestr("word/embeddings/oleObject1.bin", b"ole")
    return path
