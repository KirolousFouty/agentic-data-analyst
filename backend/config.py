from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://analyst_reader:analyst_reader_password@localhost:5432/analytics"
    database_admin_url: str = "postgresql+psycopg://analytics_admin:analytics_admin_password@localhost:5432/analytics"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:0.5b"
    sql_statement_timeout_ms: int = 5000
    sql_max_rows: int = 1000


settings = Settings()
