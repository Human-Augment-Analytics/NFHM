from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class RedisSettings(BaseModel):
    host: str
    port: int = Field(default=6379)
    database: int = Field(default=0)
    username: str | None = None
    password: str | None = None


class MongoSettings(BaseModel):
    host: str
    port: int = Field(default=27017)
    database: str = Field(default='NFHM')
    username: str | None = None
    password: str | None = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter='__')
    redis: RedisSettings | None = None
