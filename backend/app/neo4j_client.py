from typing import Any, Dict, List, Tuple
from neo4j import GraphDatabase
from .config import settings


class Neo4jClient:
    def __init__(self) -> None:
        # 旧版驱动（1.7.x）没有 Driver 类型导出，避免显式类型依赖
        self._driver: Any = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )

    def close(self) -> None:
        if self._driver:
            self._driver.close()

    def _open_read_session(self):
        """打开只读会话，兼容 5.x/4.x/1.7.x 驱动与 GDB(3.5) 无 multi-db。

        优先按照 5.x 写法传参，遇到 TypeError 再降级；当 NEO4J_USE_DATABASE_PARAM=False 时不传 database。
        """
        use_db = bool(settings.NEO4J_USE_DATABASE_PARAM)
        database = settings.NEO4J_DATABASE if use_db else None
        # 5.x 风格：database + default_access_mode
        try:
            if database is not None:
                return self._driver.session(database=database, default_access_mode="READ")
            return self._driver.session(default_access_mode="READ")
        except TypeError:
            pass
        # 4.x/1.7 风格：access_mode=READ_ACCESS（或字符串 'READ' 也可）
        try:
            # 常量 READ_ACCESS 在 4.x 可用；为避免导入差异，这里直接传 'READ'
            if database is not None:
                return self._driver.session(database=database, access_mode="READ")
            return self._driver.session(access_mode="READ")
        except TypeError:
            pass
        # 最保守：不传任何额外参数
        return self._driver.session()

    def get_schema(self) -> Dict[str, List[str]]:
        with self._open_read_session() as session:
            labels = session.run("CALL db.labels()")
            rel_types = session.run("CALL db.relationshipTypes()")
            return {
                "labels": [r[0] for r in labels],
                "relTypes": [r[0] for r in rel_types],
            }

    def run_read(self, cql: str, params: Dict[str, Any] | None = None) -> Tuple[List[Dict[str, Any]], List[str]]:
        params = params or {}
        with self._open_read_session() as session:
            # 优先传超时，如不支持则降级为无超时
            timeout_seconds = settings.QUERY_TIMEOUT_MS / 1000.0
            try:
                result = session.run(cql, parameters=params, timeout=timeout_seconds)
            except TypeError:
                result = session.run(cql, parameters=params)
            keys = result.keys()
            records = [r.data() for r in result]
            return records, list(keys)

neo4j_client = Neo4jClient()

