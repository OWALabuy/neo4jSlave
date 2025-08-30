from __future__ import annotations

import re
from typing import Tuple
from .config import settings
from .neo4j_client import neo4j_client


WRITE_BLACKLIST = [
    r"\bCREATE\b",
    r"\bMERGE\b",
    r"\bDELETE\b",
    r"\bDETACH\s+DELETE\b",
    r"\bSET\b",
    r"\bREMOVE\b",
    r"\bDROP\b",
    r"\bLOAD\s+CSV\b",
    r"\bCALL\s+dbms\.",
]


def is_readonly_cql(cql: str) -> Tuple[bool, str | None]:
    upper = cql.upper()
    for pattern in WRITE_BLACKLIST:
        if re.search(pattern, upper):
            return False, f"CQL 包含潜在写操作：{pattern}"
    return True, None


def explain_safe(cql: str) -> Tuple[bool, str | None]:
    if not settings.ENABLE_EXPLAIN_VALIDATE:
        return True, None
    try:
        explain_cql = f"EXPLAIN {cql}"
        neo4j_client.run_read(explain_cql)
        return True, None
    except Exception as e:  # noqa: BLE001
        return False, f"EXPLAIN 校验失败：{e}"


