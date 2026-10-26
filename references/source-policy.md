# Rule Sources And Precedence

## Precedence

Apply rules in this order unless the user explicitly sets another order:

1. Current university-wide doctoral-degree regulations and official template.
2. Current School of Metallurgy doctoral regulations and template.
3. Current degree-program or discipline requirements.
4. The user's explicit submission requirements.
5. Adviser or laboratory conventions.
6. Legacy self-check lists and examples.
7. General academic-writing conventions.

Record a source title, issuer, effective date or version, and degree scope whenever available. A newer lower-tier source does not automatically override a higher-tier source; surface the conflict.

## Reference-Format Precedence

For reference lists and in-text citations, use this project-specific order. It intentionally differs from the general precedence above:

1. `2 论文格式自审查要点-改正稿.docx` for author count, author truncation, separator spacing, half-width punctuation, bracket width, and its covered entry layouts.
2. `2-博士学位论文格式（学术学位，2026年6月版）.doc` for rules or document types not resolved by the self-check, including doctoral heading and body typography.
3. `附件2-东北大学冶金学院硕士、博士学位论文排版打印格式000.doc` and its required GB/T 7714-2015 basis for remaining document types and citation-to-list behavior.
4. An explicit submission instruction that the user supplies for the dissertation being audited.

Do not blend punctuation from the lower-priority examples into a rule already resolved by the self-check. In particular, the binding reference profile uses half-width bibliographic punctuation even though the later sources contain full-width or mixed examples. Read [reference-audit.md](reference-audit.md) for the normalized exact forms.

## Local Source Assessment

The skill is derived from three local documents:

- `2 论文格式自审查要点-改正稿.docx`: a six-page checklist titled for master's theses. Its package metadata says it was created in 2013 and modified in 2026, but that does not establish an official effective date. Its reference-format instructions are nevertheless the project's user-designated first priority.
- `2-博士学位论文格式（学术学位，2026年6月版）.doc`: the June 2026 university doctoral academic-degree template. It is the second reference-format source and the primary supplied doctoral template for heading and body typography.
- `附件2-东北大学冶金学院硕士、博士学位论文排版打印格式000.doc`: a School of Metallurgy format document covering both master's and doctoral theses. Its text names GB/T 7714-2015 for references but does not state an unambiguous publication or effective date in the extracted content. Confirm whether a newer university or school version exists.

Do not require these absolute paths to exist during a later audit. The normalized reference profile remains usable from this skill. For non-reference rules, label the audit provisional when current official sources cannot be confirmed.

The disposition of the 55 retained substantive checklist rows and its appended guidance is in [checklist-crosswalk.md](checklist-crosswalk.md). Use it for traceability; outside the binding reference profile, it is not proof that every legacy rule remains authoritative.

## Known Conflicts

| Topic | Legacy checklist | School format document | Treatment |
|---|---|---|---|
| Tables | Must be three-line tables | Generally use three-line tables; auxiliary lines may be added | Use the current official wording; do not flag every auxiliary line |
| Equation number | Example `（1.4）` | Example `(6–1)` | Make delimiter and separator configurable; require one current pattern before enforcing |
| Units | Generally use symbols rather than words | Symbols or Chinese unit names are allowed if used consistently | Check legality and consistency unless a current rule is stricter |
| Reference punctuation | Requires half-width symbols, including brackets | Allows either half-width or full-width if consistent; examples mix both | Use the self-check's half-width forms |
| Reference author list | List up to three authors; for four or more list the first three, then `, 等.` or `, et al.` | Requires GB/T 7714-2015 but does not spell out the threshold | Use the self-check's exact threshold and separators |
| Reference layouts | Supplies journal, book, and conference examples | Supplies eight document-type layouts | Use self-check layouts where present, then the 2026 doctoral template, then the school/GB/T source |
| Figure axes | Requires four-sided axes and inward ticks | Requires complete coordinate content and consistent lines | Apply only to applicable quantitative plots; treat as adviser preference otherwise |
| Plot software | Prefer Origin and avoid Excel | Specifies output quality, not authoring software | Review the rendered result; do not infer software or fail the thesis for software choice |
| Quantity/unit separator | Examples show `质量 /g` and `时间 /min` | Examples show `t/min` and `应力/MPa` | Follow the current template; do not enforce a space before `/` from the legacy checklist alone |
| `ppm` | Prohibited in favor of `×10^-6` | Not stated in the supplied school format | Treat as adviser preference until the applicable quantity/unit standard is confirmed |
| English title capitalization | Requires initial capitals for content words | Citation style is GB/T 7714-2015 | Check consistency and the selected citation style; do not impose title case universally |
| Abstract data | Appended guidance says to remove original data | Main checklist requires principal results | Keep material quantitative results when they support conclusions; remove only unnecessary detail |

## Rule Labels

Use one of these labels in findings:

- `official-current`: verified current authoritative requirement;
- `official-unverified`: apparently official, but currency or scope is unconfirmed;
- `user-required`: explicitly requested for this submission;
- `adviser-preference`: derived from the self-check list or local practice outside the binding reference profile;
- `general-guidance`: a recommendation rather than a compliance rule.

Never turn `adviser-preference` or `general-guidance` into a definitive compliance failure without user confirmation. Reference rules normalized in [reference-audit.md](reference-audit.md) are project requirements rather than optional adviser preferences.

## Academic Integrity Boundary

Reject the checklist's rationale that quotation length or editing should be used to avoid plagiarism detection. Assess whether borrowed language is quoted or genuinely paraphrased, attributed to the correct source, and represented accurately. A character-count threshold cannot establish originality or plagiarism.
