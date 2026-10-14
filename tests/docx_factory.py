from __future__ import annotations

import html
import zipfile
from pathlib import Path


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
O_NS = "urn:schemas-microsoft-com:office:office"
V_NS = "urn:schemas-microsoft-com:vml"


def text_paragraph(text: str) -> str:
    return f"<w:p><w:r><w:t>{html.escape(text)}</w:t></w:r></w:p>"


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


def write_docx(path: Path, paragraphs: list[str], include_ole: bool = False) -> Path:
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W_NS}" xmlns:m="{M_NS}" xmlns:r="{R_NS}" '
        f'xmlns:o="{O_NS}" xmlns:v="{V_NS}"><w:body>'
        + "".join(paragraphs)
        + "<w:sectPr/></w:body></w:document>"
    )
    relationships = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    )
    if include_ole:
        relationships += (
            '<Relationship Id="rIdImage" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.wmf"/>'
            '<Relationship Id="rIdOle" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject" Target="embeddings/oleObject1.bin"/>'
        )
    relationships += "</Relationships>"

    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document)
        archive.writestr("word/_rels/document.xml.rels", relationships)
        if include_ole:
            archive.writestr("word/media/image1.wmf", b"preview")
            archive.writestr("word/embeddings/oleObject1.bin", b"ole")
    return path
