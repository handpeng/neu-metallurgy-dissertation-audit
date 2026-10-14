---
name: neu-metallurgy-dissertation-audit
description: Audit Northeast University School of Metallurgy dissertations for institution-specific structure, formatting, equations, figures, tables, references, terminology, and academic-content quality. Use for full or focused reviews of master's or doctoral thesis DOCX, PDF, or LaTeX sources; distinguish current authoritative requirements from legacy checklists and adviser preferences.
---

# NEU Metallurgy Dissertation Audit

Audit dissertations without overstating what the available rules or file format can prove. Preserve the source document unless the user explicitly asks for corrections.

## Establish The Rule Set

Read [references/source-policy.md](references/source-policy.md) before every audit. Resolve the applicable degree, school, template version, citation standard, and user-specified exceptions. If a current authoritative source is unavailable, label the audit provisional instead of silently treating the legacy checklist as binding.

For a full audit or a request to reproduce the legacy self-check, also read [references/checklist-crosswalk.md](references/checklist-crosswalk.md). It records every substantive checklist item, its status, and the appropriate inspection method.

## Select The Audit Mode

- For a full audit, read all references below.
- For structure, typography, figures, tables, units, or references, read [references/format-audit.md](references/format-audit.md).
- For image placement, standalone image cells, table widths, column proportions, cell wrapping, or layout modification feasibility, also read [references/layout-audit.md](references/layout-audit.md).
- For any formula, equation, symbol, derivation, or mathematical-notation request, read [references/equation-audit.md](references/equation-audit.md).
- For argument, novelty, methods, evidence, discussion, abstract, or doctoral-level quality, read [references/content-audit.md](references/content-audit.md).

Do not load a mode-specific reference when it is unrelated to the request.

## Inspect The Artifact

For DOCX input, run the bundled inventory before detailed review:

```bash
python3 scripts/inspect_docx.py /path/to/dissertation.docx
```

The script emits JSON to standard output and does not modify the document. Use `--output PATH` only when the user wants a retained machine-readable artifact. Treat paragraph indices as stable evidence for the inspected file, not as page numbers.

Run the conservative deterministic checker for a full DOCX audit:

```bash
python3 scripts/check_docx.py /path/to/dissertation.docx
```

Use its optional legacy thresholds or notation flags only after the applicable source is confirmed. Findings from this checker are candidates with evidence and confidence, not a substitute for semantic or rendered-page review.

For LaTeX input, inventory supported display environments, labels, references, and nearby definition blocks without modifying the source:

```bash
python3 scripts/inspect_tex_equations.py /path/to/tex/source
```

Use `--legacy-formula-definition-style` with either the DOCX checker or LaTeX inspector only when the legacy `式中，` convention is applicable. It checks marker punctuation, paragraph/line separation, direct indentation evidence where available, and candidate symbol delimiters. It does not prove that every formula symbol has a matching definition.

For a focused image and table layout inventory, run:

```bash
python3 scripts/inspect_layout.py /path/to/dissertation.docx
```

Separate `structural`, `estimated`, and `rendered` evidence. Automatic Word line wrapping is not explicit in DOCX XML: treat `likely_automatic_wrap` as a candidate until the target renderer confirms it. For every layout finding, report whether modification is `auto-safe`, `auto-assisted`, `manual-only`, or `do-not-change`, plus its risk and required verification.

For `.doc`, convert a copy in a temporary directory before inspection. For visual layout claims, render the document or supplied PDF and inspect representative pages plus every page containing a reported visual defect. LibreOffice rendering may differ from Microsoft Word, so identify the renderer and lower confidence when layout depends on pagination, fonts, fields, or embedded objects.

Classify each check as one of:

- `deterministic`: directly supported by document structure or exact text;
- `semantic`: requires interpretation of the surrounding prose or mathematics;
- `visual`: requires rendered-page inspection;
- `manual`: cannot be established reliably from the available artifact.

Never treat an equation image, OLE object, missing font, or failed field update as if its contents were fully inspected.

## Report Findings

Lead with actionable findings ordered by severity. For every finding include location, observed evidence, applicable rule and source tier, confidence, and a concrete correction. Separate violations from recommendations and manual-review items.

State coverage explicitly: file type, sections/pages inspected, rule-source status, formula object types found, and checks that could not be completed. Do not assign an overall pass when required portions were inaccessible.

For every full audit and every formula-focused audit, report the formula coverage matrix defined in [references/equation-audit.md](references/equation-audit.md). Use only `passed`, `findings`, `not-checked`, or `manual-review` for each layer. Never state that formulas passed as a whole unless every applicable layer was completed and passed; otherwise name only the layers that passed and retain the remaining review obligations.

Do not reproduce or endorse the legacy instruction to edit quotations to evade plagiarism detection. Replace it with checks for accurate quotation, attribution, citation completeness, and genuine paraphrase.
