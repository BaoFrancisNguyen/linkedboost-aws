# app/models/user.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Any
from datetime import datetime
from bson import ObjectId
from pydantic import GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> Any:
        from pydantic_core import core_schema
        return core_schema.str_schema()

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, schema: Any, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {
            "type": "string",
            "pattern": "^[a-f0-9]{24}$",
        }

class NotificationSettings(BaseModel):
    email: bool = True
    app: bool = True
    connectionRequests: bool = True
    messages: bool = True
    opportunities: bool = True
    automationAlerts: bool = True
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }

class PrivacySettings(BaseModel):
    shareData: bool = True
    allowAnalytics: bool = True
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }

class UserSettings(BaseModel):
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    privacy: PrivacySettings = Field(default_factory=PrivacySettings)
    theme: str = "light"
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }

class UserBase(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }

class UserCreate(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    password: str
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class UserUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[EmailStr] = None
    profilePicture: Optional[str] = None
    headline: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    location: Optional[str] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class User(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    firstName: str
    lastName: str
    email: EmailStr
    password: str
    profilePicture: Optional[str] = None
    headline: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    location: Optional[str] = None
    linkedInId: Optional[str] = None
    linkedInAccessToken: Optional[str] = None
    linkedInRefreshToken: Optional[str] = None
    linkedInTokenExpiry: Optional[datetime] = None
    profileScore: Optional[float] = 0
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
    lastLogin: Optional[datetime] = None
    isActive: bool = True
    role: str = "user"
    settings: UserSettings = Field(default_factory=UserSettings)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }