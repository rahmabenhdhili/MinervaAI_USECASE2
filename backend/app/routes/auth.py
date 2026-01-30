from fastapi import APIRouter, HTTPException, status
from app.models.user import UserCreate, UserOut
from app.database import get_users_collection
from app.core.security import hash_password, verify_password
from app.core.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

# SIGNUP
@router.post("/signup", response_model=UserOut)
async def signup(user: UserCreate):
    users = get_users_collection()
    existing = await users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    hashed_pw = hash_password(user.password)
    result = await users.insert_one({"email": user.email, "password": hashed_pw})

    return {"id": str(result.inserted_id), "email": user.email}

# LOGIN
@router.post("/login")
async def login(user: UserCreate):
    users = get_users_collection()
    db_user = await users.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": str(db_user["_id"])})
    return {"access_token": token, "token_type": "bearer"}
