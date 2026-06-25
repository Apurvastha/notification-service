from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    # database
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # app
    APP_NAME: str = 'Notification Service'
    DEBUG: bool = False
    LOG_LEVEL: str = 'INFO'

    model_config = ConfigDict(env_file='.env')




settings = Settings()
