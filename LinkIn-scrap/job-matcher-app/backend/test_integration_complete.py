# Script de test complet (test_integration_complete.py)
import asyncio
import pytest
from datetime import datetime
import json

async def test_complete_integration():
    """Test complet de l'intégration du scraper"""
    
    print("🧪 Test d'intégration complète du scraper LinkedIn")
    
    try:
        # Test 1: Import des modules
        print("📦 Test import des modules...")
        from linkedin_scraper_enhanced import LinkedInJobScraper, scrape_linkedin_jobs
        from app.services.scraping_service_enhanced import EnhancedScrapingService
        print("✅ Modules importés avec succès")
        
        # Test 2: Initialisation du scraper
        print("🔧 Test initialisation du scraper...")
        scraper = LinkedInJobScraper()
        print("✅ Scraper initialisé")
        
        # Test 3: Construction d'URL
        print("🔗 Test construction d'URL...")
        url = scraper.build_search_url(
            keywords=['python', 'développeur'],
            location='Paris, France',
            experience_level='mid_senior'
        )
        assert 'keywords=python' in url
        assert 'location=Paris' in url
        print("✅ URL construite correctement")
        
        # Test 4: Service de scraping
        print("⚙️ Test service de scraping...")
        service = EnhancedScrapingService()
        print("✅ Service initialisé")
        
        # Test 5: Scraping simple (avec données limitées)
        print("🚀 Test scraping simple...")
        jobs = await scrape_linkedin_jobs(
            keywords=['python'],
            location='France',
            max_pages=1  # Limité pour le test
        )
        print(f"✅ Scraping terminé: {len(jobs)} jobs collectés")
        
        # Test 6: Validation des données
        if jobs:
            print("📊 Validation des données...")
            first_job = jobs[0]
            required_fields = ['title', 'company', 'location', 'scraped_at']
            
            for field in required_fields:
                assert field in first_job, f"Champ manquant: {field}"
            
            print("✅ Structure des données validée")
            
            # Affichage d'un échantillon
            print("\n📋 Échantillon de données:")
            print(f"Titre: {first_job.get('title')}")
            print(f"Entreprise: {first_job.get('company')}")
            print(f"Lieu: {first_job.get('location')}")
            print(f"Remote: {first_job.get('remote', False)}")
        
        await scraper.close()
        
        print("\n🎉 Tous les tests sont passés avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Test échoué: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_endpoints():
    """Test des endpoints API"""
    
    print("🌐 Test des endpoints API...")
    
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # Test health check
        response = client.get("/api/v1/scraping/v2/health")
        assert response.status_code == 200
        print("✅ Health check OK")
        
        # Test stats endpoint
        response = client.get("/api/v1/scraping/v2/stats")
        print(f"Stats endpoint: {response.status_code}")
        
        print("✅ Endpoints API testés")
        return True
        
    except Exception as e:
        print(f"❌ Test API échoué: {e}")
        return False

# Configuration pour tests automatisés
if __name__ == "__main__":
    async def run_all_tests():
        print("🚀 Démarrage des tests d'intégration\n")
        
        # Test d'intégration complète
        success1 = await test_complete_integration()
        
        # Test des endpoints API
        success2 = await test_api_endpoints()
        
        if success1 and success2:
            print("\n🎉 Tous les tests d'intégration sont passés!")
        else:
            print("\n❌ Certains tests ont échoué")
        
        return success1 and success2
    
    # Exécution
    result = asyncio.run(run_all_tests())
    exit(0 if result else 1)