from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from APP.database import SessionLocal
from APP.models import Notification
from APP.email_service import send_email_notification

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

class NotificationCreateSchema(BaseModel):
    user_email: Optional[str] = "candidate@smarthire.ai"
    title: str
    message: str
    notification_type: Optional[str] = "INFO"
    send_email: Optional[bool] = False

def create_notification(db, user_email: str, title: str, message: str, notification_type: str = "INFO", send_email: bool = True):
    try:
        notif = Notification(
            user_email=user_email,
            title=title,
            message=message,
            notification_type=notification_type,
            is_read=0,
            created_at=datetime.utcnow()
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)

        if send_email and user_email:
            send_email_notification(user_email, title, message)

        return notif
    except Exception as e:
        print("Error creating notification:", e)
        return None

@router.get("")
def list_notifications(user_email: Optional[str] = None):
    db = SessionLocal()
    try:
        query = db.query(Notification)
        if user_email:
            query = query.filter((Notification.user_email == user_email) | (Notification.user_email == None))
        
        notifications = query.order_by(Notification.created_at.desc()).limit(50).all()
        
        return [
            {
                "id": n.id,
                "user_email": n.user_email,
                "title": n.title,
                "message": n.message,
                "notification_type": n.notification_type,
                "is_read": bool(n.is_read),
                "created_at": n.created_at.isoformat() if n.created_at else None
            }
            for n in notifications
        ]
    finally:
        db.close()

@router.post("/{id}/read")
def mark_notification_read(id: int):
    db = SessionLocal()
    try:
        notif = db.query(Notification).filter(Notification.id == id).first()
        if not notif:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        notif.is_read = 1
        db.commit()
        return {"status": "success", "message": "Notification marked as read", "id": id}
    finally:
        db.close()

@router.post("/send")
def send_notification_endpoint(payload: NotificationCreateSchema):
    db = SessionLocal()
    try:
        notif = create_notification(
            db,
            user_email=payload.user_email,
            title=payload.title,
            message=payload.message,
            notification_type=payload.notification_type,
            send_email=payload.send_email
        )
        return {
            "status": "success",
            "message": "Notification generated",
            "notification_id": notif.id if notif else None
        }
    finally:
        db.close()
