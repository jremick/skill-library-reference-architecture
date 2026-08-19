# Level 3: governed retrieval service

Level 3 adds version-pinned activation, append-only lifecycle events,
content-bound generated bundles, telemetry redaction, evaluation gates, drift
detection, and rollback.

The governed service must reject stale registry, router, profile, and manifest
digests before retrieval. A verified earlier bundle may be restored, but a
fallback does not convert the failed current bundle into a pass.

Expected state path:

```text
registered -> policy-eligible -> retrieved candidate -> inspected -> activated
-> conditional resource loaded -> executed -> verified -> deactivated
```

Every transition binds the profile, source bundle, reason, and decision. Raw
prompts, secrets, absolute local paths, and tool payloads are excluded from the
default telemetry contract.

The `evidence/` directory contains one schema-valid, synthetic transition and
one redacted telemetry event. They demonstrate the contract shape only; they
are not production observations or evidence of real-world effectiveness.
