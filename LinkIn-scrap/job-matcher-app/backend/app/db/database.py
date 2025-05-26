# app/db/database.py
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

logger = logging.getLogger(__name__)

# Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "linkedin_scraper")

# Client global (sera initialisé au démarrage de l'app)
client: Optional[AsyncIOMotorClient] = None

async def connect_to_mongo():
    """Crée la connexion à MongoDB"""
    global client
    try:
        client = AsyncIOMotorClient(MONGODB_URI)
        # Test de la connexion
        await client.admin.command('ping')
        logger.info(f"✅ Connexion MongoDB établie: {MONGODB_URI}")
    except Exception as e:
        logger.error(f"❌ Erreur connexion MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Ferme la connexion à MongoDB"""
    global client
    if client:
        client.close()
        logger.info("🔄 Connexion MongoDB fermée")

async def get_database() -> AsyncIOMotorDatabase:
    """
    Retourne une instance de la base de données MongoDB.
    À utiliser dans les endpoints FastAPI.
    """
    global client
    if not client:
        await connect_to_mongo()
    return client[DB_NAME]

# Fonction de test de connexion synchrone
def test_mongo_connection() -> bool:
    """
    Teste la connexion à MongoDB (version synchrone)
    """
    try:
        test_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        test_client.admin.command('ping')
        test_client.close()
        logger.info("✅ Test connexion MongoDB réussi")
        return True
    except Exception as e:
        logger.error(f"❌ Test connexion MongoDB échoué: {e}")
        return False

# Fonction utilitaire pour obtenir une collection
async def get_collection(collection_name: str):
    """Retourne une collection spécifique"""
    db = await get_database()
    return db[collection_name]