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
                #f"已知图谱 schema: labels={schema_hint.get('labels')}, relTypes={schema_hint.get('relTypes')}\n"
                '''
                领域图谱 Schema（仅供参考，不得臆造标签/属性/关系）：
                - 节点
                - :item {ID:int, Name:string, Type:int, Disc:string, GetWay:string}
                - :item:block {MineTool:int, ToolLevel:int} 继承 :item 全部属性
                - :item:monster {Life:int, Attack:int} 继承 :item；怪物蛋 item 的 ID-10000 = 怪物本体 ID
                - :group {ItemGroup:int}
                - :recipe {ID:int, IsFollowMe:int}（工作站：11000=随身，797=工匠台，150029=融合台，794=锅）
                - 关系（省略为空/为0的情况）
                - (:block)-[:TOOLMINEDROPS {prob}]->(:item)
                - (:block)-[:HANDMINEDROPS {prob}]->(:item)
                - (:block)-[:PreciseDrop]->(:item)
                - (:monster)-[:DROPS {prob, countMin, countMax, conditions, source}]->(:item)
                - (:item)-[:IN_GROUP]->(:group)
                - (:recipe)-[:CONSUMES {count}]->(:item|:block|:group)
                - (:recipe)-[:PRODUCES {count}]->(:item|:block)
                - (:recipe)-[:CONTAIN]->(:item|:block)

                生成 Cypher 时必须遵守：
                - 仅允许 MATCH / OPTIONAL MATCH / WHERE / WITH / RETURN / ORDER BY / LIMIT
                - 一律使用参数化：把字面量写为 $param（如 $name, $id, $limit）
                - 默认 LIMIT 100（若用户未指定），可通过参数调整
                - 不得使用 CREATE/MERGE/DELETE/SET/LOAD/CALL dbms.* 等写操作
                - 对含糊需求先提出澄清问题；不得臆测不存在的标签/属性/关系
                - 怪物蛋 item 的 ID-10000 = 怪物本体 ID 的规则可用于联结
                - 对于用户的需求，尽量返回路径而不是节点或关系的单项属性。
                - cql语句尽量简洁。
                - 返回 JSON：{"cql": string, "params": object}，不要输出其它文本
                '''
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
