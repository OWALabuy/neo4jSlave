"""
测试 ECharts 转换器 (echarts_converter.py)
"""
import pytest
from app.echarts_converter import records_to_graph, normalize_records, build_table


class TestRecordsToGraph:
    """测试 Neo4j 记录转换为 ECharts 图数据"""

    def test_basic_node_conversion(self, sample_records):
        """测试基本节点转换"""
        nodes, links = records_to_graph(sample_records)
        
        # 应该有3个节点（Alice, Bob, TechCorp）
        assert len(nodes) == 3
        
        # 检查节点属性
        node_ids = {n["id"] for n in nodes}
        assert node_ids == {1, 2, 3}
        
        # 检查节点标签映射为 category
        categories = {n.get("category") for n in nodes}
        assert "Person" in categories
        assert "Company" in categories

    def test_basic_link_conversion(self, sample_records):
        """测试基本关系转换"""
        nodes, links = records_to_graph(sample_records)
        
        # 应该有2条边
        assert len(links) == 2
        
        # 检查边的属性
        link_types = {l.get("relation") for l in links}
        assert "KNOWS" in link_types
        assert "WORKS_AT" in link_types

    def test_node_deduplication(self, sample_records):
        """测试节点去重（Alice 出现两次）"""
        nodes, links = records_to_graph(sample_records)
        
        # Alice 应该只出现一次
        alice_nodes = [n for n in nodes if n.get("name") == "Alice"]
        assert len(alice_nodes) == 1

    def test_node_properties_preserved(self, sample_records):
        """测试节点属性被保留"""
        nodes, links = records_to_graph(sample_records)
        
        # 找到 Alice 节点
        alice = next((n for n in nodes if n.get("name") == "Alice"), None)
        assert alice is not None
        assert alice.get("age") == 30

    def test_link_properties_preserved(self, sample_records):
        """测试边的属性被保留"""
        nodes, links = records_to_graph(sample_records)
        
        # 找到 KNOWS 边
        knows_link = next((l for l in links if l.get("relation") == "KNOWS"), None)
        assert knows_link is not None
        assert knows_link.get("since") == 2020

    def test_empty_records(self):
        """测试空记录列表"""
        nodes, links = records_to_graph([])
        assert nodes == []
        assert links == []

    def test_single_node_no_relationship(self):
        """测试单节点无关系"""
        records = [{"n": {"id": 1, "name": "Alice", "labels": ["Person"]}}]
        nodes, links = records_to_graph(records)
        
        assert len(nodes) == 1
        assert len(links) == 0
        assert nodes[0]["name"] == "Alice"


class TestNormalizeRecords:
    """测试记录规范化"""

    def test_basic_normalization(self, sample_records, sample_keys):
        """测试基本规范化"""
        normalized = normalize_records(sample_records)
        
        assert isinstance(normalized, list)
        assert len(normalized) == len(sample_records)
        
        # 检查每条记录都是 dict
        for record in normalized:
            assert isinstance(record, dict)

    def test_empty_records_normalization(self):
        """测试空记录规范化"""
        normalized = normalize_records([])
        assert normalized == []


class TestBuildTable:
    """测试表格数据构建"""

    def test_basic_table(self, sample_records, sample_keys):
        """测试基本表格构建"""
        table = build_table(sample_records, sample_keys)
        
        # 应该有表头和数据
        assert "headers" in table
        assert "rows" in table
        
        # 表头应该包含所有 key
        for key in sample_keys:
            assert key in table["headers"]

    def test_table_row_count(self, sample_records, sample_keys):
        """测试表格行数"""
        table = build_table(sample_records, sample_keys)
        assert len(table["rows"]) == len(sample_records)

    def test_empty_table(self):
        """测试空表格"""
        table = build_table([], ["col1", "col2"])
        assert table["headers"] == ["col1", "col2"]
        assert table["rows"] == []
