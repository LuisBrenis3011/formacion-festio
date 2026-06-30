from pydantic_settings import BaseSettings

LOCAL_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

class Settings(BaseSettings):
    APP_NAME: str = "Festio"
    DEBUG: bool = True
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    GEMINI_API_KEY: str
    
    # ─── MERCADO PAGO ──────────────────────────────────────────────────
    MERCADOPAGO_ACCESS_TOKEN: str
    MERCADOPAGO_PUBLIC_KEY: str | None = None
    # ───────────────────────────────────────────────────────────────────
    
    CORS_ALLOW_ORIGINS: str = ",".join(LOCAL_CORS_ORIGINS)
    CORS_ALLOW_ORIGIN_REGEX: str | None = r"^http://(localhost|127\.0\.0\.1):\d+$"

    @property
    def cors_allow_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ALLOW_ORIGINS.split(",") if origin.strip()]

    @property
    def cors_allow_origin_regex_value(self) -> str | None:
        if not self.CORS_ALLOW_ORIGIN_REGEX:
            return None
        value = self.CORS_ALLOW_ORIGIN_REGEX.strip()
        return value or None

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()