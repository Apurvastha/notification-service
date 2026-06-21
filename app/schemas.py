from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, Any


#---- Auth Schemas --------------------------------------------------------------------------------------------------------

class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    is_active: bool
    created_at: datetime

    model_config = {'from_attributes': True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class LoginRequest(BaseModel):
    username: str
    password: str

    

#---- Notification Schemas----------------------------------------------------------------------------------------------------
class NotificationCreate(BaseModel):
    """Schema for creating a notification - what the client sends."""
    user_id: int
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1)
    notification_type: str = Field(default='info')
    extra_data: Optional[dict[str, Any]] = None


class NotificationResponse(BaseModel):
    """Schema for returning a notification - what the client recieves"""
    id: int
    user_id: int
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None
    extra_data: Optional[dict[str, Any]] = None

    model_config = {'from_attributes': True}
    # from_attibutes=true lets pydantic read from SQLAlchemy model instance
    # equivalent to Django serializer source = parameter

class NotificationUpdate(BaseModel):
    """Schema for marking as read."""
    is_read: bool = True


class UnreadCountResponse(BaseModel):
    count: int
    user_id: int