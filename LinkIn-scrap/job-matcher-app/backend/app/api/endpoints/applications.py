# app/api/endpoints/applications.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

from app.db.database import get_database
from app.models.application import Application, ApplicationCreate, ApplicationUpdate
from app.api.deps import get_current_active_user

router = APIRouter()

@router.post("/", response_model=Dict[str, Any])
async def create_application(
    application: ApplicationCreate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Crée une nouvelle candidature"""
    db = await get_database()
    
    # Vérification de l'existence du job
    try:
        job = await db.jobs.find_one({"_id": ObjectId(application.jobId)})
    except:
        raise HTTPException(status_code=400, detail="ID de job invalide")
    
    if not job:
        raise HTTPException(status_code=404, detail="Offre d'emploi non trouvée")
    
    # Vérification qu'une candidature n'existe pas déjà
    existing_application = await db.applications.find_one({
        "userId": ObjectId(current_user["_id"]),
        "jobId": ObjectId(application.jobId)
    })
    
    if existing_application:
        raise HTTPException(
            status_code=400,
            detail="Vous avez déjà postulé à cette offre"
        )
    
    # Création de la candidature
    new_application = Application(
        userId=ObjectId(current_user["_id"]),
        jobId=ObjectId(application.jobId),
        coverLetter=application.coverLetter,
        resumeUrl=application.resumeUrl,
        useLinkedInProfile=application.useLinkedInProfile,
        notes=application.notes,
        createdAt=datetime.utcnow(),
        updatedAt=datetime.utcnow()
    )
    
    # Insertion en base
    result = await db.applications.insert_one(new_application.dict(by_alias=True))
    
    # Récupération avec les détails du job
    created_application = await db.applications.aggregate([
        {"$match": {"_id": result.inserted_id}},
        {"$lookup": {
            "from": "jobs",
            "localField": "jobId",
            "foreignField": "_id",
            "as": "job"
        }},
        {"$unwind": "$job"}
    ]).to_list(length=1)
    
    if created_application:
        app = created_application[0]
        app["_id"] = str(app["_id"])
        app["userId"] = str(app["userId"])
        app["jobId"] = str(app["jobId"])
        app["job"]["_id"] = str(app["job"]["_id"])
        return app
    
    raise HTTPException(status_code=500, detail="Erreur lors de la création de la candidature")

@router.get("/", response_model=List[Dict[str, Any]])
async def get_user_applications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Récupère les candidatures de l'utilisateur connecté"""
    db = await get_database()
    
    # Construction du filtre
    filter_query = {"userId": ObjectId(current_user["_id"])}
    
    if status:
        filter_query["status"] = status
    
    # Récupération avec les détails des jobs
    applications = await db.applications.aggregate([
        {"$match": filter_query},
        {"$lookup": {
            "from": "jobs",
            "localField": "jobId",
            "foreignField": "_id",
            "as": "job"
        }},
        {"$unwind": "$job"},
        {"$sort": {"createdAt": -1}},
        {"$skip": skip},
        {"$limit": limit}
    ]).to_list(length=limit)
    
    # Conversion des ObjectId
    for app in applications:
        app["_id"] = str(app["_id"])
        app["userId"] = str(app["userId"])
        app["jobId"] = str(app["jobId"])
        app["job"]["_id"] = str(app["job"]["_id"])
    
    return applications

@router.get("/{application_id}", response_model=Dict[str, Any])
async def get_application(
    application_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Récupère une candidature par son ID"""
    db = await get_database()
    
    try:
        app_object_id = ObjectId(application_id)
    except:
        raise HTTPException(status_code=400, detail="ID de candidature invalide")
    
    # Récupération avec vérification des permissions
    applications = await db.applications.aggregate([
        {"$match": {
            "_id": app_object_id,
            "userId": ObjectId(current_user["_id"])
        }},
        {"$lookup": {
            "from": "jobs",
            "localField": "jobId",
            "foreignField": "_id",
            "as": "job"
        }},
        {"$unwind": "$job"}
    ]).to_list(length=1)
    
    if not applications:
        raise HTTPException(status_code=404, detail="Candidature non trouvée")
    
    app = applications[0]
    app["_id"] = str(app["_id"])
    app["userId"] = str(app["userId"])
    app["jobId"] = str(app["jobId"])
    app["job"]["_id"] = str(app["job"]["_id"])
    
    return app

@router.put("/{application_id}", response_model=Dict[str, Any])
async def update_application(
    application_id: str,
    application_update: ApplicationUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Met à jour une candidature"""
    db = await get_database()
    
    try:
        app_object_id = ObjectId(application_id)
    except:
        raise HTTPException(status_code=400, detail="ID de candidature invalide")
    
    # Vérification des permissions
    existing_application = await db.applications.find_one({
        "_id": app_object_id,
        "userId": ObjectId(current_user["_id"])
    })
    
    if not existing_application:
        raise HTTPException(status_code=404, detail="Candidature non trouvée")
    
    # Préparation des données de mise à jour
    update_data = application_update.dict(exclude_unset=True)
    update_data["updatedAt"] = datetime.utcnow()
    
    # Mise à jour
    await db.applications.update_one(
        {"_id": app_object_id},
        {"$set": update_data}
    )
    
    # Récupération des données mises à jour
    updated_applications = await db.applications.aggregate([
        {"$match": {"_id": app_object_id}},
        {"$lookup": {
            "from": "jobs",
            "localField": "jobId",
            "foreignField": "_id",
            "as": "job"
        }},
        {"$unwind": "$job"}
    ]).to_list(length=1)
    
    if updated_applications:
        app = updated_applications[0]
        app["_id"] = str(app["_id"])
        app["userId"] = str(app["userId"])
        app["jobId"] = str(app["jobId"])
        app["job"]["_id"] = str(app["job"]["_id"])
        return app
    
    raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour")

@router.delete("/{application_id}")
async def delete_application(
    application_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Supprime une candidature"""
    db = await get_database()
    
    try:
        app_object_id = ObjectId(application_id)
    except:
        raise HTTPException(status_code=400, detail="ID de candidature invalide")
    
    # Suppression avec vérification des permissions
    result = await db.applications.delete_one({
        "_id": app_object_id,
        "userId": ObjectId(current_user["_id"])
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Candidature non trouvée")
    
    return {"message": "Candidature supprimée avec succès"}

@router.get("/stats/summary")
async def get_applications_stats(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Récupère les statistiques des candidatures de l'utilisateur"""
    db = await get_database()
    
    user_id = ObjectId(current_user["_id"])
    
    # Statistiques par statut
    pipeline_status = [
        {"$match": {"userId": user_id}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    stats_by_status = await db.applications.aggregate(pipeline_status).to_list(length=100)
    
    # Total des candidatures
    total_applications = await db.applications.count_documents({"userId": user_id})
    
    # Candidatures récentes (dernière semaine)
    from datetime import timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_applications = await db.applications.count_documents({
        "userId": user_id,
        "createdAt": {"$gte": week_ago}
    })
    
    return {
        "total_applications": total_applications,
        "recent_applications": recent_applications,
        "applications_by_status": {stat["_id"]: stat["count"] for stat in stats_by_status}
    }