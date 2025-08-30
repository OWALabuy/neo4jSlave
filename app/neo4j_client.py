from typing import Any, Dict, List, Tuple
from neo4j import GraphDatabase, Driver
from .config import settings


class Neo4jClient:
    def __init__(self) -> None:
        self._driver: Driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )

    def close(self) -> None:
        if self._driver:
            self._driver.close()

    def get_schema(self) -> Dict[str, List[str]]:
        with self._driver.session(database=settings.NEO4J_DATABASE, default_access_mode="READ") as session:
            labels = session.run("CALL db.labels()")
            rel_types = session.run("CALL db.relationshipTypes()")
            return {
                "labels": [r[0] for r in labels],
                "relTypes": [r[0] for r in rel_types],
            }

    def run_read(self, cql: str, params: Dict[str, Any] | None = None) -> Tuple[List[Dict[str, Any]], List[str]]:
        params = params or {}
        with self._driver.session(database=settings.NEO4J_DATABASE, default_access_mode="READ") as session:
            # Neo4j Python driver expects tx timeout in seconds (float)
            timeout_seconds = settings.QUERY_TIMEOUT_MS / 1000.0
            result = session.run(cql, parameters=params, timeout=timeout_seconds)
            keys = result.keys()
            records = [r.data() for r in result]
            return records, list(keys)


neo4j_client = Neo4jClient()


