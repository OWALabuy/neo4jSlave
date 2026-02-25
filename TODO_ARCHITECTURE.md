# 图数据库架构修改 - 后续任务清单

## 已完成 ✓
- [x] 清除Neo4j旧数据
- [x] 使用新架构重新灌库（多标签设计）
- [x] 验证数据结构（item:block 1936个, item:monster 262个）

## 待完成任务

### 1. Prompt重写（高优先级）
**原因**: 新架构使用多标签，不再需要PLACE/SUMMON关系

**修改内容**:
- [ ] 更新Schema描述：block和monster现在是item的子标签（:item:block, :item:monster）
- [ ] 移除/更新涉及PLACE、SUMMON关系的Few-shot示例
- [ ] 简化方块查询：直接MATCH (n:item:block)，无需通过PLACE关系
- [ ] 简化生物查询：直接MATCH (n:item:monster)，无需通过SUMMON关系
- [ ] 生物名称查询简化：现在monster节点有Name属性（通过item继承）

**示例变化**:
```cypher
-- 旧查询（通过关系）
MATCH (item)-[:PLACE]->(block:block) WHERE item.Name CONTAINS '石头'

-- 新查询（多标签）
MATCH (n:item:block) WHERE n.Name CONTAINS '石头'
```

### 2. 后端代码检查（中优先级）
**检查项**:
- [ ] `echarts_converter.py` - 是否需要适配新数据结构
- [ ] `neo4j_client.py` - 特别是get_schema()方法是否正确识别多标签
- [ ] `cql_validator.py` - 安全校验是否需要调整

### 3. 自然语言查询重新测试（高优先级）
**测试场景**:
- [ ] 方块查询："深积岩用什么挖" -> 应该更准确地生成查询
- [ ] 生物查询："野人有什么属性" -> 现在可以直接查monster属性
- [ ] 合成查询："木料能合成什么" -> 知识网查询

### 4. 论文更新（中优先级）
**更新章节**:
- [ ] 数据库设计章节 - 更新为多标签架构描述
- [ ] 关系类型表格 - 移除PLACE、SUMMON关系
- [ ] Prompt设计章节 - 更新Few-shot示例
- [ ] E-R图（如果有）- 更新为多标签模型

## 架构对比

### 旧架构（GDB兼容）
```
(:item) -[:PLACE]-> (:block)
(:item) -[:SUMMON]-> (:monster)
```
问题：需要维护额外关系和连接查询

### 新架构（Neo4j原生多标签）
```
(:item:block)     - 方块直接继承item属性
(:item:monster)   - 生物直接继承item属性
```
优势：
1. 架构更简单，查询更直接
2. 无需JOIN/关系遍历即可获取完整属性
3. CQL生成准确率应该更高
4. 符合Neo4j最佳实践

## 预期改进
- 方块查询准确率：从0% → 预计60%+
- 生物查询准确率：从50% → 预计80%+
- 整体准确率：从38% → 预计60%+

## 注意事项
- 多标签节点在CQL中用 `:item:block` 语法
- 查询属性时不需要关心是哪个标签，直接访问即可
- monster节点现在有Name属性（继承自item）
