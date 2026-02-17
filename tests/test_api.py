"""
API 集成测试
使用 FastAPI TestClient 测试端点
"""
import pytest
from fastapi.testclient import TestClient

# 需要在 backend 目录下运行
import sys
from pathlib import Path
BACKEND_DIR = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def mock_neo4j_schema():
    """Mock Neo4j schema 数据"""
    return {
        "labels": ["Person", "Company", "Project"],
        "relTypes": ["KNOWS", "WORKS_AT", "MANAGES"]
    }


class TestHealthEndpoint:
    """测试健康检查端点"""

    def test_health_check(self, client):
        """测试 /health 端点"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestSchemaEndpoint:
    """测试 Schema 端点"""

    @patch("app.main.neo4j_client.get_schema")
    def test_get_schema(self, mock_get_schema, client, mock_neo4j_schema):
        """测试获取 schema"""
        mock_get_schema.return_value = mock_neo4j_schema
        
        response = client.get("/schema")
        assert response.status_code == 200
        data = response.json()
        assert "labels" in data
        assert "relTypes" in data


class TestRunCQLEndpoint:
    """测试 /run-cql 端点"""

    @patch("app.main.is_readonly_cql")
    @patch("app.main.explain_safe")
    @patch("app.main.neo4j_client.run_read")
    @patch("app.main.records_to_graph")
    def test_run_valid_cql(
        self, mock_records_to_graph, mock_run_read, 
        mock_explain_safe, mock_is_readonly, client
    ):
        """测试执行有效的只读 CQL"""
        # Mock 验证通过
        mock_is_readonly.return_value = (True, None)
        mock_explain_safe.return_value = (True, None)
        mock_run_read.return_value = ([{"n": {"id": 1}}], ["n"])
        mock_records_to_graph.return_value = (
            [{"id": 1, "name": "Test", "category": "Node"}],
            []
        )
        
        response = client.post("/run-cql", json={
            "cql": "MATCH (n) RETURN n LIMIT 10",
            "params": {}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "graph" in data

    @patch("app.main.is_readonly_cql")
    def test_run_unsafe_cql_blocked(self, mock_is_readonly, client):
        """测试不安全的 CQL 被阻止"""
        mock_is_readonly.return_value = (False, "包含写操作：CREATE")
        
        response = client.post("/run-cql", json={
            "cql": "CREATE (n:Person {name: 'Alice'})",
            "params": {}
        })
        
        assert response.status_code == 400

    def test_run_cql_missing_params(self, client):
        """测试缺少必需参数"""
        with patch("app.main.is_readonly_cql", return_value=(True, None)):
            with patch("app.main.explain_safe", return_value=(True, None)):
                response = client.post("/run-cql", json={
                    "cql": "MATCH (n {name: $name}) RETURN n",
                    "params": {}  # 缺少 $name
                })
                
                assert response.status_code == 400
                assert "missing" in response.json()["detail"]


class TestNLQEndpoint:
    """测试自然语言查询端点 /nlq"""

    @patch("app.main.llm_client.generate_cypher")
    @patch("app.main.is_readonly_cql")
    @patch("app.main.explain_safe")
    @patch("app.main.neo4j_client.run_read")
    def test_nlq_success(
        self, mock_run_read, mock_explain_safe, 
        mock_is_readonly, mock_generate_cypher, client
    ):
        """测试 NLQ 成功流程"""
        # Mock LLM 生成 CQL
        mock_generate_cypher.return_value = (
            "MATCH (n:Person) RETURN n LIMIT 10",
            {}
        )
        mock_is_readonly.return_value = (True, None)
        mock_explain_safe.return_value = (True, None)
        mock_run_read.return_value = (
            [{"n": {"id": 1, "name": "Alice", "labels": ["Person"]}}],
            ["n"]
        )
        
        response = client.post("/nlq", json={
            "query": "查找所有人",
            "options": {"limit": 10}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "cql" in data
        assert "graph" in data

    @patch("app.main.llm_client.generate_cypher")
    def test_nlq_llm_fails(self, mock_generate_cypher, client):
        """测试 LLM 生成失败"""
        mock_generate_cypher.return_value = ("", {})
        
        response = client.post("/nlq", json={
            "query": "复杂查询"
        })
        
        assert response.status_code == 400
        assert "未生成" in response.json()["detail"]

    @patch("app.main.llm_client.generate_cypher")
    @patch("app.main.is_readonly_cql")
    def test_nlq_unsafe_cql_blocked(
        self, mock_is_readonly, mock_generate_cypher, client
    ):
        """测试 NLQ 生成的不安全 CQL 被阻止"""
        mock_generate_cypher.return_value = (
            "CREATE (n:Person {name: 'Alice'})",
            {}
        )
        mock_is_readonly.return_value = (False, "包含写操作")
        
        response = client.post("/nlq", json={
            "query": "创建一个人"
        })
        
        assert response.status_code == 400
