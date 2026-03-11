# pycg-rs as a CLI Primitive

## Positioning

`pycg-rs` should be treated as a focused CLI primitive inside a larger
LLM-augmented engineering workflow, not as a broad end-user application and
not as a general-purpose platform.

That framing implies a different standard for what matters:

- Fast enough to invoke constantly during code understanding and refactoring.
- Deterministic enough that downstream tools and agents can trust the output.
- Machine-readable first; human-readable formats are secondary.
- Composable in scripts and toolchains.
- Explicit about uncertainty, unsupported constructs, and partial results.

From this point of view, the job of `pycg-rs` is not just "generate a call
graph." The job is to provide a stable static-analysis primitive that helps
humans and LLMs answer narrow questions about a codebase quickly.

## Product Boundary

The project should be optimized as:

- A CLI first.
- Personal infrastructure first.
- A static-analysis building block for code understanding, refactoring, and
  maintenance workflows.

It should not be optimized first for:

- Broad library ergonomics.
- Large amounts of presentation/UI work.
- Expanding into many loosely-related output formats.
- Premature crate decomposition for small internal modules.

## What "Good" Looks Like

If the tool is succeeding in its intended role, a higher-level system should be
able to call it and reliably ask questions like:

- What symbols exist in this file, module, or package?
- What depends on this symbol?
- What does this symbol depend on?
- What changed structurally between two revisions?
- What code should I inspect next?
- What might break if I edit this function, class, or module?

That leads to five practical requirements.

## 1. Stable Machine Interface

The JSON output should be treated as the real product contract.

Important properties:

- Schema versioning.
- Stable field names.
- Stable ordering where practical.
- Well-defined node and edge kinds.
- Explicit metadata about analysis limits and skipped cases.

The current human-readable outputs are useful for inspection, but the
longer-term leverage is in having a stable machine interface that other tools
can consume directly.

## 2. Queryable CLI Surface

A useful primitive should answer narrow questions cheaply instead of forcing
every caller to dump and post-process a whole-repo graph.

Examples of higher-value commands or modes:

- `analyze` or `index`
- `summary <path-or-module>`
- `symbols-in <path-or-module>`
- `callers <symbol>`
- `callees <symbol>`
- `neighbors <symbol>`
- `path <src> <dst>`
- `impact <symbol>`
- `diff <rev-a> <rev-b>` or equivalent structural comparison mode

The exact command set can stay small. The important idea is that the CLI
surface should evolve toward focused graph queries, not just serialization.

## 3. Provenance and Explainability

Downstream LLM workflows benefit from traceability.

Whenever possible, results should carry:

- Fully qualified symbol identity.
- Source file path.
- Line number or span.
- Symbol kind.
- Enough provenance to explain why an edge exists.

If a higher-level tool asks "why does this edge exist?", the CLI should
eventually have at least a minimal answer beyond the bare edge itself.

## 4. Scope Control and Partial Analysis

LLM-assisted workflows are iterative and budget-sensitive.

The CLI becomes much more useful if callers can cheaply constrain work:

- Limit analysis to specific files, directories, or modules.
- Choose module-level versus symbol-level output.
- Focus on changed files or impacted regions.
- Request smaller summaries instead of whole-repo dumps.
- Reuse cached or indexed state later, if the implementation grows that way.

The goal is to make the primitive cheap to call many times during one larger
session.

## 5. Honest Uncertainty Reporting

Static analysis on Python will always have blind spots. Hiding them makes the
tool less useful inside automated loops.

The CLI should eventually make uncertainty visible:

- Unsupported or partially supported constructs encountered.
- Dynamic features that weaken precision.
- Incomplete edges or ambiguous resolutions.
- Summary counters for what was skipped or approximated.

This is not just documentation polish. It improves downstream decision-making.

## Strategic Priorities

Given the intended role of the project, the main investment areas should be:

1. Accuracy and coverage on realistic Python code.
2. Speed on medium and large codebases.
3. Queryability and machine-readable output quality.
4. Trust signals: tests, invariants, and explicit limitations.

## What Not to Overinvest In

These may still matter eventually, but they should not drive the roadmap now:

- Large-scale crate/workspace decomposition for code that is still compact.
- Extra output formats with little downstream leverage.
- Heavy emphasis on visual output polish.
- Generic platform abstractions that are not required by the CLI workflow.
- Distribution polish beyond what personal infrastructure usage needs.

## Working Definition of Done

The project can be considered "done enough" for its intended role when it is:

- Fast enough to invoke repeatedly on real repositories.
- Accurate enough to beat stale alternatives on representative workloads.
- Stable enough that downstream tooling can depend on its JSON contract.
- Honest enough about limits that automated consumers can adjust behavior.
- Queryable enough that larger systems do not need to reconstruct everything
  from a full graph dump.

At that point, the tool can move into a maintenance-first mode with targeted
improvements rather than broad feature development.
