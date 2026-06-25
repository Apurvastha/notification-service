from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from app.database import get_db
from typing import Optional
from app.models import Notification
from app.schemas import (
    NotificationCreate,
    NotificationResponse,
    UnreadCountResponse
)


from app.dependencies import get_current_user_id
from app.tasks import (
    log_notification_created,
    log_notification_read,
    simulate_push_notification
)



router = APIRouter(
    prefix='/notifications',
    tags=['Notifications']
)

@router.post('/', response_model=NotificationResponse, status_code=201)
async def create_notification(
    payload: NotificationCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new notification for a user.
    Response is sent immediately - push notification fires in background.
    """
    notification = Notification(**payload.model_dump())
    db.add(notification)
    await db.flush() # assign ID without committing
    await db.refresh(notification) # loads DB-generated values

    # these run after the response is sent
    background_tasks.add_task(
        log_notification_created,
        notification_id=notification.id,
        user_id=notification.user_id,
        title=notification.title
    )
    background_tasks.add_task(
        simulate_push_notification,
        user_id=notification.user_id,
        title=notification.title,
        message=notification.message
    )

    return notification


@router.get('/', response_model=list[NotificationResponse])
async def list_notification(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    unread_only: bool = Query(default=False),
    notification_type: Optional[str] = Query(default=None)
):
    """
    List notification for the authenticated user.
    Supports filtering by read status and type
    """
    query = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    # add optional filters
    if unread_only:
        query = query.where(Notification.is_read.is_(False))
    
    if notification_type:
        query = query.where(Notification.notification_type == notification_type)
    
    result = await db.execute(query)
    return result.scalars().all()


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
            Notification.is_read.is_(False)
        )
    )
    count = result.scalar()
    return UnreadCountResponse(count=count, user_id=user_id)


@router.get('/{notification_id}', response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Notification).where(
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
    return notification


@router.patch('/{notification_id}/read', response_model=NotificationResponse)
async def mark_as_read(
    notification_id: int,
    background_tasks: BackgroundTasks,
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

    # log the read event in background
    background_tasks.add_task(
        log_notification_read,
        notification_id=notification.id,
        user_id=notification.user_id
    )

    return notification


@router.patch('/read-all', response_model=dict)
async def mark_all_read(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk update - mark all unread notifications as read.
    Uses UPDATE directly instead of fetching each row.
    """
    result = await db.execute(
        update(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False)
        )
        .values(
            is_read=True,
            read_at=datetime.now(timezone.utc)
        )
    )
    return {'updated': result.rowcount}


@router.delete('/{notification_id}', status_code=204)
async def delete_notification(
    notification_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
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
    await db.delete(notification)