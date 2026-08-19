from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from skillref import check_public_surface
from tests.support import ROOT  # adds src/ to sys.path for source checkouts


class PrivacyTests(unittest.TestCase):
    def test_clean_synthetic_surface_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# Synthetic example\n", encoding="utf-8")
            report = check_public_surface(root)
        self.assertTrue(report["ok"])
        self.assertEqual([], report["findings"])

    def test_secret_and_machine_path_findings_are_value_safe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = "synthetic_secret_value_1234567890"
            machine_path = "/" + "Users" + "/sample-user/private/config.yaml"
            (root / "fixture.md").write_text(
                f"api_key={marker}\nsource={machine_path}\n", encoding="utf-8"
            )
            report = check_public_surface(root)

        self.assertFalse(report["ok"])
        self.assertEqual(
            {"credential-assignment", "machine-path"},
            {finding["category"] for finding in report["findings"]},
        )
        serialized = repr(report)
        self.assertNotIn(marker, serialized)
        self.assertNotIn("sample-user", serialized)

    def test_secret_bearing_dotfile_and_private_key_material_are_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = "synthetic_secret_value_1234567890"
            (root / ".env").write_text(f"PASSWORD={marker}\n", encoding="utf-8")
            private_key_header = "-----BEGIN " + "OPENSSH PRIVATE KEY-----"
            (root / "fixture.pem").write_text(f"{private_key_header}\n", encoding="utf-8")
            report = check_public_surface(root)

        self.assertFalse(report["ok"])
        self.assertTrue(
            {"credential-assignment", "private-key", "secret-bearing-file"}.issubset(
                {finding["category"] for finding in report["findings"]}
            )
        )
        self.assertNotIn(marker, repr(report))

    def test_extensionless_credentials_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "credentials").write_text("synthetic placeholder\n", encoding="utf-8")
            report = check_public_surface(root)

        self.assertFalse(report["ok"])
        self.assertIn("secret-bearing-file", {item["category"] for item in report["findings"]})

    def test_decode_error_fails_closed_without_returning_file_contents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "broken.txt").write_bytes(b"\xff\xfeprivate-value")
            report = check_public_surface(root)

        self.assertFalse(report["ok"])
        self.assertEqual("scan-error", report["findings"][0]["category"])
        self.assertNotIn("private-value", repr(report))

    def test_symlink_is_rejected_without_following_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ignored = root / ".venv"
            ignored.mkdir()
            target = ignored / "target.txt"
            target.write_text("synthetic public content\n", encoding="utf-8")
            (root / "linked.txt").symlink_to(target)
            report = check_public_surface(root)

        self.assertFalse(report["ok"])
        self.assertEqual({"symlink"}, {item["category"] for item in report["findings"]})
        self.assertEqual("linked.txt", report["findings"][0]["file"])

    def test_structured_non_public_labels_are_rejected_but_schema_enums_are_not(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "evidence.yaml").write_text(
                "input:\n  dataClassification: approved-private\n",
                encoding="utf-8",
            )
            (root / "schema.json").write_text(
                '{"properties":{"dataClassification":{"enum":["public","restricted"]}}}\n',
                encoding="utf-8",
            )
            report = check_public_surface(root)

        self.assertFalse(report["ok"])
        label_findings = [
            item for item in report["findings"] if item["category"] == "non-public-data-label"
        ]
        self.assertEqual(["evidence.yaml"], [item["file"] for item in label_findings])

    def test_findings_are_bounded_and_truncation_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = "synthetic_secret_value_1234567890"
            (root / "many.txt").write_text(
                "".join(f"password={marker}{index:03d}\n" for index in range(125)),
                encoding="utf-8",
            )
            report = check_public_surface(root)

        self.assertFalse(report["ok"])
        self.assertEqual(125, report["finding_count"])
        self.assertEqual(100, report["returned_finding_count"])
        self.assertEqual(100, len(report["findings"]))
        self.assertTrue(report["truncated"])
        self.assertNotIn(marker, repr(report))

    def test_current_public_surface_has_no_known_private_patterns(self) -> None:
        report = check_public_surface(ROOT)
        self.assertTrue(report["ok"], report["findings"])


if __name__ == "__main__":
    unittest.main()
