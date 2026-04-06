#!/usr/bin/env python3
"""
从 Neo4j 统计论文「数据规模」表所需数字，便于与 doc/paper/main.tex 对齐。

用法（与 backend 相同环境变量）：
  cd /path/to/neo4jSlave
  export NEO4J_URI=bolt://localhost:7687 NEO4J_USER=neo4j NEO4J_PASSWORD=...
  python3 scripts/neo4j_paper_stats.py

依赖：pip install neo4j python-dotenv
也可在已安装项目 requirements 的 venv 中运行。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# 加载仓库根目录 .env（与 backend 一致）
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # type: ignore[assignment]

_ROOT = Path(__file__).resolve().parents[1]
if load_dotenv:
    load_dotenv(_ROOT / ".env")

try:
    from neo4j import GraphDatabase
except ImportError:
    print("请先安装 neo4j 驱动：pip install neo4j", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    database = os.getenv("NEO4J_DATABASE", "neo4j")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        with driver.session(database=database, default_access_mode="READ") as session:

            def c1(q: str) -> int:
                v = session.run(q).single()
                return int(v[0]) if v and v[0] is not None else 0

            # 与论文表口径一致：互斥分类
            pure_item = c1(
                "MATCH (n:item) WHERE NOT n:block AND NOT n:monster RETURN count(n)"
            )
            blocks = c1("MATCH (n:item:block) RETURN count(n)")
            monsters = c1("MATCH (n:item:monster) RETURN count(n)")
            recipes = c1("MATCH (n:recipe) RETURN count(n)")
            groups = c1("MATCH (n:group) RETURN count(n)")
            smelts = c1("MATCH (n:smelt) RETURN count(n)")
            devices = c1("MATCH (n:device) RETURN count(n)")

            total_nodes = c1("MATCH (n) RETURN count(n)")
            total_rels = c1("MATCH ()-[r]->() RETURN count(r)")

            rows = {
                "pure_item_item_only": pure_item,
                "item_block": blocks,
                "item_monster": monsters,
                "recipe": recipes,
                "group": groups,
                "smelt": smelts,
                "device": devices,
                "sum_typed_rows": pure_item
                + blocks
                + monsters
                + recipes
                + groups
                + smelts
                + devices,
                "total_nodes_all_labels": total_nodes,
                "total_relationships": total_rels,
            }

        print(json.dumps(rows, ensure_ascii=False, indent=2))
        print("\n--- LaTeX 占比（占 sum_typed_rows，自行核对是否与 total_nodes 一致）---", file=sys.stderr)
        s = rows["sum_typed_rows"] or 1
        for name, val in [
            ("纯物品", pure_item),
            ("方块", blocks),
            ("生物", monsters),
            ("配方", recipes),
            ("分组", groups),
            ("熔炼", smelts),
            ("设备", devices),
        ]:
            pct = 100.0 * val / s
            print(f"  {name}: {val} ({pct:.2f}%)", file=sys.stderr)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
