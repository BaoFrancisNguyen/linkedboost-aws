# scraper_service.py - Service intégré pour le scraping
from typing import List, Dict, Optional, Any
from datetime import datetime
from app.services.linkedin_scraper import LinkedInScraper
from app.db.database import get_database
from app.models.job import Job
from app.models.scraping import ScrapingSession
from bson import ObjectId
import asyncio
import logging

logger = logging.getLogger(__name__)

class ScrapingService:
    """Service de scraping intégré à l'architecture FastAPI existante"""
    
    def __init__(self):
        self.scraper = None
    
    async def start_scraping_session(self, 
                                   user_id: str,
                                   search_params: Dict[str, Any]) -> str:
        """
        Démarre une nouvelle session de scraping
        
        Args:
            user_id: ID de l'utilisateur
            search_params: Paramètres de recherche (keywords, location, etc.)
        
        Returns:
            ID de la session créée
        """
        db = await get_database()
        
        # Création de la session
        session = ScrapingSession(
            user_id=user_id,
            search_query=search_params.get('keywords', ''),
            location=search_params.get('location'),
            filters=search_params,
            status="pending"
        )
        
        result = await db.scraping_sessions.insert_one(session.dict(by_alias=True))
        session_id = str(result.inserted_id)
        
        # Démarrage du scraping en arrière-plan
        asyncio.create_task(self._run_scraping_task(session_id, search_params))
        
        return session_id
    
    async def _run_scraping_task(self, session_id: str, search_params: Dict[str, Any]):
        """Exécute la tâche de scraping en arrière-plan"""
        db = await get_database()
        
        try:
            # Mise à jour du statut
            await db.scraping_sessions.update_one(
                {"_id": ObjectId(session_id)},
                {"$set": {"status": "running", "start_time": datetime.utcnow()}}
            )
            
            # Initialisation du scraper
            from linkedin_scraper_enhanced import LinkedInJobScraper
            scraper = LinkedInJobScraper()
            
            # Configuration des paramètres
            scraping_config = {
                'keywords': search_params.get('keywords', '').split(',') if search_params.get('keywords') else None,
                'location': search_params.get('location'),
                'max_pages': search_params.get('max_pages', 3),
                'experience_level': search_params.get('experience_level'),
                'job_type': search_params.get('job_type'),
                'date_posted': search_params.get('date_posted')
            }
            
            # Filtrage des paramètres None
            scraping_config = {k: v for k, v in scraping_config.items() if v is not None}
            
            # Exécution du scraping
            logger.info(f"🚀 Début scraping session {session_id}")
            jobs_data = await scraper.scrape_jobs(**scraping_config)
            
            # Conversion et sauvegarde des jobs
            jobs_saved = 0
            for job_data in jobs_data:
                try:
                    # Conversion vers le modèle Job
                    job = Job(
                        title=job_data.get('title', ''),
                        company=job_data.get('company', ''),
                        location=job_data.get('location', ''),
                        description=job_data.get('description', ''),
                        remote=job_data.get('remote', False),
                        urgent=job_data.get('urgent', False),
                        postedAt=job_data.get('posted_at', datetime.utcnow()),
                        requirements=job_data.get('requirements', []),
                        benefits=job_data.get('benefits', []),
                        salary=job_data.get('salary'),
                        type=job_data.get('job_type'),
                        experienceLevel=job_data.get('experience_level'),
                        views=job_data.get('views', 0),
                        applications=job_data.get('applications', 0)
                    )
                    
                    # Sauvegarde avec gestion des doublons
                    existing_job = await db.jobs.find_one({
                        "title": job.title,
                        "company": job.company,
                        "location": job.location
                    })
                    
                    if not existing_job:
                        result = await db.jobs.insert_one(job.dict(by_alias=True))
                        jobs_saved += 1
                        logger.info(f"✅ Job sauvegardé: {job.title} chez {job.company}")
                    else:
                        # Mise à jour si nécessaire
                        await db.jobs.update_one(
                            {"_id": existing_job["_id"]},
                            {"$set": {"updatedAt": datetime.utcnow()}}
                        )
                
                except Exception as e:
                    logger.error(f"❌ Erreur sauvegarde job: {e}")
                    continue
            
            # Mise à jour finale de la session
            await db.scraping_sessions.update_one(
                {"_id": ObjectId(session_id)},
                {
                    "$set": {
                        "status": "completed",
                        "end_time": datetime.utcnow(),
                        "jobs_found": len(jobs_data),
                        "jobs_added": jobs_saved
                    }
                }
            )
            
            logger.info(f"✅ Scraping terminé: {jobs_saved}/{len(jobs_data)} jobs sauvegardés")
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping session {session_id}: {e}")
            
            # Mise à jour du statut d'erreur
            await db.scraping_sessions.update_one(
                {"_id": ObjectId(session_id)},
                {
                    "$set": {
                        "status": "failed",
                        "end_time": datetime.utcnow(),
                        "error": str(e)
                    }
                }
            )
        
        finally:
            if scraper:
                await scraper.close()
    
    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Récupère le statut d'une session de scraping"""
        db = await get_database()
        
        try:
            session = await db.scraping_sessions.find_one({"_id": ObjectId(session_id)})
            if session:
                session["_id"] = str(session["_id"])
                return session
            return None
        except Exception as e:
            logger.error(f"❌ Erreur récupération session: {e}")
            return None
    
    async def get_user_sessions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Récupère les sessions de scraping d'un utilisateur"""
        db = await get_database()
        
        try:
            sessions = await db.scraping_sessions.find(
                {"user_id": user_id}
            ).sort("start_time", -1).limit(limit).to_list(length=limit)
            
            for session in sessions:
                session["_id"] = str(session["_id"])
            
            return sessions
        except Exception as e:
            logger.error(f"❌ Erreur récupération sessions utilisateur: {e}")
            return []
    
    async def cancel_session(self, session_id: str) -> bool:
        """Annule une session de scraping en cours"""
        db = await get_database()
        
        try:
            result = await db.scraping_sessions.update_one(
                {"_id": ObjectId(session_id), "status": {"$in": ["pending", "running"]}},
                {
                    "$set": {
                        "status": "cancelled",
                        "end_time": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"❌ Erreur annulation session: {e}")
            return False

# Configuration pour les endpoints FastAPI
scraping_service = ScrapingService()