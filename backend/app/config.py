import os
from dotenv import load_dotenv


load_dotenv()


class Settings:
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    NEO4J_DATABASE: str = os.getenv("NEO4J_DATABASE", "neo4j")

    LLM_API_BASE: str = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

    ENABLE_EXPLAIN_VALIDATE: bool = os.getenv("ENABLE_EXPLAIN_VALIDATE", "false").lower() == "true"
    QUERY_TIMEOUT_MS: int = int(os.getenv("QUERY_TIMEOUT_MS", "5000"))
    QUERY_HARD_LIMIT: int = int(os.getenv("QUERY_HARD_LIMIT", "200"))


settings = Settings()
