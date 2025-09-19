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
- 可访问的 Neo4j 或阿里云 GDB 实例（建议只读账号）

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
# 在项目根新建 config.json，填入你的连接与 LLM 配置
New-Item -Path . -Name config.json -ItemType File

uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

启动后访问：`http://localhost:8000` 打开可视化页面。

### 配置文件（config.json）
放在项目根目录，示例：
```json
{
  "GRAPH_VENDOR": "gdb",                 
  "NEO4J_USE_DATABASE_PARAM": false,     
  "NEO4J_URI": "bolt://localhost:7687",
  "NEO4J_USER": "neo4j",
  "NEO4J_PASSWORD": "password",
  "NEO4J_DATABASE": "neo4j",

  "LLM_API_BASE": "https://ark.cn-beijing.volces.com/api/v3",
  "LLM_API_KEY": "",
  "LLM_MODEL": "Doubao-1.5-pro-32k",

  "ENABLE_EXPLAIN_VALIDATE": false,
  "QUERY_TIMEOUT_MS": 5000,
  "QUERY_HARD_LIMIT": 200
}
```

### API 概览
- GET `/health` 健康检查
- GET `/schema` 返回标签与关系类型
- POST `/run-cql` 执行用户提供的只读 CQL
  - body: `{ "cql": "MATCH ...", "params": {"name": "Alice"} }`
- POST `/nlq` 自然语言 → CQL → 执行 → ECharts JSON
  - body: `{ "query": "查找 Alice 的同事", "options": {"limit": 100} }`

### 提示词可控
在 `backend/app/llm_client.py` 中可调整系统提示与 few-shot 模板；也可通过 `.env` 动态切换模型与 Base URL。

### 安全与限制
- 强制只读：黑名单校验（禁止 CREATE/MERGE/DELETE/SET/LOAD 等）
- 可选 `EXPLAIN` 预检（启用 `ENABLE_EXPLAIN_VALIDATE=true`）
- 统一超时与返回行数限制，避免一次性大图卡死

### 前端
- 使用 ECharts 渲染 `graph`，支持展示生成的 CQL 与手动执行

### 发展方向
- 路径查询、邻居展开、分页与聚类
- Schema 统计增强（属性 Top-N）
- 角色权限与审计日志

### GDB 兼容说明（Neo4j 3.5.x 驱动）
- GDB 推荐使用 Neo4j Python 驱动 1.7.x（例如 1.7.6）。你可以执行：
  - `pip install -r requirements-neo4j17.txt`
- 使用上面的 `config.json` 配置：
  - `GRAPH_VENDOR` 设为 `gdb`
  - `NEO4J_USE_DATABASE_PARAM` 设为 `false`（GDB 无多数据库，传 `database` 会报错）