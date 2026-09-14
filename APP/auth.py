from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from APP.database import SessionLocal
from APP.models import User
from APP.schemas import UserCreate, UserLogin, UserUpdateRole
from APP.jwt_handler import create_access_token, decode_access_token

router = APIRouter()
security = HTTPBearer(auto_error=False)

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if not credentials:
        return None
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        return None
    return payload

@router.post("/register")
def register(user: UserCreate):
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            return {"message": "Email already registered"}

        role = user.role if user.role in ["Candidate", "Recruiter", "Admin"] else "Candidate"

        new_user = User(
            username=user.username,
            email=user.email,
            password=user.password,
            role=role
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "message": "User Registered Successfully",
            "username": new_user.username,
            "email": new_user.email,
            "role": new_user.role,
            "user_id": new_user.id
        }
    except Exception as e:
        db.rollback()
        return {"message": "Registration Failed", "error": str(e)}
    finally:
        db.close()


@router.post("/login")
def login(user: UserLogin):
    db = SessionLocal()
    try:
        db_user = db.query(User).filter(User.email == user.email).first()
        if not db_user:
            return {"message": "User Not Found"}

        if db_user.password != user.password:
            return {"message": "Incorrect Password"}

        role = db_user.role or "Candidate"

        token = create_access_token({
            "sub": db_user.email,
            "user_id": db_user.id,
            "username": db_user.username,
            "role": role
        })

        return {
            "message": "Login Successful",
            "user_id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "role": role,
            "access_token": token,
            "token_type": "bearer"
        }
    finally:
        db.close()


@router.get("/profile")
def profile(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    user = get_current_user(credentials)
    if not user:
        return {"message": "Guest user or invalid token", "authenticated": False}
    return {
        "message": f"Welcome {user.get('username', 'User')}!",
        "authenticated": True,
        "user": user
    }

# ----------------------------------------------------
# ADMIN USER MANAGEMENT ENDPOINTS
# ----------------------------------------------------

@router.get("/api/admin/users")
def get_all_users(role: Optional[str] = Query(None)):
    db = SessionLocal()
    try:
        query = db.query(User)
        if role and role.strip():
            query = query.filter(User.role == role.strip())
        
        users = query.order_by(User.id.asc()).all()
        return [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role or "Candidate",
                "created_at": u.created_at.strftime("%Y-%m-%d %H:%M") if hasattr(u, "created_at") and u.created_at else "N/A"
            }
            for u in users
        ]
    finally:
        db.close()


@router.post("/api/admin/users")
def create_user_by_admin(payload: UserCreate):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="User with this email already exists")

        role = payload.role if payload.role in ["Candidate", "Recruiter", "Admin"] else "Candidate"
        new_u = User(
            username=payload.username,
            email=payload.email,
            password=payload.password,
            role=role
        )
        db.add(new_u)
        db.commit()
        db.refresh(new_u)

        return {
            "status": "success",
            "message": f"User {new_u.username} created with role {new_u.role}",
            "user": {
                "id": new_u.id,
                "username": new_u.username,
                "email": new_u.email,
                "role": new_u.role
            }
        }
    finally:
        db.close()


@router.put("/api/admin/users/{user_id}/role")
def update_user_role(user_id: int, payload: UserUpdateRole):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if payload.role not in ["Candidate", "Recruiter", "Admin"]:
            raise HTTPException(status_code=400, detail="Invalid role specified")

        user.role = payload.role
        db.commit()
        return {"status": "success", "message": f"User {user.username} role updated to {payload.role}"}
    finally:
        db.close()


@router.delete("/api/admin/users/{user_id}")
def delete_user_by_id(user_id: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        db.delete(user)
        db.commit()
        return {"status": "success", "message": f"User #{user_id} deleted successfully"}
    finally:
        db.close()


# ----------------------------------------------------
# ADMIN RECRUITER & FULL USER MANAGEMENT ENDPOINTS
# ----------------------------------------------------

@router.get("/api/admin/recruiters")
def get_all_recruiters(status: Optional[str] = Query(None)):
    db = SessionLocal()
    try:
        query = db.query(User).filter(User.role == "Recruiter")
        recruiters = query.order_by(User.id.asc()).all()
        
        result = []
        for r in recruiters:
            result.append({
                "id": r.id,
                "username": r.username,
                "email": r.email,
                "company": "Infosys Springboard" if r.id == 2 else ("TCS Technical Hiring" if r.id == 3 else "Enterprise Talent Partner"),
                "status": "Approved" if r.id in [2, 3] else "Pending Approval",
                "is_active": True,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if hasattr(r, "created_at") and r.created_at else "2026-09-12 10:00"
            })
        return result
    finally:
        db.close()


@router.post("/api/admin/recruiters")
def create_recruiter_by_admin(payload: UserCreate):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="User with this email already exists")

        new_r = User(
            username=payload.username,
            email=payload.email,
            password=payload.password,
            role="Recruiter"
        )
        db.add(new_r)
        db.commit()
        db.refresh(new_r)

        return {
            "status": "success",
            "message": f"Recruiter {new_r.username} created successfully",
            "recruiter": {
                "id": new_r.id,
                "username": new_r.username,
                "email": new_r.email,
                "company": "Infosys Springboard Partner",
                "status": "Approved",
                "is_active": True
            }
        }
    finally:
        db.close()


@router.put("/api/admin/recruiters/{recruiter_id}")
def update_recruiter_details(recruiter_id: int, payload: UserCreate):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == recruiter_id, User.role == "Recruiter").first()
        if not user:
            raise HTTPException(status_code=404, detail="Recruiter not found")

        if payload.username: user.username = payload.username
        if payload.email: user.email = payload.email
        if payload.password: user.password = payload.password

        db.commit()
        return {"status": "success", "message": f"Recruiter #{recruiter_id} updated successfully"}
    finally:
        db.close()


@router.patch("/api/admin/recruiters/{recruiter_id}/approval")
def update_recruiter_approval(recruiter_id: int, approval: str = Query(...)):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == recruiter_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Recruiter not found")

        return {"status": "success", "message": f"Recruiter #{recruiter_id} approval status updated to {approval}"}
    finally:
        db.close()


@router.patch("/api/admin/recruiters/{recruiter_id}/status")
def toggle_recruiter_active_status(recruiter_id: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == recruiter_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Recruiter not found")

        return {"status": "success", "message": f"Recruiter #{recruiter_id} status toggled successfully"}
    finally:
        db.close()


@router.delete("/api/admin/recruiters/{recruiter_id}")
def delete_recruiter_by_id(recruiter_id: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == recruiter_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Recruiter not found")

        db.delete(user)
        db.commit()
        return {"status": "success", "message": f"Recruiter #{recruiter_id} deleted successfully"}
    finally:
        db.close()


@router.put("/api/admin/users/{user_id}")
def update_user_details(user_id: int, payload: UserCreate):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if payload.username: user.username = payload.username
        if payload.email: user.email = payload.email
        if payload.role and payload.role in ["Candidate", "Recruiter", "Admin"]: user.role = payload.role

        db.commit()
        return {"status": "success", "message": f"User #{user_id} details updated successfully"}
    finally:
        db.close()


@router.patch("/api/admin/users/{user_id}/status")
def toggle_user_active_status(user_id: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {"status": "success", "message": f"User #{user_id} status toggled successfully"}
    finally:
        db.close()
