# Limitations and Uncertainty

This document explains where `pycg-rs` is reliable, where it is only partially
reliable, and how to interpret uncertainty in its JSON/query outputs.

The short version:

- Treat the graph as a strong static hint, not runtime truth.
- Always inspect `diagnostics` before using results for refactors.
- Missing edges do not prove absence of runtime coupling.
- Ambiguous or approximated edges mean "one of these" rather than "all of
  these are definitely called."

## What `pycg-rs` Is Good At

The tool is strongest on first-party Python package code with explicit symbol
definitions and relatively direct call flow.

Patterns that are generally high-confidence:

- module, class, function, and method definitions
- direct function and method calls
- relative and absolute imports inside the analyzed input set
- inheritance and MRO-based method lookup
- return-value propagation across straightforward helper chains
- `staticmethod`, `classmethod`, and `property` handling
- tuple/list destructuring and simple list/dict subscript flow
- symbol-level queries over package-style source trees

In practice, the best workflow is:

1. Use `symbols-in` on a file or module.
2. Pick an exact `canonical_name`.
3. Use `callees`, `callers`, `neighbors`, or `path`.
4. Read `diagnostics` before making refactor decisions.

## Partial / Lower-Confidence Areas

These patterns are not ignored, but the results are often incomplete,
approximate, or noisy:

- framework decorators such as Click/Typer-style CLI registration
- external-library-heavy code where most behavior lives on imported objects
- attribute-heavy OO code with lots of instance state and helper methods
- script-style repositories with many top-level effects or `main()` entrypoints
- star imports and wildcard expansion
- module-mode summaries on mixed script repos
- repos with non-package directory names that do not map cleanly to Python
  import paths

Real examples from local repos:

- `mission-control` produced a useful internal graph, but its Click-based CLI
  surface generated many unresolved names such as `group`, `command`, `option`,
  `echo`, and `getLogger`.
- `nwyin.com/tools/openprocessing` was reasonably queryable, while
  `build.py` and `tools/gen-art/render.py` produced many unresolved and
  external references because much of the behavior lives in object attributes,
  stdlib calls, Playwright, PIL, and other external APIs.

These are still useful for orientation, but they are lower-confidence inputs
for rename/move/delete refactors.

## Weak / Unsupported Areas

`pycg-rs` is not a full Python runtime model. It is weakest on patterns where
symbol identity is created or redirected dynamically.

Expect poor coverage or misleading confidence around:

- dynamic imports
- `getattr` / `setattr` / `delattr`-driven dispatch
- monkey patching and runtime method replacement
- metaprogramming and reflection-heavy frameworks
- `exec`, `eval`, runtime code generation, and string-based dispatch
- plugin/registration systems discovered indirectly at runtime
- environment/vendor directories included accidentally in the input set

For these cases, the graph can miss real edges, widen one edge into many
possibilities, or drop external behavior from the main graph entirely.

## How To Read `diagnostics`

The JSON graph and query contracts include a `diagnostics` section. This is the
main uncertainty surface. Use it.

### `external_references`

These are references to modules or imported symbols outside the analyzed input
set.

Typical causes:

- stdlib imports
- third-party packages
- sibling code not included in the current invocation

Interpretation:

- normal and expected at package boundaries
- not automatically a bug
- important because behavior behind those boundaries is not modeled deeply

High external-reference counts often mean the graph is still useful for
first-party structure, but weak for cross-boundary call reasoning.

### `unresolved_references`

These are uses the analyzer could not resolve to a concrete emitted node.

Typical causes:

- dynamic behavior
- builtin/function/method calls that are not modeled deeply
- unresolved object attributes
- names excluded from the analyzed input set
- framework/decorator indirection

Interpretation:

- more important than a raw edge count
- currently somewhat noisy
- should be treated as a "confidence down" signal, not a precise defect list

Not every unresolved reference is equally serious. On real repos, this can
include benign names like `len`, `str`, `echo`, or file/path helpers alongside
genuinely missing project-level links.

### `ambiguous_resolutions`

These mark cases where more than one concrete target remained plausible.

Interpretation:

- the graph is widened here
- use this as "one of these targets is likely involved"
- do not treat all returned targets as equally certain

This matters directly for refactors: ambiguous edges are not strong enough to
justify automated changes without inspection.

### `approximations`

These mark places where analysis intentionally widened the result to avoid
dropping all information.

Typical causes:

- wildcard expansion
- multi-return flow where several targets remain live

Interpretation:

- better than an empty result
- not evidence of a precise call edge

Approximation is useful for exploration, but it should lower your confidence
for edits with large blast radius.

### `warnings`

This is reserved for higher-level analysis warnings. It may be empty even when
the graph is low-confidence; do not treat `warnings == 0` as a proof of safety.

## Confidence Guide For Refactors

### Higher confidence

Use results more aggressively when most of these are true:

- you are querying first-party package code
- `symbols-in` finds a clean exact `canonical_name`
- `callees` / `callers` / `path` return the expected internal symbols
- diagnostics for the target area are low
- no ambiguity or approximation is reported

### Lower confidence

Slow down and inspect code manually when any of these are true:

- unresolved references cluster around the symbol you care about
- ambiguity or approximation is present
- most of the behavior crosses into external libraries
- the code is decorator-driven, framework-driven, or attribute-heavy
- you are looking only at module-mode output
- the repo includes script directories, generated files, or vendored/virtualenv
  code in the analysis input

### Things the graph does not prove

- A missing edge does not prove no runtime dependency exists.
- A present edge does not prove that exact call happens on every runtime path.
- A pretty DOT/text graph does not imply low uncertainty.
- Low diagnostics do not prove semantic correctness; they only mean the current
  analyzer had fewer obvious uncertainty signals.

## Operational Caveats

### Each query currently re-analyzes the input set

Today, `summary`, `symbols-in`, `callees`, `callers`, `neighbors`, and `path`
all trigger a fresh analysis run. This keeps the CLI simple, but it means:

- repeated query latency
- repeated stderr progress output
- repeated diagnostics computation

This is fine for now, but it matters for interactive workflows.

### JSON results are on stdout; progress/errors still use stderr

When scripting:

- parse stdout as the contract surface
- treat stderr as progress/human diagnostics

For example, JSON mode may still emit lines like `Analyzing 9 Python files...`
on stderr.

### Input hygiene matters

Do not aim the tool at a repo root blindly if that repo contains `.venv`,
vendored packages, generated code, or caches. Curate the analyzed file set or
set `--root` carefully.

On a messy repo, input sprawl can dominate the graph and make both diagnostics
and canonical names much less useful.

## Recommended Documentation Contract

For downstream users and future tools, the right mental model is:

- `pycg-rs` is a static-analysis primitive
- its outputs are useful for routing attention and estimating impact
- its results should inform refactors, not authorize them on their own

Use the graph to decide what to inspect next. Use the diagnostics to decide how
much to trust what you see.
