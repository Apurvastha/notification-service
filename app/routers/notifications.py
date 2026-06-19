from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from app.database import get_db
from app.models import Notification
from app.schemas import (
    NotificationCreate,
    NotificationResponse,
    UnreadCountResponse
)


from app.dependencies import get_current_user_id

router = APIRouter(
    prefix='/notifications',
    tags=['Notifications']
)

@router.post('/', response_model=NotificationResponse, status_code=201)
async def create_notification(
    payload: NotificationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new notification for a user."""
    notification = Notification(**payload.model_dump())
    db.add(notification)
    await db.flush() # assign ID without committing
    await db.refresh(notification) # loads DB-generated values
    return notification


@router.get('/', response_model=list[NotificationResponse])
async def list_notification(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 20
):
    """List notification for the authenticated user."""
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.patch('/{notification_id}/read', response_model=NotificationResponse)
async def mark_as_read(
    notification_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Mark a notification as read"""
    result = await db.execute(
        select(Notification)
        .where(
            Notification.id == notification_id,
            Notification.user_id == user_id
        )
    )
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Notification not found'
        )
    notification.is_read = True
    notification.read_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(notification)
    return notification


@router.get('/unread-count', response_model=UnreadCountResponse)
async def unread_count(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get count of unread notification for the authenticated user."""
    result = await db.execute(
        select(func.count(Notification.id))
        .where(
            Notification.user_id == user_id,
            not Notification.is_read
        )
    )
    count = result.scalar()
    return UnreadCountResponse(count=count, user_id=user_id)