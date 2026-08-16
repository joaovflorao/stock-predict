from sqlalchemy.engine import URL
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "stock-predict"

    database_user: str
    database_password: str
    database_host: str
    database_port: int = 5432
    database_name: str

    model_config = SettingsConfigDict(env_file=".env")

    @computed_field
    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.database_user,
            password=self.database_password,
            host=self.database_host,
            port=self.database_port,
            database=self.database_name
        )


settings = Settings()
