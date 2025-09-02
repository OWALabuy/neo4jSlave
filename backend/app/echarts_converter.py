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

    def add_node(n: graph.Node) -> None:
        nid = _node_id(n)
        if nid in seen_nodes:
            return
        label = next(iter(n.labels), "Node")
        name = n.get("name") or n.get("Name") or nid
        nodes.append(
            {
                "id": nid,
                "name": str(name),
                "category": label,
                "symbolSize": 30,
                "value": dict(n),
            }
        )
        seen_nodes.add(nid)

    def add_rel(rel: graph.Relationship) -> None:
        src = _node_id(rel.start_node)
        tgt = _node_id(rel.end_node)
        edge_key = f"{src}->{tgt}:{rel.type}"
        if edge_key in seen_edges:
            return
        # 确保端点节点也在集合中
        add_node(rel.start_node)
        add_node(rel.end_node)
        links.append(
            {
                "source": src,
                "target": tgt,
                "category": rel.type,
                "label": rel.type,
                "value": dict(rel),
            }
        )
        seen_edges.add(edge_key)

    def dict_is_node(d: Dict[str, Any]) -> bool:
        # 经验规则：有 ID 或 Name/ name 等属性时，当作节点属性字典
        return isinstance(d, dict) and ("ID" in d or "Id" in d or "id" in d or "Name" in d or "name" in d)

    def infer_category(d: Dict[str, Any]) -> str:
        if "IsFollowMe" in d:
            return "recipe"
        if "MineTool" in d or "ToolLevel" in d:
            return "block"
        return "item"

    def get_node_key(d: Dict[str, Any]) -> str:
        nid = d.get("ID") or d.get("Id") or d.get("id")
        cat = infer_category(d)
        return f"{cat[0]}:{nid}" if nid is not None else (d.get("Name") or d.get("name") or str(hash(frozenset(d.items()))))

    def add_node_dict(d: Dict[str, Any]) -> str:
        nid = get_node_key(d)
        if nid in seen_nodes:
            return nid
        name = d.get("name") or d.get("Name") or nid
        cat = infer_category(d)
        nodes.append({
            "id": nid,
            "name": str(name),
            "category": cat,
            "symbolSize": 30,
            "value": d,
        })
        seen_nodes.add(nid)
        return nid

    def add_edge_by_type(src_id: str, tgt_id: str, rel_type: str, value: Dict[str, Any] | None = None) -> None:
        edge_key = f"{src_id}->{tgt_id}:{rel_type}"
        if edge_key in seen_edges:
            return
        links.append({
            "source": src_id,
            "target": tgt_id,
            "category": rel_type,
            "label": rel_type,
            "value": value or {},
        })
        seen_edges.add(edge_key)

    def extract(value: Any) -> None:
        # 直接的节点/关系
        if isinstance(value, graph.Node):
            add_node(value)
            return
        if isinstance(value, graph.Relationship):
            add_rel(value)
            return
        # 路径：展开其中的所有节点和关系
        if isinstance(value, graph.Path):
            for n in value.nodes:
                add_node(n)
            for r in value.relationships:
                add_rel(r)
            return
        # 字典节点（非路径）也应当被收集，以显示孤立节点
        if isinstance(value, dict) and dict_is_node(value):
            add_node_dict(value)
            return
        # 列表/元组：递归提取
        if isinstance(value, (list, tuple)):
            # 尝试识别形如 [nodeDict, 'REL', nodeDict, 'REL', nodeDict] 的路径序列
            if len(value) >= 3 and dict_is_node(value[0]):
                # 滚动窗口，一对 (节点, 关系, 节点) 形成一条边
                last_node_id: str | None = None
                idx = 0
                while idx < len(value):
                    item = value[idx]
                    if dict_is_node(item):
                        nid = add_node_dict(item)
                        if last_node_id is None:
                            last_node_id = nid
                        else:
                            # 如果连续两个节点，中间没有关系，跳过成边
                            last_node_id = nid
                        idx += 1
                        continue
                    # 关系类型（字符串）后应跟一个节点字典
                    if isinstance(item, str) and idx + 1 < len(value) and dict_is_node(value[idx + 1]) and last_node_id is not None:
                        next_nid = add_node_dict(value[idx + 1])
                        add_edge_by_type(last_node_id, next_nid, item)
                        last_node_id = next_nid
                        idx += 2
                        continue
                    # 其它情况递归尝试
                    extract(item)
                    idx += 1
                return
            # 非路径列表：逐项递归
            for v in value:
                extract(v)
            return
        # 其它类型（标量/字典等）忽略

    for rec in records:
        for value in rec.values():
            extract(value)

    return nodes, links


def normalize_value(value: Any) -> Any:
    # 规范化为可 JSON 序列化且保留语义的结构
    if isinstance(value, graph.Node):
        return {
            "kind": "node",
            "labels": list(value.labels),
            "properties": dict(value),
            "elementId": getattr(value, "element_id", None) or getattr(value, "elementId", None),
        }
    if isinstance(value, graph.Relationship):
        return {
            "kind": "relationship",
            "type": value.type,
            "properties": dict(value),
            "startElementId": getattr(value, "start_node", None) and (getattr(value.start_node, "element_id", None) or getattr(value.start_node, "elementId", None)),
            "endElementId": getattr(value, "end_node", None) and (getattr(value.end_node, "element_id", None) or getattr(value.end_node, "elementId", None)),
        }
    if isinstance(value, graph.Path):
        return {
            "kind": "path",
            "nodes": [normalize_value(n) for n in value.nodes],
            "relationships": [normalize_value(r) for r in value.relationships],
        }
    if isinstance(value, (list, tuple)):
        return [normalize_value(v) for v in value]
    if isinstance(value, dict):
        # 可能是属性字典（已被上游序列化丢失结构时）
        return {k: normalize_value(v) for k, v in value.items()}
    return value


def normalize_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{k: normalize_value(v) for k, v in rec.items()} for rec in records]


def build_table(records: List[Dict[str, Any]], keys: List[str]) -> Dict[str, Any]:
    # 将任意结果构造成 columns + rows，以支持前端表格展示
    columns = list(keys)
    rows: List[List[Any]] = []
    for rec in records:
        row = []
        for k in columns:
            v = rec.get(k)
            nv = normalize_value(v)
            # 将复杂对象压缩为简短字符串，便于表格阅读
            if isinstance(nv, dict) and nv.get("kind") == "node":
                labels = ':'.join(nv.get('labels', []))
                name = nv.get('properties', {}).get('Name') or nv.get('properties', {}).get('name')
                nid = nv.get('elementId') or ''
                row.append(f"(:{labels} {name or ''}) {nid}")
            elif isinstance(nv, dict) and nv.get("kind") == "relationship":
                rtype = nv.get('type')
                props = nv.get('properties', {})
                row.append(f"[:{rtype} {props}]")
            elif isinstance(nv, dict) and nv.get("kind") == "path":
                row.append("<path>")
            else:
                row.append(nv)
        rows.append(row)
    return {"columns": columns, "rows": rows}

