"""
测试配置与 fixtures
"""
import pytest
import sys
from pathlib import Path

# 将 backend 加入路径
BACKEND_DIR = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture
def sample_records():
    """示例 Neo4j 查询结果"""
    return [
        {
            "p": {
                "id": 1,
                "name": "Alice",
                "age": 30,
                "labels": ["Person"]
            },
            "r": {
                "type": "KNOWS",
                "properties": {"since": 2020}
            },
            "q": {
                "id": 2,
                "name": "Bob",
                "labels": ["Person"]
            }
        },
        {
            "p": {
                "id": 1,
                "name": "Alice",
                "age": 30,
                "labels": ["Person"]
            },
            "r": {
                "type": "WORKS_AT",
                "properties": {"role": "Engineer"}
            },
            "c": {
                "id": 3,
                "name": "TechCorp",
                "labels": ["Company"]
            }
        }
    ]


@pytest.fixture
def sample_keys():
    """示例查询结果列名"""
    return ["p", "r", "q", "c"]


@pytest.fixture
def readonly_cql_samples():
    """安全的只读 CQL 示例"""
    return [
        "MATCH (n) RETURN n LIMIT 10",
        "MATCH (a:Person)-[r:KNOWS]->(b:Person) WHERE a.name = $name RETURN a, r, b",
        "MATCH (n) WHERE n.age > 25 RETURN n.name ORDER BY n.age DESC",
        "OPTIONAL MATCH (n:Person {id: $id}) RETURN n",
        "WITH 1 AS x RETURN x",
    ]


@pytest.fixture
def unsafe_cql_samples():
    """不安全的写操作 CQL 示例"""
    return [
        ("CREATE (n:Person {name: 'Alice'})", "CREATE"),
        ("MERGE (n:Person {name: $name})", "MERGE"),
        ("MATCH (n) DELETE n", "DELETE"),
        ("MATCH (n) DETACH DELETE n", "DETACH DELETE"),
        ("MATCH (n) SET n.age = 30", "SET"),
        ("MATCH (n) REMOVE n.name", "REMOVE"),
        ("DROP INDEX idx_name", "DROP"),
        ("LOAD CSV FROM 'file.csv' AS row", "LOAD CSV"),
        ("CALL dbms.info()", "CALL dbms."),
    ]
