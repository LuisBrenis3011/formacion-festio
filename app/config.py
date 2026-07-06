from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Festio"
    DEBUG: bool = True
    
    # Base de datos
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # IA
    GEMINI_API_KEY: str
    
    # MERCADO PAGO
    MERCADOPAGO_ACCESS_TOKEN: str
    MERCADOPAGO_PUBLIC_KEY: str | None = None
    FRONTEND_URL: str
    
    # CORS
    CORS_ALLOW_ORIGINS: str
    CORS_ALLOW_ORIGIN_REGEX: str | None = None

    @property
    def cors_allow_origins_list(self) -> list[str]:
        # Convierte el string del .env en una lista real de Python
        origins = [origin.strip() for origin in self.CORS_ALLOW_ORIGINS.split(",") if origin.strip()]
        
        # Inyección dinámica: asegura que Vercel siempre esté permitido en CORS
        if self.FRONTEND_URL and self.FRONTEND_URL not in origins:
            origins.append(self.FRONTEND_URL.strip())
            
        return origins

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