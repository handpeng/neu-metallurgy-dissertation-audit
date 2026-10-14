# Figure And Table Layout Audit

Use this reference when the request concerns figure placement, standalone image blocks, table width, column proportions, wrapped cell content, overflow, or whether layout can be modified safely.

## Evidence Layers

Treat layout evidence in three layers:

1. `structural`: OOXML proves how objects, paragraphs, cells, widths, breaks, and anchors are encoded.
2. `estimated`: width and font metrics indicate that wrapping or overflow is likely, but Word's final layout is not encoded.
3. `rendered`: a Microsoft Word or identified alternative rendering confirms the actual page, line breaks, clipping, and visual balance.

Never report estimated wrapping as confirmed wrapping. LibreOffice output is useful evidence but may paginate or size fonts differently from Microsoft Word.

## Figure Placement

For each picture or drawing, record its paragraph, relationship target, inline or floating placement, dimensions, alignment, table-cell location, nearby captions, and whether text shares the same paragraph.

A standalone figure block normally has no body text in the same paragraph. If a figure is placed in a table for alignment, distinguish these cases:

- one image in a dedicated cell with no unrelated text;
- multiple images intentionally forming a composite panel;
- image and caption or body text mixed in one cell;
- decorative or formula images that are not dissertation figures.

Do not flag a multi-panel figure merely because it has several image objects. Confirm whether the panels form one numbered figure. Flag floating anchors for rendered inspection because text wrapping and movement can change across Word versions.

Report `single_image_cell` separately from `dedicated_image_cell`: the former proves that the cell has one image and no visible text, while the latter also permits multiple image objects in an otherwise image-only composite cell.

Compare image width with the section's usable page width. Check aspect ratio, crop, resolution, clipping, centering, caption separation, and whether a page break strands the caption. Only the width comparison is deterministic; the rest requires rendering or source-image metadata.

## Table Width And Columns

Record page width and margins, table declared width, grid width, layout mode, indentation, logical columns, merged spans, and each cell's width. Inspect whether:

- the grid exceeds the usable page width;
- a narrow column contains long or unbreakable content;
- column width is disproportionate to headings and data;
- a wide descriptive column is constrained while short numeric columns consume excess width;
- merged cells or hidden auxiliary columns distort the apparent grid;
- table autofit changes widths unpredictably across renderers.

Column-width suitability is semantic. Use measured widths and content load to nominate cells or columns for review, then confirm on rendered pages. Do not redistribute all columns equally by default.

## Cell Wrapping

Distinguish:

- explicit line breaks (`w:br` or `w:cr`), which are deterministic;
- multiple non-empty paragraphs in one cell, which are deterministic but may be intentional;
- automatic wrapping, which is not recorded in DOCX and must be estimated from cell width, font size, and content length;
- clipping under `noWrap` or fit-to-text settings, which requires rendering.

For every suspected wrap, report table, row, cell, logical column, width, content excerpt, evidence layer, and confidence. Pay particular attention to headers, units, sample identifiers, chemical formulas, URLs, and long English words.

## Modification Assessment

Every layout finding must include one of these dispositions:

- `auto-safe`: a narrow, reversible property correction with confirmed intent, such as applying the established alignment style to an otherwise standalone figure paragraph.
- `auto-assisted`: a script can make the change, but the result must be rendered and reviewed, such as resizing an oversized image proportionally or adjusting selected column widths.
- `manual-only`: semantic regrouping or visual judgment is required, such as restructuring composite figures, splitting a table, rewriting headers, or deciding intentional line breaks.
- `do-not-change`: evidence is insufficient or the object is opaque, protected, or template-controlled.

Rate modification risk as `low`, `medium`, or `high`. This is the risk of pagination, caption/reference association, legibility, or semantic damage, not the severity of the original finding. A high-risk change may still be technically scriptable.

Assess feasibility before editing. State the proposed property changes, affected objects, pagination risk, caption/reference risk, and required before/after checks. Preserve the original and modify a copy unless the user explicitly authorizes in-place edits.

After any layout modification, render both versions with the same engine and compare page count, object order, caption association, cross-references, table completeness, formula integrity, and the pages immediately before and after every changed object.
