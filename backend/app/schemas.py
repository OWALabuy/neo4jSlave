from typing import Any, Dict, Optional
from pydantic import BaseModel


class NLQOptions(BaseModel):
    limit: Optional[int] = None


class NLQRequest(BaseModel):
    query: str
    options: Optional[NLQOptions] = None


class RunCQLRequest(BaseModel):
    cql: str
    params: Optional[Dict[str, Any]] = None


class GraphPayload(BaseModel):
    nodes: list
    links: list
    meta: Dict[str, Any]


class NLQResponse(BaseModel):
    cql: str
    params: Dict[str, Any]
    graph: GraphPayload
