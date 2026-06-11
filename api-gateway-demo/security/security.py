from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
import hashlib
import secrets

app = FastAPI()
security = HTTPBearer()

SECRET_KEY = "secret-key-123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Простое хэширование через SHA256
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed

# Хранилище пользователей
users_db: Dict[str, dict] = {}

class UserCreate(BaseModel):
    login: str
    password: str

class UserLogin(BaseModel):
    login: str
    password: str

def authenticate_user(login: str, password: str):
    user = users_db.get(login)
    if not user or not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/v1/user")
async def create_user(user: UserCreate):
    if user.login in users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    users_db[user.login] = {
        "login": user.login,
        "hashed_password": hash_password(user.password)
    }
    return {"message": "User created", "login": user.login}

@app.post("/v1/token")
async def login(user: UserLogin):
    authenticated_user = authenticate_user(user.login, user.password)
    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password"
        )
    token = create_access_token(data={"sub": user.login})
    return {"token": token}

@app.get("/v1/user")
async def get_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        login = payload.get("sub")
        if not login or login not in users_db:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"login": login}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/v1/token/validation/")
async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        login = payload.get("sub")
        if not login or login not in users_db:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"valid": True, "login": login}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/health")
async def health():
    return {"status": "ok"}
