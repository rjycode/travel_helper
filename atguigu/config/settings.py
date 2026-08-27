from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_DIR = Path(__file__).resolve().parents[2]

ENV_FILE_PATH = PROJECT_DIR / ".env"

print(ENV_FILE_PATH)

class Settings(BaseSettings):
    llm_model: str
    llm_base_url: str
    llm_api_key: str
    commerce_api_base_url: str
    database_url: str
    app_host: str
    app_port: int
    # 旅游平台数据服务（travel-data 后端）
    travel_api_base_url: str = "http://127.0.0.1:18082"
    # 客服自身会话状态库（与电商中台库分离，本机可访问）
    chat_database_url: str | None = None
    # 客服服务监听端口（避免与 travel-data 的 18082 冲突）
    chat_app_port: int = 18083

    model_config = SettingsConfigDict(env_file=ENV_FILE_PATH, env_file_encoding="utf-8", extra="ignore")


settings = Settings()

if __name__ == '__main__':
    print(settings.llm_model)
    print(settings.llm_base_url)
    print(settings.llm_api_key)
    print(type(settings.app_port))
