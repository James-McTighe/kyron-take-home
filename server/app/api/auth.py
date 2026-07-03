import os
import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Provider
from ..schemas import LoginRequest, TokenResponse, TokenData

# Production architectures must load these from AWS Secrets Manager [cite: 178]
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super_secret_clinical_scribe_key_9912")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8-hour provider shifts

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (expires_delta or datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    # Query database for matching seeded record [cite: 118]
    user = db.query(Provider).filter(Provider.email == payload.email).first()
    
    # Simple plain-text demonstration validation matching our startup seeds [cite: 12, 118]
    if not user or user.password_hash != payload.password or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email, password, or deactivated account status."
        )
    
    # Embed critical multi-role identity assertions into the token payload [cite: 117, 120]
    token_data = {"sub": user.email, "role": user.role, "user_id": user.id}
    access_token = create_access_token(data=token_data)
    return {"access_token": access_token, "token_type": "bearer"}

# --- Dependency Injections / Route Guards ---

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate active credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        user_id: int = payload.get("user_id")
        if email is None or role is None or user_id is None:
            raise credentials_exception
        return TokenData(email=email, role=role, user_id=user_id)
    except JWTError:
        raise credentials_exception

def get_current_provider(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Blocks requests if the authenticated user doesn't possess operational clinical clearance."""
    if current_user.role not in ["Provider", "Admin"]:
        raise HTTPException(status_code=403, detail="Access denied. Provider role clearance required.")
    return current_user

def get_current_admin(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Blocks standard providers from accessing administrative layout routes[cite: 120]."""
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Access denied. Administrative role clearance required.")
    return current_user
