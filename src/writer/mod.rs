//! Output writers for the visual call graph.
//!
//! Provides functions to serialize a [`VisualGraph`] into DOT (GraphViz),
//! TGF (Trivial Graph Format), plain text, and JSON.

use crate::node::{Node, NodeId};
use crate::visgraph::{VisualGraph, VisualNode};
use serde::Serialize;
use std::collections::{HashMap, HashSet};
use std::fmt::Write;

// ---------------------------------------------------------------------------
// DOT writer
// ---------------------------------------------------------------------------

/// Render the visual graph in GraphViz DOT format.
///
/// `options` is a list of extra top-level graph attributes (e.g.
/// `rankdir=LR`).  When the graph is grouped, `clusterrank="local"` is
/// appended automatically.
pub fn write_dot(graph: &VisualGraph, options: &[String]) -> String {
    let mut out = String::new();

    // Collect graph-level options.
    let mut opts: Vec<String> = options.to_vec();
    if graph.grouped {
        opts.push("clusterrank=\"local\"".to_string());
    }
    let opts_str = opts.join(", ");

    writeln!(out, "digraph G {{").unwrap();
    writeln!(out, "    graph [{opts_str}];").unwrap();

    if graph.grouped && !graph.subgraphs.is_empty() {
        for sg in &graph.subgraphs {
            write_dot_subgraph(&mut out, sg, 1);
        }
    } else {
        // No subgraphs – emit all nodes at root level.
        for node in &graph.nodes {
            write_dot_node(&mut out, node, 1);
        }
    }

    // Edges (always at root level).
    for edge in &graph.edges {
        let src = &graph.nodes[edge.source_idx];
        let tgt = &graph.nodes[edge.target_idx];
        let style = if edge.flavor == "defines" {
            "dashed"
        } else {
            "solid"
        };
        let color = &edge.color;
        writeln!(
            out,
            "    {} -> {} [style=\"{style}\", color=\"{color}\"];",
            src.id, tgt.id
        )
        .unwrap();
    }

    writeln!(out, "}}").unwrap();
    out
}

fn indent(level: usize) -> String {
    "    ".repeat(level)
}

fn write_dot_node(out: &mut String, node: &VisualNode, level: usize) {
    let pad = indent(level);
    writeln!(
        out,
        "{pad}{id} [label=\"{label}\", style=\"filled\", fillcolor=\"{fill}\", fontcolor=\"{text}\", group=\"{group}\"];",
        id = node.id,
        label = node.label,
        fill = node.fill_color,
        text = node.text_color,
        group = node.group,
    )
    .unwrap();
}

fn write_dot_subgraph(out: &mut String, sg: &VisualGraph, level: usize) {
    let pad = indent(level);
    writeln!(out, "{pad}subgraph cluster_{id} {{", id = sg.id).unwrap();

    let inner = indent(level + 1);
    writeln!(
        out,
        "{inner}graph [style=\"filled,rounded\", fillcolor=\"#80808018\", label=\"{label}\"];",
        label = sg.label,
    )
    .unwrap();

    for node in &sg.nodes {
        write_dot_node(out, node, level + 1);
    }

    for child in &sg.subgraphs {
        write_dot_subgraph(out, child, level + 1);
    }

    writeln!(out, "{pad}}}").unwrap();
}

// ---------------------------------------------------------------------------
// TGF writer
// ---------------------------------------------------------------------------

/// Render the visual graph in Trivial Graph Format.
///
/// Nodes are numbered sequentially starting at 1.
pub fn write_tgf(graph: &VisualGraph) -> String {
    let mut out = String::new();

    // Assign sequential 1-based IDs.
    for (i, node) in graph.nodes.iter().enumerate() {
        writeln!(out, "{} {}", i + 1, node.label).unwrap();
    }

    writeln!(out, "#").unwrap();

    for edge in &graph.edges {
        let tag = if edge.flavor == "uses" { "U" } else { "D" };
        writeln!(out, "{} {} {tag}", edge.source_idx + 1, edge.target_idx + 1).unwrap();
    }

    out
}

// ---------------------------------------------------------------------------
// Text writer
// ---------------------------------------------------------------------------

/// Render the visual graph as a plain-text dependency list.
///
/// Each source node is printed on its own line, followed by its outgoing
/// edges indented with `[D]` (defines) or `[U]` (uses) tags.  Output is
/// sorted alphabetically by source label, then by (tag, target label).
pub fn write_text(graph: &VisualGraph) -> String {
    use std::collections::BTreeMap;

    // Build adjacency: source label → sorted Vec<(tag, target label)>.
    let mut adj: BTreeMap<&str, Vec<(&str, &str)>> = BTreeMap::new();

    for edge in &graph.edges {
        let src_label = graph.nodes[edge.source_idx].label.as_str();
        let tgt_label = graph.nodes[edge.target_idx].label.as_str();
        let tag = if edge.flavor == "defines" { "D" } else { "U" };
        adj.entry(src_label).or_default().push((tag, tgt_label));
    }

    let mut out = String::new();
    for (src, targets) in &mut adj {
        targets.sort();
        writeln!(out, "{src}").unwrap();
        for (tag, tgt) in targets {
            writeln!(out, "    [{tag}] {tgt}").unwrap();
        }
    }

    out
}

// ---------------------------------------------------------------------------
// JSON writer
// ---------------------------------------------------------------------------

#[derive(Serialize)]
struct JsonNode {
    name: String,
    flavor: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    file: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    line: Option<usize>,
}

#[derive(Serialize)]
struct JsonEdge {
    source: String,
    target: String,
    kind: &'static str,
}

#[derive(Serialize)]
struct JsonGraph {
    nodes: Vec<JsonNode>,
    edges: Vec<JsonEdge>,
    stats: JsonStats,
}

#[derive(Serialize)]
struct JsonStats {
    total_nodes: usize,
    total_edges: usize,
    files_analyzed: usize,
    classes: usize,
    functions: usize,
    modules: usize,
}

/// Render the call graph directly as JSON.
///
/// Unlike the other writers which operate on the visual graph, this serializes
/// the raw call graph data for machine consumption.
pub fn write_json(
    nodes_arena: &[Node],
    defined: &HashSet<NodeId>,
    defines_edges: &HashMap<NodeId, HashSet<NodeId>>,
    uses_edges: &HashMap<NodeId, HashSet<NodeId>>,
) -> String {
    use crate::node::Flavor;

    let mut nodes = Vec::new();
    let mut sorted_ids: Vec<NodeId> = defined.iter().copied().collect();
    sorted_ids.sort_by(|&a, &b| {
        let na = &nodes_arena[a];
        let nb = &nodes_arena[b];
        (&na.namespace, &na.name).cmp(&(&nb.namespace, &nb.name))
    });

    let mut files: HashSet<&str> = HashSet::new();
    let mut classes = 0usize;
    let mut functions = 0usize;
    let mut modules = 0usize;

    for &id in &sorted_ids {
        let n = &nodes_arena[id];
        if let Some(ref f) = n.filename {
            files.insert(f.as_str());
        }
        match n.flavor {
            Flavor::Class => classes += 1,
            Flavor::Function | Flavor::Method | Flavor::StaticMethod | Flavor::ClassMethod => {
                functions += 1
            }
            Flavor::Module => modules += 1,
            _ => {}
        }
        nodes.push(JsonNode {
            name: n.get_name(),
            flavor: n.flavor.to_string(),
            file: n.filename.clone(),
            line: n.line,
        });
    }

    let defined_set: &HashSet<NodeId> = defined;
    let mut edges = Vec::new();

    for (&src, targets) in defines_edges {
        if !defined_set.contains(&src) {
            continue;
        }
        for &tgt in targets {
            if !defined_set.contains(&tgt) {
                continue;
            }
            edges.push(JsonEdge {
                source: nodes_arena[src].get_name(),
                target: nodes_arena[tgt].get_name(),
                kind: "defines",
            });
        }
    }

    for (&src, targets) in uses_edges {
        if !defined_set.contains(&src) {
            continue;
        }
        for &tgt in targets {
            if !defined_set.contains(&tgt) {
                continue;
            }
            edges.push(JsonEdge {
                source: nodes_arena[src].get_name(),
                target: nodes_arena[tgt].get_name(),
                kind: "uses",
            });
        }
    }

    edges.sort_by(|a, b| (&a.source, &a.target, a.kind).cmp(&(&b.source, &b.target, b.kind)));

    let graph = JsonGraph {
        stats: JsonStats {
            total_nodes: nodes.len(),
            total_edges: edges.len(),
            files_analyzed: files.len(),
            classes,
            functions,
            modules,
        },
        nodes,
        edges,
    };

    serde_json::to_string_pretty(&graph).expect("JSON serialization failed")
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use crate::node::{Flavor, Node};
    use crate::visgraph::VisualOptions;
    use std::collections::{HashMap, HashSet};

    fn make_test_graph() -> VisualGraph {
        let nodes_arena = vec![
            Node::new(Some("pkg"), "Foo", Flavor::Class).with_location("pkg.py", 1),
            Node::new(Some("pkg"), "bar", Flavor::Function).with_location("pkg.py", 10),
            Node::new(Some("other"), "baz", Flavor::Function).with_location("other.py", 5),
        ];
        let mut defined = HashSet::new();
        defined.insert(0);
        defined.insert(1);
        defined.insert(2);

        let mut uses = HashMap::new();
        uses.entry(0).or_insert_with(HashSet::new).insert(1);
        uses.entry(1).or_insert_with(HashSet::new).insert(2);

        let mut defines = HashMap::new();
        defines.entry(0).or_insert_with(HashSet::new).insert(1);

        let options = VisualOptions {
            draw_defines: true,
            draw_uses: true,
            colored: true,
            grouped: false,
            annotated: false,
        };

        VisualGraph::from_call_graph(&nodes_arena, &defined, &defines, &uses, &options)
    }

    #[test]
    fn test_dot_output_structure() {
        let g = make_test_graph();
        let dot = write_dot(&g, &["rankdir=TB".to_string()]);
        assert!(dot.starts_with("digraph G {"));
        assert!(dot.contains("rankdir=TB"));
        assert!(dot.contains("style=\"filled\""));
        assert!(dot.ends_with("}\n"));
    }

    #[test]
    fn test_dot_grouped() {
        let nodes_arena = vec![
            Node::new(Some("pkg"), "A", Flavor::Class).with_location("pkg.py", 1),
            Node::new(Some("other"), "B", Flavor::Function).with_location("other.py", 5),
        ];
        let mut defined = HashSet::new();
        defined.insert(0);
        defined.insert(1);

        let options = VisualOptions {
            draw_defines: false,
            draw_uses: false,
            colored: false,
            grouped: true,
            annotated: false,
        };

        let g = VisualGraph::from_call_graph(
            &nodes_arena,
            &defined,
            &HashMap::new(),
            &HashMap::new(),
            &options,
        );
        let dot = write_dot(&g, &[]);
        assert!(dot.contains("subgraph cluster_"));
        assert!(dot.contains("clusterrank=\"local\""));
    }

    #[test]
    fn test_tgf_output() {
        let g = make_test_graph();
        let tgf = write_tgf(&g);
        // Should contain node lines, separator, and edge lines.
        assert!(tgf.contains("#\n"));
        // Nodes are 1-indexed.
        assert!(tgf.contains("1 "));
    }

    #[test]
    fn test_text_output() {
        let g = make_test_graph();
        let text = write_text(&g);
        // Should contain [U] and [D] tags.
        assert!(text.contains("[U]") || text.contains("[D]"));
    }
}
