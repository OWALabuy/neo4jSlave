from typing import Any, Dict, Optional, List
from pydantic import BaseModel


class NLQOptions(BaseModel):
    limit: Optional[int] = None
    debug_raw: Optional[bool] = False
    debug_raw: Optional[bool] = False


class NLQRequest(BaseModel):
    query: str
    options: Optional[NLQOptions] = None


class RunCQLRequest(BaseModel):
    cql: str
    params: Optional[Dict[str, Any]] = None
    raw: Optional[bool] = False
    raw: Optional[bool] = False


class GraphPayload(BaseModel):
    nodes: list
    links: list
    meta: Dict[str, Any]
    # categories 放在 graph 根层以兼容 ECharts 图例
    # 出于兼容性我们也把它放到 meta.categories 一份（不会强制要求）
    categories: Optional[list] = None


class NLQResponse(BaseModel):
    cql: str
    params: Dict[str, Any]
    graph: GraphPayload
    raw: Optional[List[Dict[str, Any]]] = None
    keys: Optional[List[str]] = None
    raw: Optional[List[Dict[str, Any]]] = None
    keys: Optional[List[str]] = None
