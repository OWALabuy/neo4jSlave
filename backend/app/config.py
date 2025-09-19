import os
import json


def _as_bool(v: object, default: bool = False) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    if isinstance(v, str):
        return v.strip().lower() in ("1", "true", "yes", "on")
    return default


def _as_int(v: object, default: int) -> int:
    try:
        return int(v)  # type: ignore[arg-type]
    except Exception:
        return default


def _load_config() -> dict:
    path = os.path.join(os.getcwd(), "config.json")
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


class Settings:
    def __init__(self) -> None:
        cfg = _load_config()

        # 供应商与 multi-db 行为
        self.GRAPH_VENDOR: str = str(cfg.get("GRAPH_VENDOR", "neo4j")).lower()
        use_db_param = cfg.get("NEO4J_USE_DATABASE_PARAM")
        if use_db_param is None:
            self.NEO4J_USE_DATABASE_PARAM: bool = (self.GRAPH_VENDOR != "gdb")
        else:
            self.NEO4J_USE_DATABASE_PARAM = _as_bool(use_db_param, default=(self.GRAPH_VENDOR != "gdb"))

        # Neo4j/GDB 连接
        self.NEO4J_URI: str = str(cfg.get("NEO4J_URI", "bolt://localhost:7687"))
        self.NEO4J_USER: str = str(cfg.get("NEO4J_USER", "neo4j"))
        self.NEO4J_PASSWORD: str = str(cfg.get("NEO4J_PASSWORD", "password"))
        self.NEO4J_DATABASE: str = str(cfg.get("NEO4J_DATABASE", "neo4j"))

        # LLM 配置
        self.LLM_API_BASE: str = str(cfg.get("LLM_API_BASE", "https://ark.cn-beijing.volces.com/api/v3")).rstrip("/")
        self.LLM_API_KEY: str = str(cfg.get("LLM_API_KEY", ""))
        self.LLM_MODEL: str = str(cfg.get("LLM_MODEL", "Doubao-1.5-pro-32k"))

        # 执行与安全
        self.ENABLE_EXPLAIN_VALIDATE: bool = _as_bool(cfg.get("ENABLE_EXPLAIN_VALIDATE", False), default=False)
        self.QUERY_TIMEOUT_MS: int = _as_int(cfg.get("QUERY_TIMEOUT_MS", 5000), default=5000)
        self.QUERY_HARD_LIMIT: int = _as_int(cfg.get("QUERY_HARD_LIMIT", 200), default=200)


settings = Settings()
