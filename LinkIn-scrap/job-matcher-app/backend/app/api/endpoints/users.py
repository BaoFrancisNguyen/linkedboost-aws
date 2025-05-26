# app/api/endpoints/users.py
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.database import get_database
from app.models.user import User, UserCreate, UserLogin, UserUpdate
from app.api.deps import get_current_user, get_current_active_user

router = APIRouter()

@router.post("/register", response_model=Dict[str, str])
async def create_user(user: UserCreate):
    """Inscription d'un nouvel utilisateur"""
    db = await get_database()
    
    # Vérifier si l'utilisateur existe déjà
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un utilisateur avec cet email existe déjà"
        )
    
    # Hachage du mot de passe
    hashed_password = get_password_hash(user.password)
    
    # Création de l'utilisateur
    new_user = User(
        email=user.email,
        firstName=user.firstName,
        lastName=user.lastName,
        password=hashed_password,
        createdAt=datetime.utcnow(),
        updatedAt=datetime.utcnow()
    )
    
    # Insertion en base
    result = await db.users.insert_one(new_user.dict(by_alias=True))
    
    # Création du token d'accès
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "message": "Utilisateur créé avec succès"
    }

@router.post("/login", response_model=Dict[str, str])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Connexion d'un utilisateur"""
    db = await get_database()
    
    # Recherche de l'utilisateur
    user = await db.users.find_one({"email": form_data.username})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Vérification du mot de passe
    if not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Mise à jour de la dernière connexion
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"lastLogin": datetime.utcnow()}}
    )
    
    # Création du token d'accès
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Récupère les informations de l'utilisateur connecté"""
    # Nettoyage des données sensibles
    user_info = current_user.copy()
    user_info.pop("password", None)
    user_info["_id"] = str(user_info["_id"])
    
    return user_info

@router.put("/me", response_model=Dict[str, Any])
async def update_user_info(
    user_update: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Met à jour les informations de l'utilisateur connecté"""
    db = await get_database()
    
    # Préparation des données à mettre à jour
    update_data = {}
    
    if user_update.firstName is not None:
        update_data["firstName"] = user_update.firstName
    
    if user_update.lastName is not None:
        update_data["lastName"] = user_update.lastName
    
    if user_update.email is not None:
        # Vérifier si l'email n'est pas déjà utilisé
        if user_update.email != current_user["email"]:
            existing_user = await db.users.find_one({"email": user_update.email})
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cet email est déjà utilisé"
                )
        update_data["email"] = user_update.email
    
    if user_update.profilePicture is not None:
        update_data["profilePicture"] = user_update.profilePicture
    
    if user_update.headline is not None:
        update_data["headline"] = user_update.headline
    
    if user_update.company is not None:
        update_data["company"] = user_update.company
    
    if user_update.position is not None:
        update_data["position"] = user_update.position
    
    if user_update.location is not None:
        update_data["location"] = user_update.location
    
    update_data["updatedAt"] = datetime.utcnow()
    
    # Mise à jour en base
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": update_data}
    )
    
    # Récupération des données mises à jour
    updated_user = await db.users.find_one({"_id": current_user["_id"]})
    updated_user.pop("password", None)
    updated_user["_id"] = str(updated_user["_id"])
    
    return updated_user

@router.get("/", response_model=List[Dict[str, Any]])
async def get_users(
    skip: int = 0,
    limit: int = 10,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Récupère la liste des utilisateurs (avec pagination)"""
    db = await get_database()
    
    # Seuls les admins peuvent voir tous les utilisateurs
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    users = await db.users.find({}, {"password": 0}).skip(skip).limit(limit).to_list(length=limit)
    
    # Conversion des ObjectId en string
    for user in users:
        user["_id"] = str(user["_id"])
    
    return users

# app/api/endpoints/jobs.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

from app.db.database import get_database
from app.models.job import Job, JobCreate, JobUpdate
from app.api.deps import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
async def get_jobs(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(20, ge=1, le=100, description="Nombre d'éléments à retourner"),
    title: Optional[str] = Query(None, description="Filtrer par titre"),
    company: Optional[str] = Query(None, description="Filtrer par entreprise"),
    location: Optional[str] = Query(None, description="Filtrer par localisation"),
    remote: Optional[bool] = Query(None, description="Filtrer par télétravail"),
    job_type: Optional[str] = Query(None, description="Filtrer par type de contrat"),
    experience_level: Optional[str] = Query(None, description="Filtrer par niveau d'expérience")
):
    """Récupère la liste des offres d'emploi avec filtrage"""
    db = await get_database()
    
    # Construction du filtre
    filter_query = {"status": "active"}
    
    if title:
        filter_query["title"] = {"$regex": title, "$options": "i"}
    
    if company:
        filter_query["company"] = {"$regex": company, "$options": "i"}
    
    if location:
        filter_query["location"] = {"$regex": location, "$options": "i"}
    
    if remote is not None:
        filter_query["remote"] = remote
    
    if job_type:
        filter_query["type"] = job_type
    
    if experience_level:
        filter_query["experienceLevel"] = experience_level
    
    # Récupération des jobs
    jobs = await db.jobs.find(filter_query).sort("createdAt", -1).skip(skip).limit(limit).to_list(length=limit)
    
    # Conversion des ObjectId
    for job in jobs:
        job["_id"] = str(job["_id"])
    
    return jobs

@router.get("/{job_id}", response_model=Dict[str, Any])
async def get_job(job_id: str):
    """Récupère une offre d'emploi par son ID"""
    db = await get_database()
    
    try:
        job = await db.jobs.find_one({"_id": ObjectId(job_id)})
    except:
        raise HTTPException(status_code=400, detail="ID de job invalide")
    
    if not job:
        raise HTTPException(status_code=404, detail="Offre d'emploi non trouvée")
    
    job["_id"] = str(job["_id"])
    return job

@router.post("/", response_model=Dict[str, Any])
async def create_job(
    job: JobCreate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Crée une nouvelle offre d'emploi"""
    db = await get_database()
    
    # Création du job
    new_job = Job(
        **job.dict(),
        createdAt=datetime.utcnow(),
        updatedAt=datetime.utcnow()
    )
    
    # Insertion en base
    result = await db.jobs.insert_one(new_job.dict(by_alias=True))
    
    # Récupération du job créé
    created_job = await db.jobs.find_one({"_id": result.inserted_id})
    created_job["_id"] = str(created_job["_id"])
    
    return created_job

@router.put("/{job_id}", response_model=Dict[str, Any])
async def update_job(
    job_id: str,
    job_update: JobUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Met à jour une offre d'emploi"""
    db = await get_database()
    
    try:
        job_object_id = ObjectId(job_id)
    except:
        raise HTTPException(status_code=400, detail="ID de job invalide")
    
    # Vérification de l'existence
    existing_job = await db.jobs.find_one({"_id": job_object_id})
    if not existing_job:
        raise HTTPException(status_code=404, detail="Offre d'emploi non trouvée")
    
    # Préparation des données de mise à jour
    update_data = job_update.dict(exclude_unset=True)
    update_data["updatedAt"] = datetime.utcnow()
    
    # Mise à jour
    await db.jobs.update_one(
        {"_id": job_object_id},
        {"$set": update_data}
    )
    
    # Récupération des données mises à jour
    updated_job = await db.jobs.find_one({"_id": job_object_id})
    updated_job["_id"] = str(updated_job["_id"])
    
    return updated_job

@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Supprime une offre d'emploi"""
    db = await get_database()
    
    try:
        job_object_id = ObjectId(job_id)
    except:
        raise HTTPException(status_code=400, detail="ID de job invalide")
    
    # Suppression (soft delete en changeant le statut)
    result = await db.jobs.update_one(
        {"_id": job_object_id},
        {"$set": {"status": "deleted", "updatedAt": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Offre d'emploi non trouvée")
    
    return {"message": "Offre d'emploi supprimée avec succès"}

@router.get("/stats/summary")
async def get_jobs_stats():
    """Récupère les statistiques des offres d'emploi"""
    db = await get_database()
    
    # Statistiques générales
    total_jobs = await db.jobs.count_documents({"status": "active"})
    remote_jobs = await db.jobs.count_documents({"status": "active", "remote": True})
    
    # Jobs par type
    pipeline_type = [
        {"$match": {"status": "active"}},
        {"$group": {"_id": "$type", "count": {"$sum": 1}}}
    ]
    jobs_by_type = await db.jobs.aggregate(pipeline_type).to_list(length=100)
    
    # Jobs par niveau d'expérience
    pipeline_exp = [
        {"$match": {"status": "active"}},
        {"$group": {"_id": "$experienceLevel", "count": {"$sum": 1}}}
    ]
    jobs_by_experience = await db.jobs.aggregate(pipeline_exp).to_list(length=100)
    
    return {
        "total_jobs": total_jobs,
        "remote_jobs": remote_jobs,
        "remote_percentage": (remote_jobs / total_jobs * 100) if total_jobs > 0 else 0,
        "jobs_by_type": {stat["_id"]: stat["count"] for stat in jobs_by_type if stat["_id"]},
        "jobs_by_experience": {stat["_id"]: stat["count"] for stat in jobs_by_experience if stat["_id"]}
    }