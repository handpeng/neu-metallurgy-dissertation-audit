#!/usr/bin/env python3
"""Inventory LaTeX equations and conservatively audit nearby definition blocks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


ENV_RE = re.compile(
    r"\\begin\{(equation\*?|align\*?|gather\*?|multline\*?)\}(.*?)\\end\{\1\}", re.DOTALL
)
LABEL_RE = re.compile(r"\\label\{([^}]+)\}")
REFERENCE_RE = re.compile(r"\\(eqref|ref)\{([^}]+)\}")
MARKER_RE = re.compile(
    r"(?P<gap>(?:\s|\\(?:noindent|par)\b)*)"
    r"(?P<marker>式中|其中)[ \t\u3000]*(?P<delimiter>[，,:：]?)[ \t\u3000]*"
)


def strip_comments(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines(keepends=True):
        cut = len(line)
        for index, character in enumerate(line):
            if character != "%":
                continue
            backslashes = 0
            cursor = index - 1
            while cursor >= 0 and line[cursor] == "\\":
                backslashes += 1
                cursor -= 1
            if backslashes % 2 == 0:
                cut = index
                break
        ending = "\n" if line.endswith("\n") else ""
        lines.append(line[:cut].rstrip("\r\n") + ending)
    return "".join(lines)


def source_files(path: Path) -> list[Path]:
    if path.is_file():
        if path.suffix.lower() != ".tex":
            raise ValueError("input file must have a .tex extension")
        return [path]
    if not path.is_dir():
        raise FileNotFoundError(path)
    files = sorted(candidate for candidate in path.rglob("*.tex") if candidate.is_file())
    if not files:
        raise ValueError("input directory contains no .tex files")
    return files


def definition_evidence(after: str) -> dict[str, object] | None:
    window = after[:1200]
    boundary = re.search(r"\\(?:begin\{|(?:sub)*section\{|chapter\{)", window)
    if boundary:
        window = window[: boundary.start()]
    match = MARKER_RE.match(window)
    if not match:
        return None
    line_end = window.find("\n", match.end())
    if line_end < 0:
        line_end = len(window)
    same_line = window[match.end() : line_end].strip()
    remaining = window[line_end + 1 :] if line_end < len(window) else ""
    next_line = ""
    for line in remaining.splitlines():
        candidate = line.strip()
        if candidate and not candidate.startswith("\\vspace"):
            next_line = candidate
            break
    definition_text = same_line or next_line
    delimiter_match = re.search(r"^.{0,50}?([：:—])", definition_text)
    gap = match.group("gap")
    return {
        "marker": match.group("marker"),
        "marker_delimiter": match.group("delimiter"),
        "same_line_remainder": same_line,
        "next_definition_line": next_line,
        "symbol_delimiter": delimiter_match.group(1) if delimiter_match else "",
        "paragraph_break_before_marker": bool(re.search(r"\n[ \t]*\n|\\par\b", gap)),
        "noindent_before_marker": bool(re.search(r"\\noindent\b", gap)),
        "indentation_status": "manual-review",
    }


def finding(message: str, suggestion: str, file: Path, line: int, evidence: str) -> dict[str, object]:
    return {
        "rule_id": "L40",
        "severity": "review",
        "check_type": "deterministic",
        "confidence": "medium",
        "file": str(file),
        "line": line,
        "evidence": re.sub(r"\s+", " ", evidence).strip()[:180],
        "message": message,
        "suggestion": suggestion,
    }


def inspect(path: Path, legacy_formula_definition_style: bool = False) -> dict[str, object]:
    files = source_files(path)
    equations: list[dict[str, object]] = []
    references: list[dict[str, object]] = []
    labels: list[tuple[str, Path, int]] = []
    all_source_labels: set[str] = set()
    for file in files:
        source = strip_comments(file.read_text(encoding="utf-8", errors="replace"))
        all_source_labels.update(LABEL_RE.findall(source))
        for match in ENV_RE.finditer(source):
            line = source.count("\n", 0, match.start()) + 1
            environment = match.group(1)
            found_labels = LABEL_RE.findall(match.group(2))
            for label in found_labels:
                labels.append((label, file, line))
            definition = definition_evidence(source[match.end() :])
            equations.append(
                {
                    "file": str(file),
                    "line": line,
                    "environment": environment,
                    "numbered_environment": not environment.endswith("*"),
                    "labels": found_labels,
                    "definition": definition,
                }
            )
        for reference in REFERENCE_RE.finditer(source):
            references.append(
                {
                    "label": reference.group(2),
                    "command": reference.group(1),
                    "file": str(file),
                    "line": source.count("\n", 0, reference.start()) + 1,
                }
            )

    label_counts = Counter(label for label, _, _ in labels)
    duplicate_labels = sorted(label for label, count in label_counts.items() if count > 1)
    known_labels = set(label_counts)
    formula_references = [
        reference
        for reference in references
        if reference["command"] == "eqref"
        or reference["label"] in known_labels
        or str(reference["label"]).lower().startswith(("eq:", "equation:"))
    ]
    unresolved_references = [
        reference for reference in formula_references if reference["label"] not in all_source_labels
    ]
    findings: list[dict[str, object]] = []
    if legacy_formula_definition_style:
        for equation in equations:
            definition = equation["definition"]
            if definition is None:
                continue
            file = Path(str(equation["file"]))
            line = int(equation["line"])
            evidence = f"{definition['marker']}{definition['marker_delimiter']} {definition['same_line_remainder']}"
            if definition["marker"] != "式中":
                findings.append(finding("The nearby definition block uses `其中` instead of `式中，`.", "Confirm the source tier before changing the marker.", file, line, evidence))
            if definition["marker_delimiter"] != "，":
                findings.append(finding("The definition marker does not use a full-width comma.", "Use `式中，` if the legacy convention applies.", file, line, evidence))
            if definition["same_line_remainder"]:
                findings.append(finding("Symbol definitions continue on the marker line.", "Move definitions to following indented line(s) if the legacy convention applies.", file, line, evidence))
            symbol_delimiter = definition["symbol_delimiter"]
            if symbol_delimiter == ":":
                findings.append(finding("A candidate symbol definition uses an ASCII colon.", "Use a full-width colon or em dash if the legacy convention applies.", file, line, str(definition["next_definition_line"] or definition["same_line_remainder"])))
            elif definition["next_definition_line"] and symbol_delimiter not in {"：", "—"}:
                findings.append(finding("No full-width colon or em dash was detected after the candidate symbol.", "Confirm the rendered definition and delimiter manually.", file, line, str(definition["next_definition_line"])))

    definition_status = "not-checked"
    definition_detail = "Enable --legacy-formula-definition-style only when the legacy convention applies."
    if legacy_formula_definition_style:
        definition_status = "findings" if findings else "manual-review"
        definition_detail = "Marker punctuation, line separation, and candidate symbol delimiters were checked; rendered indentation still requires manual confirmation."
    return {
        "input": str(path.resolve()),
        "files": [str(file) for file in files],
        "configuration": {"legacy_formula_definition_style": legacy_formula_definition_style},
        "summary": {
            "formula_environment_count": len(equations),
            "numbered_environment_count": sum(bool(item["numbered_environment"]) for item in equations),
            "labeled_environment_count": sum(bool(item["labels"]) for item in equations),
            "equation_label_count": len(labels),
            "formula_reference_count": len(formula_references),
            "definition_block_count": sum(item["definition"] is not None for item in equations),
            "duplicate_labels": duplicate_labels,
            "unresolved_references": unresolved_references,
            "finding_count": len(findings),
        },
        "equations": equations,
        "formula_coverage": {
            "inventory": {"status": "passed", "detail": "Supported display environments, labels, and nearby definition markers were inventoried."},
            "numbering": {"status": "findings" if duplicate_labels else "manual-review", "detail": "Duplicate labels were checked; compiled equation numbers and unlabeled numbering require PDF/AUX review."},
            "cross_references": {"status": "findings" if unresolved_references else "passed", "detail": "Source-level ref/eqref targets were compared with labels in the inspected source tree."},
            "rendering_layout": {"status": "manual-review", "detail": "Compiled output is required for centering, clipping, line breaks, and alignment."},
            "mathematical_typography": {"status": "manual-review", "detail": "Semantic italic/upright usage and glyph selection were not established."},
            "symbol_definition_closure": {"status": "manual-review", "detail": "Formula symbols were not semantically matched to definitions."},
            "definition_style": {"status": definition_status, "detail": definition_detail},
            "units": {"status": "manual-review", "detail": "Units require semantic and rendered review."},
            "scientific_coherence": {"status": "manual-review", "detail": "Dimensional and mathematical correctness were not established."},
        },
        "findings": findings,
        "limitations": [
            "Only equation, align, gather, and multline environments are inventoried.",
            "Macro expansion, included generated sources, compiled numbering, and rendered indentation are not resolved.",
            "Nearby definition association is conservative and does not prove symbol-definition closure.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="a .tex file or directory containing .tex files")
    parser.add_argument("--legacy-formula-definition-style", action="store_true")
    parser.add_argument("--output", type=Path, help="write JSON to this path instead of stdout")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = inspect(args.path, args.legacy_formula_definition_style)
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        return 0
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(f"inspect_tex_equations.py: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
