# Explicit evaluation inventory

[evidence-quality.json](evidence-quality.json) records the twelve controls for the
offline probe assessment and resource report. Each case names executable tests and
its expected outcome. Run them through `python3 -B -m unittest discover -s tests -v`.
The suite also checks CLI wiring against a deterministic fake adapter.

EQ12 has two evidence sources: a synthetic replay in CI and a separately recorded
[offline CLI replay of the three historical real receipts](../docs/next-phase/evidence/offline-report-20260906/replay-controls.json).
CI does not launch containers or silently claim to reproduce the private originals.

This inventory covers the new infrastructure behavior. It does not replace the
operational-agent inventory on the separate housekeeping branch, nor establish
model quality, semantic acceptance or buyer validation.
