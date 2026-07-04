# backend/app/api/auth.py
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Provider
from app.schemas import LoginPayload

# WARNING: Manage secrets securely via AWS Secrets Manager in production!
SECRET_KEY = "SUPER_SECRET_CLINICAL_SCRIBE_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/login")
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    # Query against your auto-seeded database records
    provider = db.query(Provider).filter(Provider.email == payload.email).first()
    if not provider or provider.password_hash != payload.password:  # Replace with verification logic (e.g., bcrypt)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not provider.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")
        
    token = create_access_token(data={"sub": provider.email, "role": provider.role, "id": provider.id})
    return {"access_token": token, "token_type": "bearer", "role": provider.role}

# Dependency Injector Guard to protect individual clinical paths
def get_current_provider(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate clinical session",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    provider = db.query(Provider).filter(Provider.email == email).first()
    if provider is None:
        raise credentials_exception
    return provider
