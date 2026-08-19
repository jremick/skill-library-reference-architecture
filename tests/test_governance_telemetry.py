from __future__ import annotations

import copy
import unittest

from jsonschema import Draft202012Validator, FormatChecker

from tests.support import ROOT, load_data


class TelemetryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        schema = load_data(ROOT / "schemas" / "telemetry-event.schema.json")
        cls.validator = Draft202012Validator(schema, format_checker=FormatChecker())
        cls.example = load_data(
            ROOT / "examples" / "level-3-governed" / "evidence" / "telemetry-event.yaml"
        )

    def errors_for(self, event: dict[str, object]) -> list[str]:
        return [error.message for error in self.validator.iter_errors(event)]

    def test_synthetic_example_conforms_to_privacy_bounded_contract(self) -> None:
        self.assertEqual([], self.errors_for(self.example))

    def test_free_form_label_keys_and_values_are_rejected(self) -> None:
        event = copy.deepcopy(self.example)
        event["labels"] = {"prompt": "summarize a private customer record"}
        self.assertTrue(self.errors_for(event))

        event["labels"] = {"source": "customer-email-address"}
        self.assertTrue(self.errors_for(event))

    def test_raw_content_fields_are_rejected_at_every_bounded_object(self) -> None:
        mutations = (
            lambda event: event.update({"rawPrompt": "private prompt"}),
            lambda event: event["routing"].update({"toolArguments": "secret"}),
            lambda event: event["outcome"].update({"toolResult": "private result"}),
            lambda event: event["privacy"].update({"resourceContent": "private resource"}),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate.__code__.co_firstlineno):
                event = copy.deepcopy(self.example)
                mutate(event)
                self.assertTrue(self.errors_for(event))

    def test_non_synthetic_events_require_explicit_redaction_metadata(self) -> None:
        event = copy.deepcopy(self.example)
        event["privacy"]["classification"] = "internal"
        event["privacy"].pop("redactionPolicyVersion")
        self.assertTrue(self.errors_for(event))

        event["privacy"]["redactionPolicyVersion"] = "policy-2"
        event["privacy"]["redactionMethod"] = "allowlist"
        event["privacy"]["redacted"] = False
        self.assertTrue(self.errors_for(event))

        event["privacy"]["redacted"] = True
        self.assertEqual([], self.errors_for(event))


class PromotionPolicyBoundaryTests(unittest.TestCase):
    def test_policy_is_an_external_reference_checklist_not_a_cli_gate(self) -> None:
        policy = load_data(ROOT / "governance" / "promotion-policy.yaml")
        self.assertEqual("reference-checklist", policy["enforcement"]["status"])
        self.assertEqual("not-implemented", policy["enforcement"]["currentCli"])
        self.assertEqual(
            "external-review-required",
            policy["enforcement"]["publicAlphaAcceptance"],
        )
        self.assertEqual("not-evaluated", policy["configuration"]["unconfiguredGateResult"])


if __name__ == "__main__":
    unittest.main()
