# app/models/job.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from app.models.user import PyObjectId

class JobCreate(BaseModel):
    title: str
    company: str
    companyLogo: Optional[str] = None
    companyWebsite: Optional[str] = None
    companyDescription: Optional[str] = None
    location: str
    type: Optional[str] = None
    salary: Optional[str] = None
    description: str
    responsibilities: List[str] = []
    requirements: List[str] = []
    niceToHave: List[str] = []
    benefits: List[str] = []
    experienceLevel: Optional[str] = None
    education: Optional[str] = None
    languages: List[str] = []
    remote: bool = False
    urgent: bool = False
    startDate: Optional[str] = None
    applicationDeadline: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    companyLogo: Optional[str] = None
    companyWebsite: Optional[str] = None
    companyDescription: Optional[str] = None
    location: Optional[str] = None
    type: Optional[str] = None
    salary: Optional[str] = None
    description: Optional[str] = None
    responsibilities: Optional[List[str]] = None
    requirements: Optional[List[str]] = None
    niceToHave: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    experienceLevel: Optional[str] = None
    education: Optional[str] = None
    languages: Optional[List[str]] = None
    remote: Optional[bool] = None
    urgent: Optional[bool] = None
    startDate: Optional[str] = None
    applicationDeadline: Optional[datetime] = None
    status: Optional[str] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class Job(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    title: str
    company: str
    companyLogo: Optional[str] = None
    companyWebsite: Optional[str] = None
    companyDescription: Optional[str] = None
    location: str
    type: Optional[str] = None
    salary: Optional[str] = None
    description: str
    responsibilities: List[str] = []
    requirements: List[str] = []
    niceToHave: List[str] = []
    benefits: List[str] = []
    experienceLevel: Optional[str] = None
    education: Optional[str] = None
    languages: List[str] = []
    remote: bool = False
    urgent: bool = False
    postedAt: datetime = Field(default_factory=datetime.utcnow)
    startDate: Optional[str] = None
    applicationDeadline: Optional[datetime] = None
    views: int = 0
    applications: int = 0
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
    status: str = "active"
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }