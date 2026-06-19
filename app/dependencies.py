from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.config import settings
from app.database import get_db, AsyncSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    """Dependency that extracts user_id from JWT token.
    Used in any endpoint that requires auth
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'}
    )
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: int = payload.get('user_id')
        if user_id is None:
            raise credentials_exception
        return user_id

    except JWTError:
        raise credentials_exception
    
