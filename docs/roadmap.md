# Roadmap

## Intent

This roadmap assumes `pycg-rs` is primarily a CLI and is being built as a
static-analysis primitive inside broader LLM-augmented engineering workflows.

The project should not optimize for feature breadth by default. It should
optimize for a narrow claim:

- Faster than stale alternatives.
- Better accuracy and coverage on realistic Python code.
- More useful as a machine-consumable code-understanding tool.

## Current Phase

`pycg-rs` appears to be past the "prove the core idea" stage.

It already has:

- A working analyzer.
- Multiple output formats.
- CI and benchmark scaffolding.
- Corpus smoke coverage.
- Enough internal structure to support further hardening.

That suggests a maintenance-first development posture, but not a freeze.

The right mode is:

- Maintenance for generic call-graph functionality.
- Active development for workflow-critical capabilities.

## Priority Order

## 1. Accuracy and Coverage

This is the most important investment because it supports the project's core
claim and directly affects downstream trust.

Recommended work:

- Build a stronger semantic evaluation corpus.
- Add expected-edge and expected-absence fixtures where feasible.
- Compare against stale alternatives with a reproducible harness.
- Document unsupported patterns clearly instead of silently failing.
- Track regressions over time in CI or scheduled reports.

Questions to answer:

- On which classes of Python code does `pycg-rs` materially outperform other
  tools?
- Where does it remain weaker?
- What claims can be made honestly in the README and report site?

## 2. Performance on Real Workloads

Performance matters because this tool is meant to sit inside repeated analysis
loops.

Recommended work:

- Profile representative repositories instead of optimizing blindly.
- Continue improving hot paths only when profiles justify it.
- Preserve fast module-level workflows.
- Consider partial analysis or indexed execution later if repeated invocation
  becomes dominant.

The goal is not just a good benchmark table. The goal is a tool that feels
cheap enough to call constantly.

## 3. Query-Oriented CLI Design

Whole-graph export is useful, but it is not the highest-leverage interface for
agentic systems.

Recommended work:

- Define a small set of focused query commands.
- Add symbol/module/path filters.
- Add structural summaries suitable for routing downstream reasoning.
- Add graph neighborhood and path queries.
- Consider impact-analysis and revision-diff workflows if they match real use.

If a future LLM tool needs to decide what code to inspect next, this layer
should provide that cheaply.

## 4. JSON Contract and Provenance

If other tools depend on `pycg-rs`, the machine-readable interface becomes the
real API.

Recommended work:

- Add schema versioning.
- Make output ordering deterministic and documented.
- Include provenance fields consistently.
- Preserve stable node identity conventions.
- Add explicit analysis metadata for skipped or uncertain cases.

This is where the project becomes a dependable primitive rather than a useful
demo.

## 5. Testing and Trust Signals

Testing should evolve from "is the graph non-degenerate?" toward "does this
analysis support the claims we want to make?"

Recommended work:

- Tighten integration assertions.
- Expand corpus invariants.
- Add regression cases for tricky language features.
- Keep CLI snapshot coverage for stable output behavior.
- Prefer targeted semantic checks over weak count thresholds.

## 6. Maintenance and Refactoring

Refactoring remains important, but it should support correctness and velocity,
not become its own project.

Recommended work:

- Split oversized modules only when they are actively slowing development.
- Keep internal boundaries crisp where they support testing and profiling.
- Avoid workspace/crate decomposition unless a boundary is genuinely becoming
  public or independently reusable.

## Things Not Worth Heavy Investment Right Now

- Large amounts of visual presentation work.
- Many new export formats.
- Broad library API design.
- Packaging/distribution work beyond practical CLI use.
- Premature architectural decomposition of small modules.

## Suggested Allocation

For the next development tranche, a reasonable effort split is:

- 40% accuracy and coverage work.
- 30% query-oriented CLI work and JSON contract quality.
- 20% performance work driven by measurement.
- 10% maintenance, refactors, and documentation.

## Exit Criteria for Maintenance Mode

The project can move into a truer maintenance mode once these conditions are
mostly satisfied:

- Accuracy claims are backed by reproducible evidence.
- Performance is consistently good on the repositories that matter.
- The CLI exposes a small, stable set of query workflows.
- JSON output is stable enough for downstream tool integration.
- Known limitations are documented and surfaced honestly.

At that point, new work can become narrower and more selective:

- Fix regressions.
- Extend coverage for real encountered cases.
- Improve performance where it materially affects workflows.
- Add only those features that directly improve the primitive.
