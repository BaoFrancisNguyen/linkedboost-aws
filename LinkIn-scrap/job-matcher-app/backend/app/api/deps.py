# app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime
from typing import Dict, Any

from app.core.config import settings
from app.db.database import get_database

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/users/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Récupère l'utilisateur actuel à partir du token JWT.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Décodage du token
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Récupération de l'utilisateur
    db = await get_database()
    user = await db.users.find_one({"email": email})
    
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Récupère l'utilisateur actuel et vérifie qu'il est actif.
    """
    if not current_user.get("isActive", True):
        raise HTTPException(status_code=400, detail="Utilisateur inactif")
    return current_user

async def get_current_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Récupère l'utilisateur actuel et vérifie qu'il est admin.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissions insuffisantes"
        )
    return current_user