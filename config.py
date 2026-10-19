from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  DB_URL: str
  DB_PORT: int
  DEBUG: bool = False
  JWT_SECRET_KEY: str
  JWT_ALGORITHM: str="HS256"
  JWT_EXPIRE_MIN: int=30
  RAZORPAY_KEY_ID: str
  RAZORPAY_KEY_SECRET: str

  model_config = SettingsConfigDict(env_file=".env")

settings = Settings()



