from __future__ import annotations

from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .schemas import NLQRequest, RunCQLRequest, NLQResponse, GraphPayload
from .neo4j_client import neo4j_client
from .cql_validator import is_readonly_cql, explain_safe
from .echarts_converter import records_to_graph
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

    try:
        records, _ = neo4j_client.run_read(payload.cql, payload.params or {})
        nodes, links = records_to_graph(records)
        return {
            "graph": {
                "nodes": nodes,
                "links": links,
                "meta": {"nodeCount": len(nodes), "linkCount": len(links)},
            }
        }
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/nlq", response_model=NLQResponse)
async def nlq(payload: NLQRequest) -> NLQResponse:
    schema_hint = neo4j_client.get_schema()
    limit = payload.options.limit if payload.options else settings.QUERY_HARD_LIMIT

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
        records, _ = neo4j_client.run_read(cql, params)
        nodes, links = records_to_graph(records)
        return NLQResponse(
            cql=cql,
            params=params or {},
            graph=GraphPayload(nodes=nodes, links=links, meta={"nodeCount": len(nodes), "linkCount": len(links)}),
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))
