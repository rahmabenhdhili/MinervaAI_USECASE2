from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    SECRET_KEY: str = "supersecretkey"
    JWT_ALGORITHM: str = "HS256"

settings = Settings()
