from __future__ import annotations

import re
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .schemas import NLQRequest, RunCQLRequest, NLQResponse, GraphPayload
from .neo4j_client import neo4j_client
from .cql_validator import is_readonly_cql, explain_safe
from .echarts_converter import records_to_graph, normalize_records, build_table
from .config import settings
from .llm_client import llm_client


app = FastAPI(title="NL → CQL → Neo4j → ECharts")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse("frontend/index.html")

@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok"}


@app.get("/schema")
def get_schema() -> Dict[str, Any]:
    return neo4j_client.get_schema()


@app.post("/run-cql")
def run_cql(payload: RunCQLRequest) -> Dict[str, Any]:
    ok, reason = is_readonly_cql(payload.cql)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)
    ok, reason = explain_safe(payload.cql)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)

    # 必需参数校验：解析 CQL 中的 $param 名称并检查 payload.params 是否包含
    try:
        required_params = set(re.findall(r"\$([A-Za-z_]\w*)", payload.cql))
        provided_params = set((payload.params or {}).keys())
        missing = sorted(required_params - provided_params)
        if missing:
            raise HTTPException(status_code=400, detail={"error": "缺少必需参数", "missing": missing})
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail={"error": "参数校验异常", "detail": str(e)})

    try:
        records, keys = neo4j_client.run_read(payload.cql, payload.params or {})
        nodes, links = records_to_graph(records)
        table = build_table(records, keys)
        categories = sorted({n.get("category", "Node") for n in nodes})
        categories_payload = [{"name": c} for c in categories]
        resp: Dict[str, Any] = {
            "graph": {
                "nodes": nodes,
                "links": links,
                "categories": categories_payload,
                "meta": {"nodeCount": len(nodes), "linkCount": len(links)},
            }
        }
        if payload.raw:
            resp["raw"] = normalize_records(records)
            resp["keys"] = keys
        resp["table"] = table
        return resp
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail={"error": str(e), "cql": payload.cql, "params": payload.params})


@app.post("/nlq", response_model=NLQResponse)
async def nlq(payload: NLQRequest) -> NLQResponse:
    schema_hint = neo4j_client.get_schema()
    limit = payload.options.limit if payload.options else settings.QUERY_HARD_LIMIT
    debug_raw = bool(payload.options.debug_raw) if payload.options else False

    cql, params = await llm_client.generate_cypher(payload.query, schema_hint, limit)
    if not cql:
        raise HTTPException(status_code=400, detail="LLM 未生成 CQL")

    ok, reason = is_readonly_cql(cql)
    if not ok:
        raise HTTPException(status_code=400, detail=f"生成的 CQL 不安全：{reason}")

    ok, reason = explain_safe(cql)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)

    try:
        # 同步执行生成的 CQL
        # 注意：生成的 CQL 也可能包含参数，若缺失会抛出 400（与 /run-cql 一致的语义可在后续复用函数）
        records, keys = neo4j_client.run_read(cql, params)
        nodes, links = records_to_graph(records)
        table = build_table(records, keys)
        categories = sorted({n.get("category", "Node") for n in nodes})
        categories_payload = [{"name": c} for c in categories]
        return NLQResponse(
            cql=cql,
            params=params or {},
            graph=GraphPayload(nodes=nodes, links=links, meta={"nodeCount": len(nodes), "linkCount": len(links), "categories": categories_payload}, categories=categories_payload),
            raw=(normalize_records(records) if debug_raw else None),
            keys=(keys if debug_raw else None),
            table=table,
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail={"error": str(e), "cql": cql, "params": params})
