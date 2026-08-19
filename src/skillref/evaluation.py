"""Deterministic routing evaluation over synthetic cases."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

from . import __version__
from ._util import as_string_set, digest_value, load_structured, relative_posix
from .compiler import _is_canonical_registry, _records, _single_record, compile_bundle

TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:[_.-][a-z0-9]+)*", re.IGNORECASE)
STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "be",
        "do",
        "for",
        "from",
        "in",
        "into",
        "is",
        "it",
        "not",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "we",
        "with",
        "without",
    }
)

# This evaluator operates only on deterministic compiler output and lexical
# routing. These fields require a host/runtime evaluator with corresponding
# evidence and therefore fail closed here instead of being silently ignored.
UNSUPPORTED_EXPECTATION_FIELDS = frozenset(
    {
        "activation_state",
        "activationState",
        "expected_activation",
        "expected_loaded_resources",
        "expected_outcome",
        "expected_resources",
        "expected_resource_behavior",
        "expected_transitions",
        "outcome",
        "qualitative_rubric",
        "qualitativeRubric",
        "repetitions",
        "verification_ids",
        "verificationIds",
    }
)
SUPPORTED_EXPOSURES = frozenset({"prompt_visible", "router_retrievable"})


def _tokens(value: str) -> set[str]:
    return {
        token.lower() for token in TOKEN_PATTERN.findall(value) if token.lower() not in STOP_WORDS
    }


def _normalize_phrase(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split()).casefold()


def _matcher_terms(matchers: Any) -> tuple[set[str], set[str]]:
    any_terms: set[str] = set()
    all_terms: set[str] = set()
    if isinstance(matchers, str):
        any_terms |= _tokens(matchers)
    elif isinstance(matchers, list):
        for matcher in matchers:
            child_any, child_all = _matcher_terms(matcher)
            any_terms |= child_any
            all_terms |= child_all
    elif isinstance(matchers, dict):
        for key in ("keywords", "any", "any_keywords", "terms", "contains"):
            value = matchers.get(key)
            if isinstance(value, str):
                any_terms |= _tokens(value)
            elif isinstance(value, list):
                any_terms |= {str(item).lower() for item in value}
        for key in ("all", "all_keywords"):
            value = matchers.get(key)
            if isinstance(value, str):
                all_terms |= _tokens(value)
            elif isinstance(value, list):
                all_terms |= {str(item).lower() for item in value}
    return any_terms, all_terms


def _route(bundle: dict[str, Any], prompt: str, k: int) -> list[str]:
    prompt_tokens = _tokens(prompt)
    scores: dict[str, int] = {}
    priorities: dict[str, int] = {}
    router_allowed = set(bundle["lifecycle_states"]["router_retrievable"])
    prompt_allowed = set(bundle["lifecycle_states"]["prompt_visible"])
    allowed = router_allowed | prompt_allowed
    for route in bundle.get("routes", []):
        exact_matches = {
            alias.get("skill_id")
            for alias in route.get("exact_aliases", [])
            if isinstance(alias, dict)
            and _normalize_phrase(str(alias.get("phrase", ""))) == _normalize_phrase(prompt)
        }
        for skill_id in exact_matches:
            if isinstance(skill_id, str) and skill_id in allowed:
                scores[skill_id] = max(scores.get(skill_id, 0), 1000)
                priorities[skill_id] = max(
                    int(route.get("priority", 0)), priorities.get(skill_id, 0)
                )
        for rule in route.get("keyword_rules", []):
            if not isinstance(rule, dict):
                continue
            terms = {str(term).casefold() for term in rule.get("terms", [])}
            matches = (
                terms <= prompt_tokens
                if rule.get("match") == "all"
                else bool(terms & prompt_tokens)
            )
            skill_id = rule.get("skill_id")
            if matches and isinstance(skill_id, str) and skill_id in allowed:
                score = max(1, round(float(rule.get("weight", 1)) * 100))
                scores[skill_id] = max(scores.get(skill_id, 0), score)
                priorities[skill_id] = max(
                    int(route.get("priority", 0)), priorities.get(skill_id, 0)
                )
        any_terms, all_terms = _matcher_terms(route.get("matchers"))
        if all_terms and not all_terms <= prompt_tokens:
            continue
        matched = len(any_terms & prompt_tokens) + (2 * len(all_terms))
        if any_terms and matched == 0:
            continue
        if not any_terms and not all_terms:
            continue
        priority = int(route.get("priority", 0))
        for skill_id in route.get("candidate_skill_ids", []):
            if skill_id not in allowed:
                continue
            if matched > scores.get(skill_id, -1):
                scores[skill_id] = matched
            priorities[skill_id] = max(priority, priorities.get(skill_id, priority))

    # Lexical manifest metadata is a deterministic fallback and tie breaker.
    for skill in bundle.get("skills", []):
        skill_id = skill["skill_id"]
        if skill_id not in allowed:
            continue
        metadata = " ".join(
            [
                skill_id,
                str(skill.get("name", "")),
                str(skill.get("summary", "")),
                *skill.get("domains", []),
                *skill.get("capabilities", []),
                *skill.get("positive_triggers", []),
            ]
        )
        lexical = len(prompt_tokens & _tokens(metadata))
        # A single shared word is too weak to expose a candidate; it commonly
        # represents corpus boilerplate such as "synthetic" or "fictional".
        if lexical >= 2:
            scores[skill_id] = scores.get(skill_id, 0) + lexical
            priorities.setdefault(skill_id, 0)
    ordered = sorted(
        scores, key=lambda skill_id: (-scores[skill_id], -priorities[skill_id], skill_id)
    )
    return ordered[:k]


def _ratio(numerator: float, denominator: float) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def _unsupported_expectations(case: dict[str, Any]) -> list[str]:
    unsupported = set(case) & UNSUPPORTED_EXPECTATION_FIELDS
    expected_stage = case.get("expected_stage")
    if expected_stage is not None and expected_stage != "rejected":
        unsupported.add("expected_stage")
    if "expected_stage" in case and "expected_decision" in case:
        unsupported.add("expected_stage+expected_decision")
    expected_decision = case.get("expected_decision")
    if expected_decision is not None and expected_decision not in {"select", "reject"}:
        unsupported.add("expected_decision")
    expected_exposure = case.get("expected_exposure")
    if expected_exposure is not None and expected_exposure not in SUPPORTED_EXPOSURES:
        unsupported.add("expected_exposure")
    return sorted(unsupported)


def _expected_decision(case: dict[str, Any], expected: set[str]) -> str | None:
    decision = case.get("expected_decision")
    if decision in {"select", "reject"}:
        return str(decision)
    if case.get("expected_stage") == "rejected":
        return "reject"
    # Immutable historical candidates predate the explicit decision field.
    # Their non-empty expected set still carries an unambiguous selection
    # assertion, while an empty set without a rejection marker is denial-only.
    return "select" if expected else None


def _system_descriptor(
    bundle: dict[str, Any], level: int | None, profile_id: str
) -> dict[str, Any]:
    return {
        "architecture_level": level,
        "bundle_digest": bundle["bundle_digest"],
        "bundle_format": bundle["bundle_format"],
        "compiler_version": bundle["compiler_version"],
        "profile_digest": bundle["profile"]["profile_digest"],
        "profile_id": profile_id,
        "source_digest": bundle["source_digest"],
        "system_id": f"level-{level}-{profile_id}" if level is not None else f"root-{profile_id}",
    }


def _source_registered_skill_ids(root: Path) -> set[str]:
    """Read registry identity without projecting denied metadata into the bundle."""

    registry_record = _single_record(_records(root), "registry", required=True)
    assert registry_record is not None
    _, registry = registry_record
    canonical = _is_canonical_registry(registry)
    entries = registry.get("entries")
    if not isinstance(entries, list):
        raise ValueError("registry entries must be an array")
    registered: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        skill_id = entry.get("id") if canonical else entry.get("skill_id", entry.get("id"))
        if isinstance(skill_id, str):
            registered.add(skill_id)
    return registered


def _rankable_skill_ids(bundle: dict[str, Any], selected: set[str]) -> set[str]:
    """Collect every runtime/model-facing skill surface in a compiled bundle."""

    rankable = set(selected)
    rankable.update(
        str(item.get("skill_id"))
        for item in bundle.get("skills", [])
        if isinstance(item, dict) and isinstance(item.get("skill_id"), str)
    )
    for route in bundle.get("routes", []):
        if not isinstance(route, dict):
            continue
        rankable.update(as_string_set(route.get("candidate_skill_ids")))
        rankable.update(
            str(alias.get("skill_id"))
            for alias in route.get("exact_aliases", [])
            if isinstance(alias, dict) and isinstance(alias.get("skill_id"), str)
        )
        rankable.update(
            str(rule.get("skill_id"))
            for rule in route.get("keyword_rules", [])
            if isinstance(rule, dict) and isinstance(rule.get("skill_id"), str)
        )
    lifecycle = bundle.get("lifecycle_states", {})
    if isinstance(lifecycle, dict):
        for state in (
            "cached_eligible",
            "installed_cache_eligible",
            "installed_eligible",
            "policy_eligible",
            "prompt_visible",
            "registered_eligible",
            "router_retrievable",
        ):
            rankable.update(as_string_set(lifecycle.get(state)))
    return rankable


def evaluate_suite(root: str | Path, suite_path: str | Path) -> dict[str, Any]:
    root_path = Path(root).resolve()
    path = Path(suite_path)
    if not path.is_absolute():
        candidate = (root_path / path).resolve()
        path = candidate if candidate.exists() else path.resolve()
    suite = load_structured(path)
    if isinstance(suite, list):
        cases = suite
        suite_config: dict[str, Any] = {}
    elif isinstance(suite, dict):
        cases = suite.get("cases", [])
        suite_config = suite
    else:
        raise ValueError("evaluation suite must be an object or list")
    if not isinstance(cases, list) or not cases:
        raise ValueError("evaluation suite has no cases")
    default_profile = suite_config.get("profile_id")
    default_k = int(suite_config.get("k", 3))
    bundle_cache: dict[str, dict[str, Any]] = {}
    source_registry_cache: dict[str, set[str]] = {}
    system_cache: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []
    hit_total = top1_total = false_activations = candidate_total = 0
    positive_case_count = rejection_checks = rejection_correct = 0
    precision_total = recall_total = 0.0
    denial_checks = denial_correct = 0
    exposure_checks = exposure_correct = 0
    policy_checks = policy_correct = 0
    failures: list[str] = []

    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"evaluation case at index {index} is not an object")
        case_id = str(case.get("case_id", f"case-{index + 1}"))
        profile_id = case.get("profile_id", default_profile)
        if not isinstance(profile_id, str):
            raise ValueError(f"evaluation case {case_id} has no profile_id")
        level = case.get("level")
        case_root = root_path
        if isinstance(level, int) and (root_path / "examples").is_dir():
            level_roots = sorted((root_path / "examples").glob(f"level-{level}-*"))
            if len(level_roots) == 1:
                case_root = level_roots[0]
        cache_key = f"{case_root}:{profile_id}"
        if cache_key not in bundle_cache:
            bundle_cache[cache_key] = compile_bundle(case_root, profile_id)
        bundle = bundle_cache[cache_key]
        source_key = str(case_root)
        if source_key not in source_registry_cache:
            source_registry_cache[source_key] = _source_registered_skill_ids(case_root)
        architecture_level = level if isinstance(level, int) else None
        system = _system_descriptor(bundle, architecture_level, profile_id)
        system_cache[system["system_id"]] = system
        prompt = case.get("synthetic_prompt", case.get("query", case.get("prompt", "")))
        if not isinstance(prompt, str):
            raise ValueError(f"evaluation case {case_id} prompt must be a string")
        k = int(case.get("k", default_k))
        selected = _route(bundle, prompt, k)
        selected_set = set(selected)
        expected = as_string_set(case.get("expected_skill_ids"), ("skill_id", "id"))
        must_not = as_string_set(case.get("must_not_skill_ids"), ("skill_id", "id"))
        unsupported = _unsupported_expectations(case)
        if unsupported:
            failures.append(
                f"case {case_id} has unsupported expectations: {', '.join(unsupported)}"
            )
        expected_decision = _expected_decision(case, expected)
        intersection = selected_set & expected
        forbidden = selected_set & must_not
        hit = bool(intersection)
        top1 = bool(selected and selected[0] in expected)
        if expected:
            positive_case_count += 1
            hit_total += int(hit)
            top1_total += int(top1)
        false_activations += len(forbidden)
        candidate_total += len(selected)
        precision = _ratio(len(intersection), len(selected))
        recall = _ratio(len(intersection), len(expected))
        precision_total += precision
        recall_total += recall
        if must_not:
            denial_checks += 1
            denial_correct += int(not forbidden)
        if forbidden:
            failures.append(f"case {case_id} selected forbidden skills")
        if expected_decision == "select" and not hit:
            failures.append(f"case {case_id} did not select an expected skill")
        if expected_decision == "reject":
            rejection_checks += 1
            rejection_correct += int(not selected)
            if selected:
                failures.append(f"case {case_id} returned candidates but expected rejection")

        expected_exposure = case.get("expected_exposure")
        exposure_missing: list[str] = []
        exposure_matches: bool | None = None
        if expected_exposure in SUPPORTED_EXPOSURES:
            exposure_checks += 1
            exposed = set(bundle["lifecycle_states"].get(str(expected_exposure), []))
            exposure_missing = sorted(expected - exposed)
            exposure_matches = bool(expected) and not exposure_missing
            exposure_correct += int(exposure_matches)
            if not exposure_matches:
                failures.append(
                    f"case {case_id} expected skills do not have {expected_exposure} exposure"
                )

        expected_policy = case.get("expected_policy")
        policy_denied_expected: set[str] = set()
        policy_source_missing: list[str] = []
        policy_exclusion_leaked: list[str] = []
        policy_matches: bool | None = None
        if isinstance(expected_policy, dict):
            policy_checks += 1
            policy_denied_expected = as_string_set(
                expected_policy.get("denied_skill_ids"), ("skill_id", "id")
            )
            source_registered = source_registry_cache[source_key]
            rankable = _rankable_skill_ids(bundle, selected_set)
            policy_source_missing = sorted(policy_denied_expected - source_registered)
            policy_exclusion_leaked = sorted(policy_denied_expected & rankable)
            policy_matches = (
                bool(policy_denied_expected)
                and not policy_source_missing
                and not policy_exclusion_leaked
            )
            policy_correct += int(policy_matches)
            if not policy_matches:
                failures.append(
                    f"case {case_id} did not observe the expected pre-ranking policy exclusion"
                )
        results.append(
            {
                "case_id": case_id,
                "expected_decision": expected_decision,
                "expected_exposure": expected_exposure,
                "exposure_matches": exposure_matches,
                "exposure_missing_skill_ids": exposure_missing,
                "forbidden_selected": sorted(forbidden),
                "hit_at_k": hit,
                "precision_at_k": precision,
                "profile_id": profile_id,
                "policy_denied_expected": sorted(policy_denied_expected),
                "policy_exclusion_leaked_skill_ids": policy_exclusion_leaked,
                "policy_exclusion_matches": policy_matches,
                "policy_source_missing_skill_ids": policy_source_missing,
                "prompt_digest": digest_value(prompt),
                "recall_at_k": recall,
                "selected_skill_ids": selected,
                "system_bundle_digest": bundle["bundle_digest"],
                "system_id": system["system_id"],
                "top_1_correct": top1,
                "unsupported_expectations": unsupported,
            }
        )

    count = len(results)
    metrics = {
        "case_count": count,
        "exposure_cases": exposure_checks,
        "exposure_correctness": _ratio(exposure_correct, exposure_checks),
        "positive_case_count": positive_case_count,
        "false_activation_rate": _ratio(false_activations, candidate_total),
        "hit_at_k": _ratio(hit_total, positive_case_count),
        "mean_precision_at_k": _ratio(precision_total, positive_case_count),
        "mean_recall_at_k": _ratio(recall_total, positive_case_count),
        "permission_denied_correctness": _ratio(denial_correct, denial_checks),
        "permission_denied_cases": denial_checks,
        "policy_exclusion_cases": policy_checks,
        "policy_exclusion_correctness": _ratio(policy_correct, policy_checks),
        "rejection_correctness": _ratio(rejection_correct, rejection_checks),
        "rejection_cases": rejection_checks,
        "top_1_accuracy": _ratio(top1_total, positive_case_count),
    }
    thresholds = suite_config.get("thresholds", {})
    if isinstance(thresholds, dict):
        for metric, threshold in sorted(thresholds.items()):
            if metric not in metrics:
                failures.append(f"unknown configured threshold metric: {metric}")
                continue
            if not isinstance(threshold, (int, float)):
                failures.append(f"configured threshold for {metric} is not numeric")
                continue
            if metric in {"false_activation_rate"}:
                if metrics[metric] > threshold:
                    failures.append(f"{metric} exceeds configured maximum")
            elif metrics[metric] < threshold:
                failures.append(f"{metric} is below configured minimum")
    report: dict[str, Any] = {
        "command": "evaluate",
        "dataset_digest": digest_value(suite),
        "evaluator_scope": ["selection", "rejection", "exposure", "policy_exclusion"],
        "evaluator_version": __version__,
        "failures": sorted(set(failures)),
        "metrics": metrics,
        "ok": not failures and false_activations == 0 and rejection_correct == rejection_checks,
        "results": sorted(results, key=lambda item: item["case_id"]),
        "report_format": "skillref.evaluation-report.v0alpha1",
        "suite": relative_posix(path, root_path),
        "systems": sorted(system_cache.values(), key=lambda item: item["system_id"]),
    }
    report["report_digest"] = digest_value(report)
    return report
