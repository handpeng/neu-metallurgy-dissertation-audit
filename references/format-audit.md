# Format And Mechanical Audit

Use this reference for document-level compliance. Resolve all configurable rules through `source-policy.md` first.

## Structure And Navigation

Check the required front matter, body, and end matter for the applicable degree. Typical items include Chinese and English title pages and abstracts, declarations, contents, optional nomenclature, introduction, chapters, conclusions, references, acknowledgements, publications or achievements, and author biography. Do not assume the master's checklist exactly defines doctoral front matter.

Check heading depth, numbering continuity, title text, paragraph styles, and agreement between headings, the table of contents, bookmarks, and page locations. Distinguish an automatically generated contents field from manually typed lookalikes. Flag skipped or impossible hierarchy such as a child number exceeding or bypassing its parent.

When the legacy checklist is applicable, also check that the contents reaches the required heading depth, each contents level has the correct indentation, chapter numbers use Arabic numerals, heading numbers are followed by one space, parenthesized subheadings use the selected full-width form, and their paragraph indentation matches the template. These are template-sensitive visual checks unless the DOCX styles establish them directly.

## Text And Terminology

Check Chinese-context punctuation, paired punctuation, full-width versus half-width usage, number-unit spacing, range notation, percent notation, SI symbol case, superscripts and subscripts, abbreviation expansion at first use, and consistent translations and technical terms.

For applicable legacy text rules, inspect conjunction lists for Chinese enumeration commas, Chinese body numbering and English annotations for the selected parenthesis width, `成份` versus `成分`, `ppm` versus the required quantity expression, the selected range connector, half-width `%`, a percent sign at both endpoints of a percentage range, and sentence punctuation after short figure/table references. Treat each as conditional when a current higher-tier source is silent or contradictory.

For metallurgical notation, check context before recommending forms such as `w[Mo]` for an element mass fraction in steel and `w(FeO)` for a slag constituent. Do not replace every occurrence of `含量` mechanically: determine whether the intended quantity is specifically mass fraction, concentration, amount fraction, content in an informal sense, or another measured quantity.

Classify grammar and `的/地/得` findings as linguistic findings, not institutional-format violations, unless a source explicitly says otherwise.

## Figures And Tables

For standalone image paragraphs or cells, object dimensions, table and column widths, explicit cell breaks, estimated wrapping, and modification feasibility, follow [layout-audit.md](layout-audit.md). Keep its `structural`, `estimated`, and `rendered` evidence layers distinct.

Inventory every figure and table, its number, Chinese and English caption, first in-text reference, chapter association, and ordering. Check duplicates, missing numbers, stale cross-references, references such as `上图` or `下表`, and inconsistent caption terminology.

For captions, check bilingual pairing, number-to-title spacing, `Fig.` spacing, the capitalization convention selected for English captions, brevity, punctuation, and placement. Check the configured whitespace above Chinese table captions and below figure captions; do not hard-code `0.5-1` lines unless the legacy adviser rule is active.

Use document structure for caption and border checks, then render pages for centering, clipping, legibility, whitespace, image resolution, plot backgrounds, axis labels, tick direction, and caption proximity. Do not claim that a table is a valid three-line table merely because it has three detected borders; merged cells and conditional formatting require visual confirmation.

Judge quantitative plots differently from photographs, process diagrams, micrographs, and conceptual illustrations. Four-sided axes and inward ticks are not meaningful for every figure type.

## Abstract And Keywords

Check that the abstract states the research problem or purpose, methods, main results, and conclusions. For doctoral work, also identify the contribution or novelty claim and its evidence. Important quantitative results are allowed when they materially support the conclusion; do not enforce the legacy advice to remove all original data.

Also assess whether the abstract is independently understandable, logically complete, concise, free of citations or commentary that require the main text, and free of future plans or unrelated material. Treat prohibitions on figures, tables, chemical structures, special-character equations, and examples as template rules to confirm, while flagging any such content for review.

Check the current required keyword count before enforcing the legacy `3-5` range. Compare Chinese and English abstracts and keywords for substantive agreement rather than literal sentence-by-sentence translation.

## References

Determine the required citation standard and variant before checking punctuation or capitalization. Check citation-to-entry and entry-to-citation coverage, sequence, duplicates, missing fields, author truncation, document type, DOI or URL consistency, dates, and obvious metadata contradictions.

Where the confirmed style requires it, check the exact author threshold, `等` or `et al.` form, separator spacing, bracket width, terminal punctuation, and English title or source-name capitalization. Do not combine punctuation examples from the legacy list with a different GB/T 7714 implementation.

Treat legacy minimum counts such as 60 total and 20 foreign-language references as program-specific until confirmed. Counts do not establish relevance, quality, currency, or adequate coverage.

## Automation Boundary

Good deterministic candidates include numbering continuity, literal punctuation patterns, missing spaces, repeated terminology candidates, caption inventory, cross-reference coverage, and reference counts. Semantic candidates include term equivalence, abstract completeness, whether a figure is mentioned meaningfully, and whether a unit matches the measured quantity. Visual candidates include actual alignment, table rules, font rendering, plot construction, and page balance.
