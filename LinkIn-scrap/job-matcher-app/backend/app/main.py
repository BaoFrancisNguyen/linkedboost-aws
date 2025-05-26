# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.database import connect_to_mongo, close_mongo_connection
from app.api.router import api_router

# Configuration du logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)

# Gestionnaire de cycle de vie de l'application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire du cycle de vie de l'application"""
    # Démarrage
    logger.info("🚀 Démarrage de l'application")
    try:
        # Connexion à MongoDB
        await connect_to_mongo()
        logger.info("✅ Services initialisés")
        yield
    except Exception as e:
        logger.error(f"❌ Erreur lors du démarrage: {e}")
        raise
    finally:
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.database import connect_to_mongo, close_mongo_connection
from app.api.router import api_router

# Configuration du logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)

# Gestionnaire de cycle de vie de l'application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire du cycle de vie de l'application"""
    # Démarrage
    logger.info("🚀 Démarrage de l'application")
    try:
        # Connexion à MongoDB
        await connect_to_mongo()
        logger.info("✅ Services initialisés")
        yield
    except Exception as e:
        logger.error(f"❌ Erreur lors du démarrage: {e}")
        raise
    finally:
        # Arrêt
        logger.info("🔄 Arrêt de l'application")
        await close_mongo_connection()
        logger.info("✅ Services fermés")

# Création de l'application FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion du routeur principal
app.include_router(api_router, prefix=settings.API_V1_STR)

# Route de base
@app.get("/")
async def root():
    """Point d'entrée de l'API"""
    return {
        "message": f"Bienvenue sur {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
        "status": "running"
    }

# Route de santé
@app.get("/health")
async def health_check():
    """Vérification de l'état de l'application"""
    try:
        from app.db.database import get_database
        db = await get_database()
        await db.admin.command('ping')
        
        return {
            "status": "healthy",
            "database": "connected",
            "version": settings.VERSION
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )

# Gestionnaire d'erreur global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Gestionnaire d'erreur global"""
    logger.error(f"❌ Erreur non gérée: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "message": "Erreur interne du serveur",
            "detail": str(exc) if settings.DEBUG else "Une erreur inattendue s'est produite"
        }
    )

# Point d'entrée pour exécuter l'application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )