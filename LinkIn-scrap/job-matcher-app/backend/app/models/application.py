# app/models/application.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId
from app.models.user import PyObjectId

class ApplicationCreate(BaseModel):
    jobId: str
    coverLetter: Optional[str] = None
    resumeUrl: Optional[str] = None
    useLinkedInProfile: bool = False
    notes: Optional[str] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class ApplicationUpdate(BaseModel):
    coverLetter: Optional[str] = None
    resumeUrl: Optional[str] = None
    useLinkedInProfile: Optional[bool] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class Application(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    userId: PyObjectId
    jobId: PyObjectId
    coverLetter: Optional[str] = None
    resumeUrl: Optional[str] = None
    useLinkedInProfile: bool = False
    status: str = "pending"
    notes: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
    lastStatusChange: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }