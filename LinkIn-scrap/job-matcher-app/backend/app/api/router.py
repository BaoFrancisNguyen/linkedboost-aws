# Mise à jour du router principal (app/api/router.py)
from fastapi import APIRouter
from app.api.endpoints import users, scraping, jobs, applications

api_router = APIRouter()

# Endpoints existants
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])

# Nouveau endpoint pour le scraping amélioré
api_router.include_router(scraping.router, prefix="/scraping", tags=["scraping"])

# Mise à jour du modèle Job (app/models/job.py) pour supporter les nouvelles données
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.models.user import PyObjectId

class JobCompanyInfo(BaseModel):
    """Informations sur l'entreprise"""
    name: str
    size: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    description: Optional[str] = None

class JobLocation(BaseModel):
    """Informations de localisation"""
    city: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    postal_code: Optional[str] = None
    full_address: Optional[str] = None
    remote: bool = False

class JobScrapingInfo(BaseModel):
    """Informations de scraping"""
    source: str = "linkedin"
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    linkedin_job_id: Optional[str] = None
    linkedin_url: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class JobEnhanced(BaseModel):
    """Modèle de job amélioré avec données de scraping"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    # Informations de base
    title: str
    company: JobCompanyInfo
    location: JobLocation
    
    # Détails du poste
    description: str = ""
    responsibilities: List[str] = []
    requirements: List[str] = []
    nice_to_have: List[str] = []
    benefits: List[str] = []
    
    # Conditions
    salary: Optional[str] = None
    experience_level: Optional[str] = None
    job_type: Optional[str] = None  # full_time, part_time, contract, etc.
    contract_duration: Optional[str] = None
    
    # Statut et dates
    status: str = "active"  # active, closed, draft, expired
    posted_at: Optional[datetime] = None
    application_deadline: Optional[datetime] = None
    start_date: Optional[datetime] = None
    
    # Métriques
    views: int = 0
    applications: int = 0
    
    # Flags
    remote: bool = False
    urgent: bool = False
    featured: bool = False
    
    # Métadonnées
    scraping_info: Optional[JobScrapingInfo] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Configuration
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }

# Modèle de session de scraping amélioré (app/models/scraping.py)
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from bson import ObjectId
from app.models.user import PyObjectId

class ScrapingFilters(BaseModel):
    """Filtres de scraping"""
    experience_level: Optional[str] = None  # entry, mid_senior, director, etc.
    job_type: Optional[str] = None         # full_time, part_time, contract, etc.
    date_posted: Optional[str] = None      # past_24h, past_week, past_month
    salary_range: Optional[str] = None     # Plage salariale
    company_size: Optional[str] = None     # startup, small, medium, large
    remote_only: bool = False
    urgent_only: bool = False

class ScrapingStats(BaseModel):
    """Statistiques de scraping"""
    total_pages_scraped: int = 0
    total_jobs_found: int = 0
    total_jobs_saved: int = 0
    duplicates_found: int = 0
    errors_count: int = 0
    average_time_per_page: float = 0.0

class ScrapingError(BaseModel):
    """Erreur de scraping"""
    timestamp: datetime
    error_type: str
    error_message: str
    page_number: Optional[int] = None

class ScrapingSessionEnhanced(BaseModel):
    """Session de scraping améliorée"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    
    # Paramètres de recherche
    keywords: Optional[str] = None
    location: Optional[str] = None
    max_pages: int = 3
    filters: ScrapingFilters = Field(default_factory=ScrapingFilters)
    
    # Statut et timing
    status: str = "pending"  # pending, running, completed, failed, cancelled
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    estimated_duration: Optional[int] = None  # en secondes
    
    # Résultats
    stats: ScrapingStats = Field(default_factory=ScrapingStats)
    errors: List[ScrapingError] = []
    
    # Métadonnées
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }