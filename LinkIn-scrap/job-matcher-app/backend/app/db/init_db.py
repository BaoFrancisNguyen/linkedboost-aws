# app/db/init_db.py
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient, ASCENDING, TEXT
import os
import asyncio
import logging
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

logger = logging.getLogger(__name__)

# Récupération de l'URI MongoDB depuis les variables d'environnement
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "linkedin_scraper")

async def init_mongodb():
    """
    Initialise la base de données MongoDB avec toutes les collections et index nécessaires.
    """
    logger.info(f"🔧 Initialisation MongoDB: {MONGODB_URI}")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    
    try:
        # Test de connexion
        await client.admin.command('ping')
        logger.info("✅ Connexion MongoDB établie")
        
        # Liste des collections à créer
        collections = [
            "users",
            "connections", 
            "messages",
            "messageTemplates",
            "opportunities",
            "automations",
            "profileOptimizations",
            "analytics",
            "campaigns",
            "notifications",
            "jobs",
            "applications",
            "scraping_sessions",
            "recruiters"
        ]
        
        # Création des collections si elles n'existent pas
        existing_collections = await db.list_collection_names()
        for collection in collections:
            if collection not in existing_collections:
                logger.info(f"📁 Création collection: {collection}")
                await db.create_collection(collection)
        
        # Création des index
        await create_indexes(db)
        
        logger.info("🎉 Initialisation MongoDB terminée avec succès!")
        return client
        
    except Exception as e:
        logger.error(f"❌ Erreur initialisation MongoDB: {e}")
        raise
    
async def create_indexes(db):
    """Crée tous les index nécessaires"""
    logger.info("📊 Création des index...")
    
    try:
        # Index pour la collection users
        await db.users.create_index("email", unique=True, background=True)
        await db.users.create_index("linkedInId", sparse=True, background=True)
        await db.users.create_index("role", background=True)
        await db.users.create_index("isActive", background=True)
        logger.info("✅ Index users créés")
        
        # Index pour la collection connections
        await db.connections.create_index("userId", background=True)
        await db.connections.create_index("connectionId", background=True)
        await db.connections.create_index([("firstName", TEXT), ("lastName", TEXT)], background=True)
        await db.connections.create_index("status", background=True)
        logger.info("✅ Index connections créés")
        
        # Index pour la collection messages
        await db.messages.create_index("userId", background=True)
        await db.messages.create_index("connectionId", background=True)
        await db.messages.create_index("sentAt", background=True)
        await db.messages.create_index("status", background=True)
        logger.info("✅ Index messages créés")
        
        # Index pour la collection messageTemplates
        await db.messageTemplates.create_index("userId", background=True)
        await db.messageTemplates.create_index("category", background=True)
        logger.info("✅ Index messageTemplates créés")
        
        # Index pour la collection opportunities
        await db.opportunities.create_index("userId", background=True)
        await db.opportunities.create_index("relevanceScore", background=True)
        await db.opportunities.create_index("status", background=True)
        await db.opportunities.create_index("detectedAt", background=True)
        logger.info("✅ Index opportunities créés")
        
        # Index pour la collection automations
        await db.automations.create_index("userId", background=True)
        await db.automations.create_index("status", background=True)
        await db.automations.create_index("nextRun", background=True)
        await db.automations.create_index("type", background=True)
        logger.info("✅ Index automations créés")
        
        # Index pour la collection profileOptimizations
        await db.profileOptimizations.create_index("userId", background=True)
        await db.profileOptimizations.create_index("status", background=True)
        await db.profileOptimizations.create_index("category", background=True)
        logger.info("✅ Index profileOptimizations créés")
        
        # Index pour la collection analytics
        await db.analytics.create_index("userId", background=True)
        await db.analytics.create_index("date", background=True)
        await db.analytics.create_index("period", background=True)
        logger.info("✅ Index analytics créés")
        
        # Index pour la collection campaigns
        await db.campaigns.create_index("userId", background=True)
        await db.campaigns.create_index("status", background=True)
        await db.campaigns.create_index("startDate", background=True)
        logger.info("✅ Index campaigns créés")
        
        # Index pour la collection notifications
        await db.notifications.create_index("userId", background=True)
        await db.notifications.create_index("isRead", background=True)
        await db.notifications.create_index("createdAt", background=True)
        await db.notifications.create_index("type", background=True)
        logger.info("✅ Index notifications créés")
        
        # Index pour la collection jobs
        await db.jobs.create_index([("title", TEXT), ("description", TEXT)], background=True)
        await db.jobs.create_index("company", background=True)
        await db.jobs.create_index("location", background=True)
        await db.jobs.create_index("postedAt", background=True)
        await db.jobs.create_index("status", background=True)
        await db.jobs.create_index("remote", background=True)
        await db.jobs.create_index("type", background=True)
        await db.jobs.create_index("experienceLevel", background=True)
        await db.jobs.create_index("createdAt", background=True)
        
        # Index composé pour éviter les doublons
        await db.jobs.create_index([
            ("title", 1),
            ("company", 1), 
            ("location", 1)
        ], unique=True, background=True)
        logger.info("✅ Index jobs créés")
        
        # Index pour la collection applications
        await db.applications.create_index("userId", background=True)
        await db.applications.create_index("jobId", background=True)
        await db.applications.create_index("status", background=True)
        await db.applications.create_index("createdAt", background=True)
        
        # Index composé pour éviter les doublons de candidatures
        await db.applications.create_index([
            ("userId", 1),
            ("jobId", 1)
        ], unique=True, background=True)
        logger.info("✅ Index applications créés")
        
        # Index pour la collection scraping_sessions
        await db.scraping_sessions.create_index("user_id", background=True)
        await db.scraping_sessions.create_index("status", background=True)
        await db.scraping_sessions.create_index("start_time", background=True)
        logger.info("✅ Index scraping_sessions créés")
        
        # Index pour la collection recruiters
        await db.recruiters.create_index("email", sparse=True, background=True)
        await db.recruiters.create_index("linkedin_id", sparse=True, background=True)
        await db.recruiters.create_index("company", background=True)
        logger.info("✅ Index recruiters créés")
        
    except Exception as e:
        logger.error(f"❌ Erreur création index: {e}")
        raise

def init_mongodb_sync():
    """
    Version synchrone de l'initialisation pour les tests ou les scripts.
    """
    logger.info(f"🔧 Initialisation MongoDB (sync): {MONGODB_URI}")
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    
    try:
        # Test de connexion
        client.admin.command('ping')
        logger.info("✅ Connexion MongoDB établie (sync)")
        
        # Liste des collections
        collections = [
            "users", "connections", "messages", "messageTemplates", 
            "opportunities", "automations", "profileOptimizations", 
            "analytics", "campaigns", "notifications", "jobs", 
            "applications", "scraping_sessions", "recruiters"
        ]
        
        # Création des collections
        existing_collections = db.list_collection_names()
        for collection in collections:
            if collection not in existing_collections:
                logger.info(f"📁 Création collection: {collection}")
                db.create_collection(collection)
        
        # Index essentiels (version simplifiée)
        db.users.create_index("email", unique=True, background=True)
        db.jobs.create_index([("title", 1), ("company", 1), ("location", 1)], unique=True, background=True)
        db.applications.create_index([("userId", 1), ("jobId", 1)], unique=True, background=True)
        
        logger.info("🎉 Initialisation MongoDB (sync) terminée!")
        return client
        
    except Exception as e:
        logger.error(f"❌ Erreur initialisation MongoDB (sync): {e}")
        raise
    finally:
        client.close()

# Fonction utilitaire pour exécuter des coroutines
def run_async(coroutine):
    """Exécute une coroutine de manière synchrone"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coroutine)

# Script d'initialisation standalone
async def main():
    """Script principal d'initialisation"""
    try:
        client = await init_mongodb()
        logger.info("🎉 Base de données initialisée avec succès!")
    except Exception as e:
        logger.error(f"❌ Échec de l'initialisation: {e}")
        exit(1)
    finally:
        if client:
            client.close()

# Exécution si le script est lancé directement
if __name__ == "__main__":
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Exécution
    asyncio.run(main())