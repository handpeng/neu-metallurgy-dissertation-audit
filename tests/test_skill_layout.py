from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SkillLayoutTests(unittest.TestCase):
    def test_skill_frontmatter_and_references(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(skill.startswith("---\nname: neu-metallurgy-dissertation-audit\n"))
        self.assertNotIn("TODO", skill)
        self.assertIn("references/layout-audit.md", skill)
        self.assertIn("scripts/inspect_layout.py", skill)
        self.assertIn("scripts/inspect_tex_equations.py", skill)
        self.assertIn("formula coverage matrix", skill.lower())

    def test_local_markdown_links_resolve(self) -> None:
        for markdown in ROOT.rglob("*.md"):
            content = markdown.read_text(encoding="utf-8")
            for relative in re.findall(r"\[[^]]+\]\(([^)]+)\)", content):
                if relative.startswith(("http://", "https://", "#")):
                    continue
                target = relative.split("#", 1)[0]
                self.assertTrue((markdown.parent / target).exists(), f"{markdown}: {relative}")

    def test_crosswalk_has_every_substantive_row(self) -> None:
        crosswalk = (ROOT / "references" / "checklist-crosswalk.md").read_text(encoding="utf-8")
        found = {int(value) for value in re.findall(r"\| L(\d{2}) \|", crosswalk)}
        self.assertEqual(found, set(range(2, 58)))


if __name__ == "__main__":
    unittest.main()
