from pydantic_settings import BaseSettings


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

    class Config:
        env_file = '.env'


settings = Settings()
