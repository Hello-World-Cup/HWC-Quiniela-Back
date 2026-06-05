from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL as DbURL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    db_driver: str = "postgresql+asyncpg"
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "quiniela"
    db_password: str = "quiniela_secret"
    db_name: str = "quiniela"

    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    google_client_id: str = ""
    google_client_secret: str = ""

    api_football_key: str = ""
    sync_cron_hour: int = 2
    sync_cron_minute: int = 0

    @property
    def database_url(self) -> DbURL:
        return DbURL.create(
            self.db_driver,
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )


settings = Settings()
