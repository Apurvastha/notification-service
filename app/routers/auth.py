from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User
from app.schemas import UserRegister, UserResponse, TokenResponse
from app.auth import hash_password, verify_password, create_access_token
from app.dependencies import get_current_user


router = APIRouter(
    prefix='/auth',
    tags=['Authentication']
)


@router.post('/register', response_model=UserResponse, status_code=201)
async def register(
    payload: UserRegister,
    db: AsyncSession = Depends(get_db)
):

    # check email is not already taken
    result = await db.execute(
        select(User).where(User.email == payload.email)
    )

    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Email already registered'
        )

    # check username is not already taken
    result = await db.execute(
        select(User).where(User.username == payload.username)
    )

    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Username already taken'
        )

    # hash the password - never store plain text
    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password)
    )

    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.post('/token', response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Login with username and password
    Return a JWt access token
    Uses Oauth2passwordrequestfrom - expects form data not Json
    """

    # find user by username
    result = await db.execute(
        select(User).where(User.username == form_data.username)
    )

    user = result.scalar_one_or_none()

    # verify user existes and passwrd is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='User account is disabled'
        )

    # create JWT token with user info as claims
    access_token = create_access_token(data={
        'user_id': user.id,
        'username': user.username,
        'email': user.email
    })

    return TokenResponse(access_token=access_token)


@router.get('/me', response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
