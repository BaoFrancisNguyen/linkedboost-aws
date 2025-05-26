# Script de démarrage rapide
# start_app.py
#!/usr/bin/env python3
"""
Script de démarrage rapide pour l'application LinkedIn Job Matcher
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

def check_python_version():
    """Vérifie la version de Python"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ requis")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} OK")

def check_mongodb():
    """Vérifie si MongoDB est accessible"""
    try:
        import pymongo
        client = pymongo.MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        client.close()
        print("✅ MongoDB accessible")
        return True
    except Exception as e:
        print(f"⚠️ MongoDB non accessible: {e}")
        print("💡 Démarrez MongoDB avec: mongod --dbpath /path/to/db")
        return False

def install_dependencies():
    """Installe les dépendances"""
    print("📦 Installation des dépendances...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dépendances installées")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur installation: {e}")
        return False

def create_env_file():
    """Crée le fichier .env s'il n'existe pas"""
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ Fichier .env trouvé")
        return True
    
    print("📝 Création du fichier .env...")
    
    env_content = """# Database Configuration
MONGODB_URI=mongodb://localhost:27017
DB_NAME=linkedin_scraper

# JWT Configuration
SECRET_KEY=your_super_secret_key_change_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=True
LOG_LEVEL=INFO

# CORS Configuration
BACKEND_CORS_ORIGINS=["*"]

# Scraping Configuration
MAX_SCRAPING_PAGES=10
SELENIUM_TIMEOUT=15
"""
    
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print("✅ Fichier .env créé")
    return True

async def initialize_database():
    """Initialise la base de données"""
    print("🔧 Initialisation de la base de données...")
    
    try:
        from app.db.init_db import init_mongodb
        await init_mongodb()
        print("✅ Base de données initialisée")
        return True
    except Exception as e:
        print(f"❌ Erreur initialisation DB: {e}")
        return False

def start_application():
    """Démarre l'application"""
    print("🚀 Démarrage de l'application...")
    
    try:
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🔄 Application arrêtée par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur démarrage: {e}")

async def main():
    """Fonction principale"""
    print("🎯 DÉMARRAGE RAPIDE - LinkedIn Job Matcher API")
    print("=" * 50)
    
    # Vérifications
    check_python_version()
    
    mongodb_ok = check_mongodb()
    if not mongodb_ok:
        print("\n⚠️ MongoDB non accessible. Continuez-vous quand même? (y/N)")
        if input().lower() != 'y':
            print("Démarrez MongoDB et relancez le script.")
            return
    
    # Configuration
    create_env_file()
    
    if not install_dependencies():
        print("❌ Impossible d'installer les dépendances")
        return
    
    # Initialisation DB (si MongoDB OK)
    if mongodb_ok:
        db_ok = await initialize_database()
        if not db_ok:
            print("⚠️ Erreur initialisation DB, mais continuons...")
    
    print("\n🎉 Configuration terminée!")
    print("📱 L'application sera disponible sur: http://localhost:8000")
    print("📚 Documentation API: http://localhost:8000/docs")
    print("\nAppuyez sur Ctrl+C pour arrêter l'application")
    
    # Démarrage
    start_application()

if __name__ == "__main__":
    asyncio.run(main())