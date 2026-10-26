# Reference And Citation Audit

Use this file for every reference-list or in-text citation audit. It defines the repository's exact reference profile and overrides conflicting reference examples in the other supplied sources.

## Source Order

1. The self-check document controls author thresholds, truncation, separator spacing, half-width punctuation, bracket width, and the layouts it illustrates.
2. The June 2026 doctoral template supplies unresolved doctoral layouts and typography.
3. The School of Metallurgy document and GB/T 7714-2015 supply remaining document types and citation behavior.

Do not average or mix conflicting punctuation. Apply the first source that resolves the point.

## In-Text Citations

- Use the sequential numbering system and order the reference list by first citation.
- Use half-width square brackets with no internal spaces: `[1]`, `[10,24]`, and `[3-4]`.
- When the citation does not form a sentence component, render it as a superscript. When it forms a sentence component, keep it on the baseline, as in `文献[6]`.
- Check every cited number has one list entry and every list entry is cited. Treat fields that do not expose their displayed result in DOCX as manual-review items.

Superscript/baseline placement is a rendered or run-level check. Text extraction alone cannot prove it.

## Entry Prefix And Punctuation

- Display every entry with a `[序号]` prefix. A literal prefix uses one following ASCII space. Word automatic numbering is allowed when `numbering.xml` renders the same bracketed decimal label; its tab/hanging-indent separator requires rendered confirmation.
- Use half-width bibliographic punctuation throughout the entry, including `,`, `.`, `:`, `;`, `?`, `!`, `(`, `)`, `[`, and `]`.
- Separate authors with exactly `, `.
- End the author block with exactly `. `.
- End every entry with `.`.
- A Chinese title is followed immediately by its type marker, such as `题名[J]`. An English title has one ASCII space before the marker, such as `Title [J]`.
- Follow the primary type marker with exactly `. `, except where the conference layout below explicitly uses the secondary `[C], ` sequence.

Do not flag Chinese prose outside the reference list merely because it correctly uses full-width punctuation. Conversely, do not allow lower-priority Chinese examples to introduce full-width punctuation into a reference entry.

## Authors

- One to three authors: list every author.
- Four or more authors: list exactly the first three, then `, 等.` for a Chinese author list or `, et al.` for a non-Chinese author list.
- `等` and `et al.` never replace one of the first three authors.
- The final period in `等.` or `et al.` is also the author-block terminator; follow it with one ASCII space before the title.

Text inspection can prove the displayed count and separators. It cannot prove that source metadata omitted or reordered an author, so compare the original publication when authorship completeness is material.

## Exact Layouts

Apply these literal element orders. Placeholder words describe values; they are not output labels.

```text
Journal:
[序号] 作者. 题名[J]. 刊名, 年, 卷(期): 起止页码.

Book:
[序号] 作者. 书名[M]. 出版地: 出版社, 年, 起止页码.

Conference contribution:
[序号] 作者. 论文题名[A]. 论文集名[C], 出版地, 出版年: 起止页码.

Dissertation:
[序号] 作者. 学位论文名称[D]. 发表地: 学位授予单位, 年度.

Patent:
[序号] 专利申请者. 专利题名: 专利国别, 专利号[P]. 发布日期.

Standard:
[序号] 主要责任者. 标准号及标准名称[S]. 出版地: 出版者, 出版年: 引文页码.

Newspaper article:
[序号] 责任者. 文献题名[N]. 报纸名称, 出版日期[版次].

Electronic document:
[序号] 主要责任者. 题名[类型/载体]. 出版地: 出版者, 出版年[引用日期]. 获取和访问路径.
```

For English titles, insert the required space before `[J]`, `[A]`, or another title marker. Apply the same rule to an English proceedings title before `[C]`.

## Typography And Layout

For the final dissertation, `参考文献` is a first-level heading. The June 2026 template specifies a centered second-size Heiti first-level heading occupying three lines. Reference body text uses small-four Songti; Latin text and numbers use Times New Roman or the template's equivalent.

Inspect hanging indents, line starts, font substitution, line wrapping, and superscript citations in the target Word renderer. Do not infer exact visual conformance from extracted text or a LibreOffice conversion.

## Automation Boundary

Deterministic checks may cover literal and Word automatic numbering, citation/list coverage, displayed author count, truncation markers, separator spaces, punctuation width, type-marker position, and the listed element orders. Metadata correctness, genuine author completeness, English capitalization semantics, source-title accuracy, DOI/URL resolution, automatic-number suffix rendering, font rendering, and page layout still require semantic, external, or rendered review.

Do not enforce a minimum number of references or a foreign-language proportion.
