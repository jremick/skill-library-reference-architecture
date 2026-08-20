from __future__ import annotations

import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path

from skillref import compile_bundle
from skillref.compiler import write_bundle
from tests.support import ROOT

MARKDOWN_TARGET = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HTML_IMAGE_TARGET = re.compile(r'<img\b[^>]*\bsrc="([^"]+)"')


class RepositorySurfaceTests(unittest.TestCase):
    def test_readme_and_ci_use_the_same_validation_contract(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
        commands = (
            "uv sync --locked",
            "uv run skillref validate .",
            "uv run python -m unittest discover -s tests -v",
        )
        for command in commands:
            with self.subTest(command=command):
                self.assertIn(command, readme)
                self.assertIn(command, workflow)
        self.assertIn("uv run skillref check-public-surface .", workflow)

    def test_ci_is_read_only_and_has_a_stable_validate_job(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("\n  validate:\n", workflow)
        self.assertIn("needs:\n      - checks", workflow)
        self.assertNotIn("pull_request_target", workflow)
        self.assertNotIn("contents: write", workflow)

    def test_relative_markdown_links_resolve(self) -> None:
        failures: list[str] = []
        for document in sorted(ROOT.rglob("*.md")):
            if any(part.startswith(".") or part in {"build", "dist"} for part in document.parts):
                continue
            text = document.read_text(encoding="utf-8")
            targets = MARKDOWN_TARGET.findall(text) + HTML_IMAGE_TARGET.findall(text)
            for raw_target in targets:
                target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
                if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                    continue
                target = target.split("#", 1)[0]
                if target and not (document.parent / target).resolve().exists():
                    failures.append(f"{document.relative_to(ROOT)} -> {target}")
        self.assertEqual([], failures)

    def test_every_diagram_source_has_an_accessible_render(self) -> None:
        source_root = ROOT / "docs" / "diagrams" / "src"
        rendered_root = ROOT / "docs" / "diagrams" / "rendered"
        sources = {path.stem for path in source_root.glob("*.mmd")}
        renders = {path.stem for path in rendered_root.glob("*.svg")}
        self.assertEqual(sources, renders)
        self.assertTrue(sources)
        for name in sorted(sources):
            svg = (rendered_root / f"{name}.svg").read_text(encoding="utf-8")
            with self.subTest(diagram=name):
                self.assertIn("<title", svg)
                self.assertIn("<desc", svg)
                self.assertIn('role="graphics-document document"', svg)

    def test_diagram_renders_are_bound_to_sources(self) -> None:
        manifest = json.loads(
            (ROOT / "docs" / "diagrams" / "render-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual("skillref.diagram-render-manifest.v0alpha1", manifest["format"])
        source_names = {path.stem for path in (ROOT / "docs" / "diagrams" / "src").glob("*.mmd")}
        manifest_names = {diagram["name"] for diagram in manifest["diagrams"]}
        self.assertEqual(source_names, manifest_names)
        for diagram in manifest["diagrams"]:
            with self.subTest(diagram=diagram["name"]):
                source = ROOT / "docs" / "diagrams" / "src" / f"{diagram['name']}.mmd"
                render = ROOT / "docs" / "diagrams" / "rendered" / f"{diagram['name']}.svg"
                self.assertEqual(
                    diagram["source_sha256"], hashlib.sha256(source.read_bytes()).hexdigest()
                )
                self.assertEqual(
                    diagram["render_sha256"], hashlib.sha256(render.read_bytes()).hexdigest()
                )

    def test_social_preview_is_content_bound_and_1280_by_640(self) -> None:
        manifest = json.loads(
            (ROOT / "assets" / "render-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual("skillref.asset-render-manifest.v0alpha1", manifest["format"])
        source = ROOT / manifest["source"]
        render = ROOT / manifest["render"]
        self.assertEqual(manifest["source_sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertEqual(manifest["render_sha256"], hashlib.sha256(render.read_bytes()).hexdigest())
        png = render.read_bytes()
        self.assertEqual(b"\x89PNG\r\n\x1a\n", png[:8])
        width = int.from_bytes(png[16:20], "big")
        height = int.from_bytes(png[20:24], "big")
        self.assertEqual((1280, 640), (width, height))

    def test_readme_level_2_compile_example_is_reproducible(self) -> None:
        example = ROOT / "examples" / "level-2-retrieval"
        first = compile_bundle(example, "standard")
        second = compile_bundle(example, "standard")
        self.assertEqual(first, second)
        self.assertNotIn(
            "deployment-runner",
            first["lifecycle_states"]["router_retrievable"],
        )
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "bundle.json"
            write_bundle(first, output)
            self.assertTrue(output.is_file())

    def test_readme_teaches_level_1_and_level_2_agent_adoption_paths(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        required_targets = (
            "docs/diagrams/rendered/level-1-static-routing-in-practice.svg",
            "docs/diagrams/rendered/level-2-filtered-retrieval-in-practice.svg",
            "examples/level-1-static-router/skills/table-analysis/SKILL.md",
            "examples/level-1-static-router/skills/code-review/SKILL.md",
            "examples/level-2-retrieval/skills/deployment-review/SKILL.md",
            "examples/level-2-retrieval/skills/deployment-runner/SKILL.md",
            "docs/migration.md",
            "spec/README.md",
            "adapters/",
        )
        for target in required_targets:
            with self.subTest(target=target):
                self.assertIn(target, readme)
        self.assertIn("Quick start: use this with your AI assistant", readme)
        self.assertIn("Do not modify my system until I approve it.", readme)


if __name__ == "__main__":
    unittest.main()
