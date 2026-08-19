# Independent candidate v1 result

This candidate was written without reading the repository's other suites and
was executed once before tuning. It is retained as failed development evidence,
not as a passing release gate.

First-run result: **FAIL**.

- Dataset digest: `sha256:0b6a6e3589e4eda78cd85419eac3b7e1d8afae05be4854d7215757f9dc23e02b`
- Report digest: `sha256:c7d34da4c2cd5bc38f4d06590c48f40090c27345b4bad89c804a70e5e479a4ca`
- Hit@k: `1.0`
- Top-1 accuracy: `1.0`
- False activation rate: `0.111111`
- Permission-denial correctness: `0.875`
- Rejection correctness: `0.666667`

The failure exposed a tokenizer flaw: common words could satisfy a two-token
lexical threshold and surface unrelated skills. The case was not edited after
the run. A later candidate must be created independently after the general
tokenizer fix and must be executed without tuning.
