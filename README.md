## 最小可执行 NL → CQL → Neo4j → ECharts 产品

### 功能
- 输入自然语言，调用 LLM 生成只读 CQL
- 执行 Neo4j 查询（只读）
- 将结果转换为 ECharts Graph JSON 并在前端展示

### 目录结构
```
neo4jSlave/
  backend/
    app/
      __init__.py
      main.py
      config.py
      schemas.py
      llm_client.py
      neo4j_client.py
      cql_validator.py
      echarts_converter.py
  frontend/
    index.html
    app.js
  requirements.txt
  .env.example
```

### 先决条件
- Python 3.10+
- 已有可访问的 Neo4j 实例（建议只读账号）

### 快速开始（Linux *sh / Windows PowerShell）

最好是弄虚拟环境（linux必须弄 windows可选 反正windows没有包管 不需要考虑破坏包管环境）

Linux
```bash
python -m venv .venv
source ./.venv/bin/activate
pip install -r requirements.txt
#用你喜欢的文本编辑器编辑 .env
export $(grep -v '^#' .env | xargs)
#启动网页服务
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Windows
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# 编辑 .env，填入你的 NEO4J 与 LLM 配置
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

启动后访问：`http://localhost:8000` 打开可视化页面。

### 环境变量（.env）
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j

# LLM（OpenAI 兼容）：
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=sk-xxxx
LLM_MODEL=gpt-4o-mini

# 可选：启用 EXPLAIN 校验
ENABLE_EXPLAIN_VALIDATE=false

# 执行限制
QUERY_TIMEOUT_MS=5000
QUERY_HARD_LIMIT=200
```

### API 概览
- GET `/health` 健康检查
- GET `/schema` 返回标签与关系类型
- POST `/run-cql` 执行用户提供的只读 Cypher（请求字段名历史原因仍为 `cql`）
  - body: `{ "cql": "MATCH ...", "params": {"name": "Alice"} }`
- POST `/nlq` 自然语言 → Cypher → 执行 → ECharts JSON
  - body: `{ "query": "查找 Alice 的同事", "options": {"limit": 100} }`

### 提示词可控
在 `backend/app/llm_client.py` 中可调整系统提示与 few-shot 模板；也可通过 `.env` 动态切换模型与 Base URL。

### 安全与限制
- 强制只读：黑名单校验（禁止 CREATE/MERGE/DELETE/SET/LOAD 等）
- 可选 `EXPLAIN` 预检（启用 `ENABLE_EXPLAIN_VALIDATE=true`）
- 统一超时与返回行数限制，避免一次性大图卡死

### 前端
- 使用 ECharts 渲染 `graph`，支持展示 LLM 生成的 Cypher 与手动 Cypher 模式

### 论文与数据口径（重要）
- **节点/关系规模**：`doc/paper/main.tex` 中「知识图谱数据规模」表应与真实库一致。配置好 `.env` 后，在已安装项目依赖的虚拟环境中运行（示例：`source ~/pyenv/bin/activate`）：
  ```bash
  python scripts/neo4j_paper_stats.py
  ```
  将输出的计数与「互斥分类之和」「全库节点总数」核对后再改论文；若存在仅带其它标签的节点，二者可能不等，应在文中说明统计口径。
- **自然语言准确率**：pytest 中 `/nlq` 用例 **Mock 了 LLM**，通过只说明链路正确，**不**代表真实 NL 准确率。人工 21 条评测请在 `doc/paper/nlq_eval_protocol.md` 中固定模型、问句原文与「通过」标准，并与论文表 5-1 数字一致。

### 发展方向
- 路径查询、邻居展开、分页与聚类
- Schema 统计增强（属性 Top-N）
- 角色权限与审计日志

## 测试

### 测试框架
项目使用 **pytest** 进行单元测试和集成测试，确保代码质量和功能稳定性。

### 测试结构
```
tests/
├── conftest.py              # 测试 fixtures 和配置
├── test_cql_validator.py    # CQL 验证器单元测试
├── test_echarts_converter.py # ECharts 转换器测试
└── test_api.py              # API 集成测试 (使用 Mock)
```

### 运行测试

**一键运行所有测试：**
```bash
./run_tests.sh
```

**使用 pytest 直接运行：**
```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_cql_validator.py -v

# 运行特定测试类
python -m pytest tests/test_cql_validator.py::TestIsReadonlyCQL -v

# 显示覆盖率报告（需安装 pytest-cov）
python -m pytest tests/ --cov=backend/app --cov-report=html
```

### 测试覆盖范围

| 模块 | 测试内容 | 测试数量 |
|------|---------|---------|
| `cql_validator` | 只读 Cypher 验证、黑名单、`explain_safe` | 19 |
| `echarts_converter` | 图数据转换、表格构建 | 11 |
| `api` | 端点响应、错误处理、Mock 集成 | 8 |
| **合计** | | **38** |

### 编写新测试

参考 `tests/conftest.py` 中的 fixtures，使用示例：

```python
# tests/test_example.py
import pytest
from app.some_module import some_function

def test_something():
    result = some_function("input")
    assert result == "expected_output"

@pytest.mark.parametrize("input,expected", [
    ("input1", "output1"),
    ("input2", "output2"),
])
def test_multiple_cases(input, expected):
    assert some_function(input) == expected
```

### CI/CD 测试
在提交代码前，请确保：
1. 所有测试通过：`python -m pytest tests/`
2. 代码风格检查（推荐添加 `black` 和 `flake8`）
3. 类型检查（可选，使用 `mypy`）