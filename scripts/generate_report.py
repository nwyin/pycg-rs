#!/usr/bin/env python3
"""Generate a self-contained HTML report for pycallgraph-rs.

Runs pycg --format json on each corpus, collects stats, and emits a single
index.html with inline CSS/JS.  Designed to be called from CI or locally:

    python scripts/generate_report.py --pycg ./target/release/pycg \
        --corpora benchmarks/corpora --out report/index.html

If --test-count is given (e.g. from `cargo test 2>&1 | tail -1`), it is
shown in the overview.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from html import escape
from pathlib import Path

# Mapping: corpus name -> subdirectory containing the Python package source.
# The generator tries these in order; first existing dir wins.
SOURCE_HINTS = {
    "black": ["src/black"],
    "flask": ["src/flask"],
    "httpx": ["httpx"],
    "requests": ["src/requests"],
    "rich": ["rich"],
    "pytest": ["src"],
    "click": ["src/click"],
    "pydantic": ["pydantic"],
    "fastapi": ["fastapi"],
}


def find_source_dir(corpus_dir: Path, name: str) -> Path | None:
    hints = SOURCE_HINTS.get(name, [name])
    for hint in hints:
        candidate = corpus_dir / hint
        if candidate.is_dir():
            return candidate
    # Fallback: look for <name>/__init__.py
    candidate = corpus_dir / name
    if candidate.is_dir():
        return candidate
    return None


def count_py_files(directory: Path) -> int:
    return sum(1 for _ in directory.rglob("*.py"))


def run_pycg(pycg_bin: str, source_dir: Path) -> dict | None:
    """Run pycg --format json on source_dir, return parsed JSON or None."""
    try:
        start = time.monotonic()
        result = subprocess.run(
            [pycg_bin, str(source_dir), "--format", "json"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        elapsed = time.monotonic() - start
        if result.returncode != 0:
            print(f"  [warn] pycg exited {result.returncode}: {result.stderr[:200]}", file=sys.stderr)
            return None
        data = json.loads(result.stdout)
        data["_elapsed_s"] = round(elapsed, 2)
        return data
    except subprocess.TimeoutExpired:
        print(f"  [warn] pycg timed out on {source_dir}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"  [warn] bad JSON from pycg: {e}", file=sys.stderr)
        return None


def run_cargo_test_count() -> int | None:
    """Run cargo test and count how many tests passed."""
    try:
        result = subprocess.run(
            ["cargo", "test", "--", "--format=terse"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        # Parse "test result: ok. 126 passed; 0 failed; ..."
        for line in result.stderr.splitlines() + result.stdout.splitlines():
            if "test result:" in line and "passed" in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if p == "passed;" and i > 0:
                        return int(parts[i - 1])
    except Exception:
        pass
    return None


def generate_html(corpora_results: list[dict], meta: dict) -> str:
    """Generate the full HTML report string."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Build summary table rows
    rows_html = ""
    for r in corpora_results:
        s = r.get("stats", {})
        elapsed = r.get("_elapsed_s", "—")
        py_files = r.get("_py_files", "—")
        status_class = "ok" if r.get("_success") else "fail"
        status_text = "ok" if r.get("_success") else "error"
        rows_html += f"""<tr class="{status_class}">
  <td class="name">{escape(r['name'])}</td>
  <td>{py_files}</td>
  <td>{s.get('files_analyzed', '—')}</td>
  <td>{s.get('total_nodes', '—')}</td>
  <td>{s.get('classes', '—')}</td>
  <td>{s.get('functions', '—')}</td>
  <td>{s.get('modules', '—')}</td>
  <td>{s.get('total_edges', '—')}</td>
  <td>{elapsed}s</td>
  <td class="status">{status_text}</td>
</tr>"""

    # Build edge detail sections
    details_html = ""
    for r in corpora_results:
        if not r.get("_success"):
            continue
        edges = r.get("edges", [])
        if not edges:
            continue
        edge_rows = ""
        for e in edges[:500]:  # cap at 500 for sanity
            edge_rows += f"<tr><td>{escape(e['source'])}</td><td>{escape(e['target'])}</td><td>{e['kind']}</td></tr>\n"
        total = len(r.get("edges", []))
        truncated = f' <span class="truncated">(showing 500 of {total})</span>' if total > 500 else ""
        details_html += f"""
<details class="corpus-detail" id="detail-{escape(r['name'])}">
  <summary>{escape(r['name'])} — {total} edges{truncated}</summary>
  <div class="search-box"><input type="text" placeholder="Filter edges..." onInput="filterTable(this)"></div>
  <table class="edge-table">
    <thead><tr><th>Source</th><th>Target</th><th>Kind</th></tr></thead>
    <tbody>{edge_rows}</tbody>
  </table>
</details>"""

    test_count = meta.get("test_count", "—")
    version = meta.get("version", "0.1.0")
    commit = meta.get("commit", "unknown")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>pycallgraph-rs — Analysis Report</title>
<style>
:root {{
  --bg: #0d1117;
  --surface: #161b22;
  --border: #30363d;
  --text: #e6edf3;
  --text-muted: #8b949e;
  --accent: #58a6ff;
  --green: #3fb950;
  --red: #f85149;
  --orange: #d29922;
  --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  --mono: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: var(--font);
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}}
h1 {{ font-size: 1.5rem; margin-bottom: 0.25rem; }}
.subtitle {{ color: var(--text-muted); font-size: 0.875rem; margin-bottom: 2rem; }}
.meta-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}}
.meta-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 1rem;
}}
.meta-card .label {{ color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }}
.meta-card .value {{ font-size: 1.5rem; font-weight: 600; font-family: var(--mono); }}
table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}}
th, td {{
  padding: 0.5rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--border);
}}
th {{ color: var(--text-muted); font-weight: 500; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; white-space: nowrap; }}
td {{ font-family: var(--mono); font-size: 0.8125rem; }}
td.name {{ font-weight: 600; color: var(--accent); }}
tr.ok td.status {{ color: var(--green); }}
tr.fail td.status {{ color: var(--red); }}
tr:hover {{ background: rgba(88,166,255,0.05); }}
.section {{ margin-top: 2.5rem; }}
.section h2 {{ font-size: 1.125rem; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--border); }}
details.corpus-detail {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  margin-bottom: 0.75rem;
}}
details.corpus-detail summary {{
  padding: 0.75rem 1rem;
  cursor: pointer;
  font-weight: 500;
  font-family: var(--mono);
  font-size: 0.875rem;
}}
details.corpus-detail summary:hover {{ color: var(--accent); }}
.edge-table {{ margin: 0; }}
.edge-table th, .edge-table td {{ padding: 0.375rem 0.75rem; font-size: 0.8125rem; }}
.search-box {{ padding: 0.5rem 0.75rem; }}
.search-box input {{
  width: 100%;
  padding: 0.375rem 0.625rem;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text);
  font-family: var(--mono);
  font-size: 0.8125rem;
}}
.search-box input:focus {{ outline: none; border-color: var(--accent); }}
.truncated {{ color: var(--text-muted); font-size: 0.75rem; }}
footer {{ margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border); color: var(--text-muted); font-size: 0.75rem; }}
</style>
</head>
<body>

<h1>pycallgraph-rs</h1>
<p class="subtitle">Static call graph analysis report — generated {now}</p>

<div class="meta-grid">
  <div class="meta-card">
    <div class="label">Version</div>
    <div class="value">{escape(version)}</div>
  </div>
  <div class="meta-card">
    <div class="label">Tests</div>
    <div class="value">{test_count}</div>
  </div>
  <div class="meta-card">
    <div class="label">Commit</div>
    <div class="value" style="font-size: 0.875rem">{escape(str(commit)[:8])}</div>
  </div>
</div>

<div class="section">
  <h2>Corpus Compatibility</h2>
  <table>
    <thead>
      <tr>
        <th>Project</th>
        <th>.py files</th>
        <th>Analyzed</th>
        <th>Nodes</th>
        <th>Classes</th>
        <th>Functions</th>
        <th>Modules</th>
        <th>Edges</th>
        <th>Time</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
</div>

<div class="section">
  <h2>Edge Details</h2>
  <p style="color: var(--text-muted); font-size: 0.8125rem; margin-bottom: 1rem;">Click a project to expand and search its resolved call edges.</p>
  {details_html}
</div>

<footer>
  Generated by <a href="https://github.com/tau/pycallgraph-rs" style="color: var(--accent);">pycallgraph-rs</a> report generator
</footer>

<script>
function filterTable(input) {{
  const query = input.value.toLowerCase();
  const tbody = input.closest('.corpus-detail').querySelector('tbody');
  for (const row of tbody.rows) {{
    const text = row.textContent.toLowerCase();
    row.style.display = text.includes(query) ? '' : 'none';
  }}
}}

// Sortable columns on main table
document.querySelector('table thead tr').addEventListener('click', function(e) {{
  const th = e.target.closest('th');
  if (!th) return;
  const table = th.closest('table');
  const tbody = table.querySelector('tbody');
  const rows = Array.from(tbody.rows);
  const idx = Array.from(th.parentNode.children).indexOf(th);
  const dir = th.dataset.sort === 'asc' ? -1 : 1;
  th.dataset.sort = dir === 1 ? 'asc' : 'desc';
  rows.sort((a, b) => {{
    let av = a.cells[idx].textContent.replace(/[^\d.]/g, '');
    let bv = b.cells[idx].textContent.replace(/[^\d.]/g, '');
    const an = parseFloat(av), bn = parseFloat(bv);
    if (!isNaN(an) && !isNaN(bn)) return (an - bn) * dir;
    return a.cells[idx].textContent.localeCompare(b.cells[idx].textContent) * dir;
  }});
  rows.forEach(r => tbody.appendChild(r));
}});
</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Generate pycallgraph-rs HTML report")
    parser.add_argument("--pycg", default="./target/release/pycg", help="Path to pycg binary")
    parser.add_argument("--corpora", default="benchmarks/corpora", help="Corpora directory")
    parser.add_argument("--out", default="report/index.html", help="Output HTML path")
    parser.add_argument("--test-count", type=int, default=None, help="Number of passing tests")
    parser.add_argument("--commit", default=None, help="Git commit hash")
    parser.add_argument("--version", default=None, help="Project version")
    args = parser.parse_args()

    corpora_dir = Path(args.corpora)
    if not corpora_dir.is_dir():
        print(f"Corpora directory not found: {corpora_dir}", file=sys.stderr)
        sys.exit(1)

    # Discover version from Cargo.toml if not given
    version = args.version
    if not version:
        try:
            cargo = Path("Cargo.toml").read_text()
            for line in cargo.splitlines():
                if line.startswith("version"):
                    version = line.split('"')[1]
                    break
        except Exception:
            version = "unknown"

    commit = args.commit
    if not commit:
        try:
            commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        except Exception:
            commit = "unknown"

    test_count = args.test_count
    if test_count is None:
        print("Counting tests...", file=sys.stderr)
        test_count = run_cargo_test_count() or "—"

    # Analyze each corpus
    results = []
    for corpus_name in sorted(os.listdir(corpora_dir)):
        corpus_path = corpora_dir / corpus_name
        if not corpus_path.is_dir():
            continue
        source_dir = find_source_dir(corpus_path, corpus_name)
        if not source_dir:
            print(f"  [skip] {corpus_name}: no source directory found", file=sys.stderr)
            continue

        py_count = count_py_files(source_dir)
        print(f"  Analyzing {corpus_name} ({py_count} .py files)...", file=sys.stderr)
        data = run_pycg(args.pycg, source_dir)

        if data:
            entry = {
                "name": corpus_name,
                "_py_files": py_count,
                "_success": True,
                "_elapsed_s": data.pop("_elapsed_s", "—"),
                "stats": data.get("stats", {}),
                "edges": data.get("edges", []),
            }
        else:
            entry = {
                "name": corpus_name,
                "_py_files": py_count,
                "_success": False,
            }
        results.append(entry)

    meta = {"test_count": test_count, "version": version, "commit": commit}
    html = generate_html(results, meta)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)
    print(f"Report written to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
