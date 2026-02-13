from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    bot_token: str

    db_host: str = "postgres"
    db_port: int = 5432
    db_user: str = "qss_bot"
    db_pass: str = "changeme"
    db_name: str = "qss_service"

    log_level: str = "INFO"

    # Admin panel auth
    admin_login: str = "admin"
    admin_password: str = "changeme"
    secret_key: str = "changeme"

    @property
    def db_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_pass}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
