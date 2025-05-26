# Endpoints FastAPI améliorés (app/api/endpoints/scraping_enhanced.py)
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from app.services.scraping_service_enhanced import enhanced_scraping_service
from app.api.deps import get_current_user

router = APIRouter()

class ScrapingRequestV2(BaseModel):
    """Requête de scraping version 2"""
    keywords: Optional[str] = Field(None, description="Mots-clés séparés par des virgules")
    location: Optional[str] = Field(None, description="Localisation (ex: Paris, France)")
    max_pages: int = Field(3, ge=1, le=10, description="Nombre de pages (1-10)")
    
    # Filtres avancés
    experience_level: Optional[str] = Field(None, description="entry, associate, mid_senior, director, executive")
    job_type: Optional[str] = Field(None, description="full_time, part_time, contract, temporary, internship")
    date_posted: Optional[str] = Field(None, description="past_24h, past_week, past_month")
    salary_range: Optional[str] = Field(None, description="Plage salariale")
    company_size: Optional[str] = Field(None, description="startup, small, medium, large")
    remote_only: bool = Field(False, description="Uniquement les postes en télétravail")
    urgent_only: bool = Field(False, description="Uniquement les postes urgents")

class ScrapingResponseV2(BaseModel):
    """Réponse de scraping version 2"""
    session_id: str
    status: str
    message: str
    estimated_duration: int  # en secondes
    created_at: datetime

@router.post("/v2/start", response_model=ScrapingResponseV2)
async def start_enhanced_scraping(
    request: ScrapingRequestV2,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Démarre une session de scraping LinkedIn améliorée
    
    Cette version offre:
    - Filtres avancés
    - Suivi détaillé des statistiques
    - Gestion d'erreurs améliorée
    - Conversion automatique vers le modèle de données enrichi
    """
    try:
        user_id = str(current_user["_id"])
        
        # Conversion des filtres
        filters = {
            "experience_level": request.experience_level,
            "job_type": request.job_type,
            "date_posted": request.date_posted,
            "salary_range": request.salary_range,
            "company_size": request.company_size,
            "remote_only": request.remote_only,
            "urgent_only": request.urgent_only
        }
        
        # Démarrage de la session
        session_id = await enhanced_scraping_service.create_scraping_session(
            user_id=user_id,
            keywords=request.keywords,
            location=request.location,
            max_pages=request.max_pages,
            filters=filters
        )
        
        return ScrapingResponseV2(
            session_id=session_id,
            status="started",
            message="Session de scraping démarrée avec succès",
            estimated_duration=request.max_pages * 60,
            created_at=datetime.utcnow()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur démarrage scraping: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@router.get("/v2/sessions/{session_id}")
async def get_enhanced_session_details(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Récupère les détails complets d'une session de scraping"""
    try:
        session = await enhanced_scraping_service.get_session_details(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        
        # Vérification des permissions
        if session["user_id"] != str(current_user["_id"]):
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération session: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@router.get("/v2/sessions")
async def get_user_scraping_sessions(
    limit: int = Query(20, ge=1, le=100, description="Nombre de sessions à retourner"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Récupère les sessions de scraping de l'utilisateur connecté"""
    try:
        user_id = str(current_user["_id"])
        sessions = await enhanced_scraping_service.get_user_sessions(user_id, limit)
        
        return {
            "sessions": sessions,
            "total": len(sessions),
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"Erreur récupération sessions: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@router.delete("/v2/sessions/{session_id}")
async def cancel_scraping_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Annule une session de scraping en cours"""
    try:
        # Vérification des permissions
        session = await enhanced_scraping_service.get_session_details(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        
        if session["user_id"] != str(current_user["_id"]):
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        # Annulation
        success = await enhanced_scraping_service.cancel_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Impossible d'annuler la session (déjà terminée ou inexistante)"
            )
        
        return {"message": "Session annulée avec succès", "session_id": session_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur annulation session: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@router.get("/v2/jobs/enhanced")
async def get_enhanced_jobs(
    limit: int = Query(50, ge=1, le=200, description="Nombre de jobs"),
    keywords: Optional[str] = Query(None, description="Filtrer par mots-clés"),
    location: Optional[str] = Query(None, description="Filtrer par localisation"),
    remote_only: bool = Query(False, description="Uniquement télétravail"),
    experience_level: Optional[str] = Query(None, description="Niveau d'expérience"),
    job_type: Optional[str] = Query(None, description="Type de contrat"),
    sort_by: str = Query("created_at", description="Tri par: created_at, posted_at, title")
):
    """Récupère les jobs avec le modèle de données enrichi"""
    try:
        from app.db.database import get_database
        db = await get_database()
        
        # Construction du filtre
        filter_query = {}
        
        if keywords:
            keyword_list = [kw.strip() for kw in keywords.split(',')]
            filter_query["$or"] = [
                {"title": {"$regex": kw, "$options": "i"}} for kw in keyword_list
            ]
        
        if location:
            filter_query["$or"] = [
                {"location.city": {"$regex": location, "$options": "i"}},
                {"location.country": {"$regex": location, "$options": "i"}},
                {"location.full_address": {"$regex": location, "$options": "i"}}
            ]
        
        if remote_only:
            filter_query["remote"] = True
        
        if experience_level:
            filter_query["experience_level"] = experience_level
        
        if job_type:
            filter_query["job_type"] = job_type
        
        # Tri
        sort_field = sort_by if sort_by in ["created_at", "posted_at", "title"] else "created_at"
        
        # Récupération des jobs
        jobs = await db.jobs.find(filter_query).sort(sort_field, -1).limit(limit).to_list(length=limit)
        
        # Conversion des ObjectId
        for job in jobs:
            job["_id"] = str(job["_id"])
        
        return {
            "jobs": jobs,
            "total": len(jobs),
            "filters_applied": {
                "keywords": keywords,
                "location": location,
                "remote_only": remote_only,
                "experience_level": experience_level,
                "job_type": job_type
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur récupération jobs: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@router.get("/v2/stats")
async def get_enhanced_scraping_stats():
    """Récupère les statistiques complètes de scraping"""
    try:
        stats = await enhanced_scraping_service.get_scraping_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"Erreur récupération statistiques: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@router.get("/v2/health")
async def scraping_health_check():
    """Vérifie l'état du service de scraping"""
    try:
        from app.db.database import get_database
        
        # Test connexion DB
        db = await get_database()
        await db.admin.command('ping')
        
        # Test import du scraper
        try:
            from linkedin_scraper_enhanced import LinkedInJobScraper
            scraper_available = True
        except ImportError:
            scraper_available = False
        
        return {
            "status": "healthy",
            "database": "connected",
            "scraper": "available" if scraper_available else "unavailable",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }