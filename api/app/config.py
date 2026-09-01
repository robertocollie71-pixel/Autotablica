from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "MunduroVehDB"
    APP_VERSION: str = "2.1.0"
    SECRET_KEY: str = "zmien-na-dlugi-losowy-klucz"
    DATABASE_URL: str = "sqlite:///./mundurovehdb.db"
    OFFICER_USER: str = "policja"
    OFFICER_PASSWORD: str = "demo123"
    ALLOWED_ORIGINS: str = "http://localhost:8080,http://127.0.0.1:8080,http://knieja.site,https://knieja.site,http://www.knieja.site,https://www.knieja.site"
    TOKEN_EXPIRE_MINUTES: int = 480


settings = Settings()
