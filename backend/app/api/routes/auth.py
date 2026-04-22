"""
Auth routes — email/password with JWT + bcrypt
POST /auth/register
POST /auth/login  
GET  /auth/me
POST /auth/logout
"""

import uuid, os
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import jwt
import bcrypt

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY        = os.getenv("SECRET_KEY", "outreachx-dev-secret-2024")
TOKEN_EXPIRE_DAYS = 30
oauth2_scheme     = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

# In-memory user store {email: user_dict}
_users: dict = {}


# ── Helpers ───────────────────────────────────────────────────────────────────

def hash_pw(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_pw(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def make_token(user_id: str, email: str) -> str:
    return jwt.encode(
        {"sub": user_id, "email": email,
         "exp": datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)},
        SECRET_KEY, algorithm="HS256"
    )

def read_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Session expired — please log in again")
    except Exception:
        raise HTTPException(401, "Invalid token")

def current_user(token: str = Depends(oauth2_scheme)) -> dict:
    if not token:
        raise HTTPException(401, "Not logged in")
    data = read_token(token)
    user = _users.get(data.get("email", ""))
    if not user:
        raise HTTPException(401, "User not found")
    return user


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterIn(BaseModel):
    email:    str
    password: str
    name:     str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/register")
async def register(body: RegisterIn):
    email = body.email.lower().strip()
    if "@" not in email:
        raise HTTPException(400, "Invalid email")
    if len(body.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    if not body.name.strip():
        raise HTTPException(400, "Name is required")
    if email in _users:
        raise HTTPException(400, "Email already registered — please sign in")

    uid = str(uuid.uuid4())
    _users[email] = {
        "id": uid, "email": email,
        "name": body.name.strip(),
        "hashed_password": hash_pw(body.password),
        "created_at": datetime.utcnow().isoformat(),
    }
    token = make_token(uid, email)
    print(f"[Auth] Registered: {email}")
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": uid, "email": email, "name": body.name.strip()},
    }


@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    email = form.username.lower().strip()
    user  = _users.get(email)
    if not user or not check_pw(form.password, user["hashed_password"]):
        raise HTTPException(401, "Invalid email or password")
    token = make_token(user["id"], email)
    print(f"[Auth] Login: {email}")
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user["id"], "email": email, "name": user["name"]},
    }


@router.get("/me")
async def me(user: dict = Depends(current_user)):
    return {"id": user["id"], "email": user["email"],
            "name": user["name"], "created_at": user["created_at"]}


@router.post("/logout")
async def logout():
    return {"message": "Logged out"}