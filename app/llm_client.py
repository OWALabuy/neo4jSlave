from __future__ import annotations

from typing import Any, Dict, Tuple
import httpx
from .config import settings


SYSTEM_PROMPT = (
    "你是 Neo4j Cypher 专家。只生成只读 CQL（MATCH/WHERE/RETURN/WITH/ORDER BY/LIMIT/OPTIONAL MATCH），"
    "禁止 CREATE/MERGE/DELETE/SET/LOAD。使用参数化变量（$param）。返回 JSON 格式：{\"cql\": str, \"params\": object}。"
)


class LLMClient:
    def __init__(self) -> None:
        self.api_base = settings.LLM_API_BASE.rstrip("/")
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL

    async def generate_cypher(self, nlq: str, schema_hint: Dict[str, Any], limit: int | None) -> Tuple[str, Dict[str, Any]]:
        user_prompt = {
            "role": "user",
            "content": (
                f"已知图谱 schema: labels={schema_hint.get('labels')}, relTypes={schema_hint.get('relTypes')}\n"
                f"请为以下需求编写只读 Cypher，并尽量添加 LIMIT（默认 {limit or '100'}）：\n{nlq}"
            ),
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    user_prompt,
                ],
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
            }
            resp = await client.post(f"{self.api_base}/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            import json as _json

            try:
                obj = _json.loads(content)
                cql = obj.get("cql", "").strip()
                params = obj.get("params", {})
            except Exception:  # noqa: BLE001
                cql = ""
                params = {}
            return cql, params


llm_client = LLMClient()


