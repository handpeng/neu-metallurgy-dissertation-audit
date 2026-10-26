# NEU Metallurgy Dissertation Audit

An unofficial Codex skill for evidence-backed review of Northeast University School of Metallurgy dissertations. It covers document structure, Word formatting, equations, figures, tables, references, metallurgical notation, abstracts, and academic-content quality.

This repository does not redistribute university or adviser Word documents. Users must obtain and confirm the current official regulations and templates themselves.

## What It Does

- Routes full, format-only, equation-only, and content-focused audits.
- Distinguishes current official rules, unverified official material, user requirements, adviser preferences, and general guidance.
- Tracks 55 retained substantive rows from the self-check; the reference-count row is intentionally excluded.
- Applies a self-check-first reference profile for author truncation, half-width punctuation, spacing, citation order, and exact element layouts.
- Inventories native OMML, embedded OLE/MathType, legacy EQ fields, scripted text, media, formula numbers, and formula references.
- Inventories LaTeX display equations, labels, source references, and nearby `式中`/`其中` blocks.
- Emits a formula coverage matrix that prevents numbering-only checks from being reported as a complete formula pass.
- Audits standalone image placement, floating anchors, image extents, table grids, column proportions, explicit cell breaks, and estimated wrapping risk.
- Runs conservative evidence-backed checks with paragraph-level locations and explicit confidence.
- Classifies layout changes as `auto-safe`, `auto-assisted`, `manual-only`, or `do-not-change` before any edit is proposed.
- Keeps disputed legacy rules opt-in instead of silently treating them as doctoral requirements.

## Limits

This is not an official Northeast University publication. It cannot establish mathematical correctness, worldwide novelty, plagiarism, or visual conformance from text extraction alone. OLE and image formulas require visual or application-level review, and Microsoft Word pagination may differ from LibreOffice rendering.

## Install

Clone the repository into the Codex skills directory:

```bash
git clone https://github.com/handpeng/neu-metallurgy-dissertation-audit.git \
  ~/.codex/skills/neu-metallurgy-dissertation-audit
```

Invoke it as `$neu-metallurgy-dissertation-audit` or let Codex select it for an applicable thesis review.

## Local Tools

Inventory a DOCX without changing it:

```bash
python3 scripts/inspect_docx.py dissertation.docx > inventory.json
```

Inventory image and table layout evidence:

```bash
python3 scripts/inspect_layout.py dissertation.docx > layout.json
```

Run conservative checks:

```bash
python3 scripts/check_docx.py dissertation.docx > findings.json
```

Inventory equations in one LaTeX file or a source tree:

```bash
python3 scripts/inspect_tex_equations.py ./Tex > tex-equations.json
```

Enable only confirmed local requirements explicitly:

```bash
python3 scripts/check_docx.py dissertation.docx \
  --legacy-text-rules \
  --legacy-formula-definition-style \
  --equation-separator dash \
  --equation-parentheses halfwidth
```

The same formula-definition flag is available on `inspect_tex_equations.py`. It enables candidates for the legacy `式中，` marker, following-line separation, indentation evidence, and `：`/`—` symbol delimiters. It is intentionally off by default and does not automate semantic symbol-definition matching.

The scripts use only the Python standard library. Layout output distinguishes direct OOXML structure from width/font estimates and rendered confirmation. DOCX does not record automatic table-cell wrapping as an explicit event, so `likely_automatic_wrap` is a review candidate rather than a confirmed formatting defect.

Keyword limits remain configurable with `--keyword-min` and `--keyword-max`. The checker intentionally has no reference-count or language-proportion threshold.

## Validate

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/*.py
```

When Codex's system skill tools are available, also run:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

## Rule Precedence

General dissertation rules follow the official-source precedence in `references/source-policy.md`. Reference-format conflicts use the dedicated self-check-first order in `references/reference-audit.md`.

## License

Code and original documentation in this repository are released under the MIT License. External institutional documents, standards, and trademarks remain the property of their respective owners.
