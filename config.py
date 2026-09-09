from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  DB_URL: str
  DB_PORT: int
  DEBUG: bool = False

  model_config = SettingsConfigDict(env_file=".env")


settings = Settings()


db_url = settings.DB_URL
db_port = settings.DB_PORT
