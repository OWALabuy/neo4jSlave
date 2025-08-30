from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple
from neo4j import graph


def _node_id(n: graph.Node) -> str:
    return str(n.element_id) if hasattr(n, "element_id") else str(n.id)


def records_to_graph(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    nodes: List[Dict[str, Any]] = []
    links: List[Dict[str, Any]] = []
    seen_nodes: Set[str] = set()
    seen_edges: Set[str] = set()

    for rec in records:
        for value in rec.values():
            if isinstance(value, graph.Node):
                nid = _node_id(value)
                if nid not in seen_nodes:
                    nodes.append(
                        {
                            "id": nid,
                            "name": str(value.get("name", nid)),
                            "category": next(iter(value.labels), "Node"),
                            "symbolSize": 30,
                            "value": dict(value),
                        }
                    )
                    seen_nodes.add(nid)
            elif isinstance(value, graph.Relationship):
                src = _node_id(value.start_node)
                tgt = _node_id(value.end_node)
                edge_key = f"{src}->{tgt}:{value.type}"
                if edge_key not in seen_edges:
                    links.append(
                        {
                            "source": src,
                            "target": tgt,
                            "category": value.type,
                            "label": value.type,
                            "value": dict(value),
                        }
                    )
                    seen_edges.add(edge_key)

    return nodes, links


