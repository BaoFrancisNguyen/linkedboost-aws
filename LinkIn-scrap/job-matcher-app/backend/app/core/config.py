# app/core/config.py
import os
from typing import List, Union
from pydantic import BaseSettings, validator
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "LinkedIn Job Matcher API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API pour le scraping LinkedIn et la gestion des offres d'emploi"
    
    # Server Configuration
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    DEBUG: bool = False
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database Configuration
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "linkedin_scraper")
    
    # JWT Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "votre_clé_secrète_très_sécurisée_à_changer_en_production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    
    # LinkedIn Configuration (optional)
    LINKEDIN_USERNAME: str = os.getenv("LINKEDIN_USERNAME", "")
    LINKEDIN_PASSWORD: str = os.getenv("LINKEDIN_PASSWORD", "")
    
    # Scraping Configuration
    MAX_SCRAPING_PAGES: int = int(os.getenv("MAX_SCRAPING_PAGES", "10"))
    SELENIUM_TIMEOUT: int = int(os.getenv("SELENIUM_TIMEOUT", "15"))
    SCRAPING_DELAY_MIN: float = float(os.getenv("SCRAPING_DELAY_MIN", "2.0"))
    SCRAPING_DELAY_MAX: float = float(os.getenv("SCRAPING_DELAY_MAX", "5.0"))
    
    # Email Configuration (optional)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Redis Configuration (optional, for future use)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# Instance globale des settings
settings = Settings()
