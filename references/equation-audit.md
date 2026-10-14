# Equation And Mathematical-Notation Audit

Use this reference for equations, formulas, symbol lists, derivations, and formula cross-references. An equation audit has structural, typographic, semantic, and visual layers; report the layers actually completed.

## 1. Inventory Formula Representations

Identify each formula representation before applying rules:

- Native Word OMML (`m:oMath` or `m:oMathPara`), whose structure and text can usually be inspected.
- MathType or another embedded OLE object, whose presence is detectable but whose mathematical content may not be available without the originating application.
- A field equation such as a legacy `EQ` field.
- Plain text using Unicode, superscript, or subscript formatting.
- A raster or vector image that visually contains a formula.

Record a formula identifier, paragraph index, rendered page when known, object type, visible or extracted expression, nearby number, chapter, and confidence. Flag opaque OLE and image formulas for visual/manual review. Do not infer that every image is a formula or that every OLE object is MathType.

## 2. Numbering And Cross-References

Resolve the required number grammar first. The local sources conflict between dot and dash forms and between full-width and half-width parentheses. Treat the pattern as configurable until a current official template decides it.

Then check:

- displayed formulas that require numbers have exactly one number;
- numbers are unique and sequential within the required scope;
- the chapter component agrees with the containing chapter;
- deleted or inserted formulas did not leave gaps, duplicates, or stale references;
- every formula reference resolves to an existing formula;
- every required formula is introduced or discussed in nearby prose;
- references use explicit numbers instead of relative phrases such as `上式` when the applicable rule forbids them.

Distinguish a literal typed number from a Word field or cross-reference. A literal number can look correct while becoming stale after editing.

## 3. Layout And Editability

Check the rendered page as well as OOXML properties. A correct layout normally places a display equation on the visual center line with its number at the right margin, but it may be implemented by tab stops, a borderless table, or another template mechanism. Paragraph alignment alone is not enough evidence.

Check vertical separation from prose, baseline alignment, consistent equation size, line wrapping, clipping, page breaks through an equation or its explanation, and collision with the number. Flag low-resolution images and inaccessible or non-editable formula objects as maintainability risks, not automatically as mathematical errors.

The legacy preference to use an equation editor only for second-level or deeper scripts is not a universal correctness rule. Enforce object-type requirements only when a current template requires them; otherwise judge legibility, semantics, and editability.

## 4. Mathematical Typography

Inspect both the equation and its symbol explanation. Apply the current institutional or national convention where supplied. Typical checks include:

- variables and variable indices are italic;
- numerals, punctuation, units, chemical element symbols, and defined mathematical functions such as `sin`, `ln`, and `exp` are upright;
- descriptive subscripts are upright while variable subscripts remain italic;
- vectors, matrices, tensors, sets, and constants follow one declared convention consistently;
- operators, relation signs, minus signs, multiplication signs, and brackets use the intended mathematical glyphs;
- superscripts and subscripts attach to the correct base and retain the intended nesting;
- quantities and units are separated and formatted consistently, with units upright;
- metallurgical mass-fraction notation such as `w[Mo]` and `w(FeO)` matches the physical context.

Do not decide italic versus upright from the character alone. For example, `T` can be a variable temperature, a transpose marker, or literal text. Use the definition and surrounding equation.

## 5. Symbol-Definition Closure

For each displayed equation followed by `式中` or an equivalent definition block:

1. Extract candidate variables, indexed quantities, operators, and constants from the equation.
2. Exclude standard operators and symbols that the applicable style does not require defining.
3. Match the remaining symbols to the explanation, preserving subscripts, superscripts, bold/italic meaning, and case.
4. Report missing definitions, unexplained changes in notation, duplicate definitions, extra definitions, and inconsistent units.
5. Check whether one symbol is reused for incompatible meanings within the same scope.

Preserve the distinction between a scalar, vector, matrix, species label, chemical formula, and unit. Text extraction commonly collapses these distinctions, so lower confidence unless OMML structure or rendering confirms them.

Also check that the punctuation, indentation, and delimiter after each symbol are consistent with the selected template. Consistency alone does not resolve the source conflict between `式中，` and `式中：`.

## 6. Mathematical And Scientific Coherence

When the user requests content review, go beyond appearance:

- test dimensional consistency where quantities and units are known;
- verify that variables, domains, boundary or initial conditions, and assumptions are stated;
- compare transformed or derived equations for missing factors, signs, exponents, and indices;
- trace empirical correlations and borrowed equations to citations;
- check whether fitted parameters, uncertainty, applicable range, and validation data are supplied;
- compare formula claims with tables, figures, methods, and conclusions.

Label these findings as semantic unless verified by reproducible calculation. Do not claim a derivation is correct merely because notation is consistent. If a calculation can be reproduced from supplied data, show the assumptions and method.

## 7. Confidence And Output

For every formula finding report:

- formula number or local identifier;
- paragraph index and page if rendered;
- object type;
- exact observed evidence;
- rule source and rule tier;
- affected layer: structure, typography, definition, scientific meaning, or rendering;
- confidence and whether manual confirmation is required;
- a specific correction that preserves the author's intended mathematics.

At the end, summarize formula coverage by counts of native OMML, OLE, field, plain-text, and image candidates. Explicitly list opaque objects and formulas whose symbols or layout could not be verified.

Use a coverage matrix with one row for each layer below:

| Layer | Minimum evidence |
| --- | --- |
| Inventory/object types | Formula representations and inaccessible objects |
| Numbering | Labels, uniqueness, sequence, and configured number grammar |
| Cross-references | Detected references resolved against detected labels |
| Rendering/layout | Rendered centering, number position, clipping, and page breaks |
| Mathematical typography | Italic/upright semantics, scripts, glyphs, and size |
| Symbol-definition closure | Equation symbols matched to definitions with case and scripts preserved |
| `式中` definition style | Selected marker, punctuation, separation, indentation, and symbol delimiters |
| Units | Quantity-unit notation and definition consistency |
| Scientific coherence | Dimensions, assumptions, transformations, and applicability |

Each layer must be `passed`, `findings`, `not-checked`, or `manual-review`, with a short evidence statement. `passed` means the layer's applicable scope was actually completed, not merely that an automated helper emitted no finding. In particular, `check_docx.py` and `inspect_tex_equations.py` leave symbol-definition closure, typography, units, rendering, and scientific coherence at `manual-review` unless separate evidence completes them. Never collapse partial structural success into “formulas passed.”

The legacy self-check requests `式中，`, symbol definitions on following indented lines, and a full-width colon or dash after each symbol. Treat this as an opt-in legacy convention until its current authority is confirmed. Even in strict mode, automatic marker and delimiter checks do not establish symbol-definition closure: compare each equation token with its rendered definition block manually or with structure-aware math parsing.
