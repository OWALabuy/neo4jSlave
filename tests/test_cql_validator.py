"""
测试 CQL 验证器 (cql_validator.py)
"""
import pytest
from app.cql_validator import is_readonly_cql, explain_safe


class TestIsReadonlyCQL:
    """测试只读 CQL 验证"""

    def test_simple_match_is_safe(self):
        """简单 MATCH 查询应该是安全的"""
        cql = "MATCH (n) RETURN n LIMIT 10"
        ok, reason = is_readonly_cql(cql)
        assert ok is True
        assert reason is None

    def test_match_with_params_is_safe(self):
        """带参数的 MATCH 查询应该是安全的"""
        cql = "MATCH (a:Person)-[r:KNOWS]->(b:Person) WHERE a.name = $name RETURN a, r, b"
        ok, reason = is_readonly_cql(cql)
        assert ok is True
        assert reason is None

    def test_optional_match_is_safe(self):
        """OPTIONAL MATCH 应该是安全的"""
        cql = "OPTIONAL MATCH (n:Person {id: $id}) RETURN n"
        ok, reason = is_readonly_cql(cql)
        assert ok is True

    def test_with_clause_is_safe(self):
        """WITH 子句应该是安全的"""
        cql = "WITH 1 AS x RETURN x"
        ok, reason = is_readonly_cql(cql)
        assert ok is True

    def test_create_is_blocked(self):
        """CREATE 应该被阻止"""
        cql = "CREATE (n:Person {name: 'Alice'})"
        ok, reason = is_readonly_cql(cql)
        assert ok is False
        assert "CREATE" in reason

    def test_merge_is_blocked(self):
        """MERGE 应该被阻止"""
        cql = "MERGE (n:Person {name: $name})"
        ok, reason = is_readonly_cql(cql)
        assert ok is False
        assert "MERGE" in reason

    def test_delete_is_blocked(self):
        """DELETE 应该被阻止"""
        cql = "MATCH (n) DELETE n"
        ok, reason = is_readonly_cql(cql)
        assert ok is False
        assert "DELETE" in reason

    def test_detach_delete_is_blocked(self):
        """DETACH DELETE 应该被阻止"""
        cql = "MATCH (n) DETACH DELETE n"
        ok, reason = is_readonly_cql(cql)
        assert ok is False
        # 实际返回的是匹配到的 pattern，可能是 DELETE 或 DETACH DELETE
        assert "DELETE" in reason

    def test_set_is_blocked(self):
        """SET 应该被阻止"""
        cql = "MATCH (n) SET n.age = 30"
        ok, reason = is_readonly_cql(cql)
        assert ok is False
        assert "SET" in reason

    def test_remove_is_blocked(self):
        """REMOVE 应该被阻止"""
        cql = "MATCH (n) REMOVE n.name"
        ok, reason = is_readonly_cql(cql)
        assert ok is False
        assert "REMOVE" in reason

    def test_drop_is_blocked(self):
        """DROP 应该被阻止"""
        cql = "DROP INDEX idx_name"
        ok, reason = is_readonly_cql(cql)
        assert ok is False
        assert "DROP" in reason

    def test_load_csv_is_blocked(self):
        """LOAD CSV 应该被阻止"""
        cql = "LOAD CSV FROM 'file.csv' AS row"
        ok, reason = is_readonly_cql(cql)
        assert ok is False
        # 实际返回的是正则 pattern，包含转义字符
        assert "LOAD" in reason and "CSV" in reason

    def test_call_dbms_is_blocked(self):
        """CALL dbms.* 应该被阻止"""
        cql = "CALL dbms.info()"
        ok, reason = is_readonly_cql(cql)
        assert ok is False
        # 实际返回的是正则 pattern，检查关键部分
        assert "CALL" in reason and "DBMS" in reason

    def test_case_insensitive_blocking(self):
        """大小写不敏感检查"""
        cql = "create (n:Person {name: 'Alice'})"
        ok, reason = is_readonly_cql(cql)
        assert ok is False
        assert "CREATE" in reason

    @pytest.mark.parametrize("cql", [
        "MATCH (n) RETURN n LIMIT 10",
        "MATCH (a:Person)-[r:KNOWS]->(b:Person) WHERE a.name = $name RETURN a, r, b",
        "MATCH (n) WHERE n.age > 25 RETURN n.name ORDER BY n.age DESC",
        "OPTIONAL MATCH (n:Person {id: $id}) RETURN n",
    ])
    def test_various_safe_queries(self, cql):
        """参数化测试各种安全查询"""
        ok, reason = is_readonly_cql(cql)
        assert ok is True
        assert reason is None


class TestExplainSafe:
    """测试 EXPLAIN 预检功能"""

    def test_explain_disabled_returns_true(self, monkeypatch):
        """EXPLAIN 禁用时返回 True"""
        monkeypatch.setattr("app.cql_validator.settings.ENABLE_EXPLAIN_VALIDATE", False)
        ok, reason = explain_safe("MATCH (n) RETURN n")
        assert ok is True
        assert reason is None
