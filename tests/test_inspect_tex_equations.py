from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import inspect_tex_equations  # noqa: E402


class InspectTexEquationsTests(unittest.TestCase):
    def test_inventory_definition_style_and_references(self) -> None:
        source = r"""
\begin{equation}
  f_H = w[\%H]
  \label{eq:hydrogen}
\end{equation}

式中，
  $f_H$：氢在钢液中的相互作用系数；

\begin{align}
  T &= 1873 \label{eq:temperature}
\end{align}
其中，$T$: 钢液温度，K。

见式~\eqref{eq:hydrogen} 和 \eqref{eq:missing}。
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "chapter.tex"
            path.write_text(source, encoding="utf-8")
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            result = inspect_tex_equations.inspect(path, legacy_formula_definition_style=True)
            after = hashlib.sha256(path.read_bytes()).hexdigest()

            self.assertEqual(before, after)
            self.assertEqual(result["summary"]["formula_environment_count"], 2)
            self.assertEqual(result["summary"]["definition_block_count"], 2)
            self.assertEqual(len(result["summary"]["unresolved_references"]), 1)
            self.assertEqual(result["equations"][0]["definition"]["marker"], "式中")
            self.assertEqual(result["equations"][0]["definition"]["symbol_delimiter"], "：")
            messages = " ".join(item["message"] for item in result["findings"])
            self.assertIn("`其中`", messages)
            self.assertIn("ASCII colon", messages)
            self.assertEqual(result["formula_coverage"]["symbol_definition_closure"]["status"], "manual-review")
            self.assertEqual(result["formula_coverage"]["definition_style"]["status"], "findings")

    def test_duplicate_labels_and_default_legacy_status(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.tex").write_text("\\begin{equation}x\\label{eq:x}\\end{equation}\n", encoding="utf-8")
            (root / "b.tex").write_text("\\begin{equation}y\\label{eq:x}\\end{equation}\n", encoding="utf-8")
            result = inspect_tex_equations.inspect(root)

            self.assertEqual(result["summary"]["duplicate_labels"], ["eq:x"])
            self.assertEqual(result["formula_coverage"]["numbering"]["status"], "findings")
            self.assertEqual(result["formula_coverage"]["definition_style"]["status"], "not-checked")


if __name__ == "__main__":
    unittest.main()
