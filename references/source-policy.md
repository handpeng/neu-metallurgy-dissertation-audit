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

## Local Source Assessment

The skill was initially derived from two local documents:

- `2 论文格式自审查要点-改正稿.docx`: a six-page, 57-row checklist titled for master's theses. Its package metadata says it was created in 2013 and modified in 2026, but that does not establish an official effective date. Treat its positive/negative examples as useful adviser-level evidence, not as the sole doctoral standard.
- `附件2-东北大学冶金学院硕士、博士学位论文排版打印格式000.doc`: a School of Metallurgy format document covering both master's and doctoral theses. Its text names GB/T 7714-2015 for references but does not state an unambiguous publication or effective date in the extracted content. Confirm whether a newer university or school version exists.

Do not require either absolute path to exist during a later audit. The normalized rules in this skill remain usable, but the audit is provisional until the current official sources are confirmed.

The complete disposition of the 56 substantive checklist rows and its appended guidance is in [checklist-crosswalk.md](checklist-crosswalk.md). Use it for traceability, not as proof that every legacy rule remains binding.

## Known Conflicts

| Topic | Legacy checklist | School format document | Treatment |
|---|---|---|---|
| Tables | Must be three-line tables | Generally use three-line tables; auxiliary lines may be added | Use the current official wording; do not flag every auxiliary line |
| Equation number | Example `（1.4）` | Example `(6–1)` | Make delimiter and separator configurable; require one current pattern before enforcing |
| Units | Generally use symbols rather than words | Symbols or Chinese unit names are allowed if used consistently | Check legality and consistency unless a current rule is stricter |
| References | Examples use a legacy list style | Explicitly requires GB/T 7714-2015 | Apply the current official citation standard and its chosen variant |
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
- `adviser-preference`: derived from the self-check list or local practice;
- `general-guidance`: a recommendation rather than a compliance rule.

Never turn `adviser-preference` or `general-guidance` into a definitive compliance failure without user confirmation.

## Academic Integrity Boundary

Reject the checklist's rationale that quotation length or editing should be used to avoid plagiarism detection. Assess whether borrowed language is quoted or genuinely paraphrased, attributed to the correct source, and represented accurately. A character-count threshold cannot establish originality or plagiarism.
