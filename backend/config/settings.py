from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Annotated
class Settings(BaseSettings):
    model_config = SettingsConfigDict(protected_namespaces=('settings_',))
    
    model_name: Annotated[str, Field(
        default="ViT-B-32",
        description="Name of the CLIP model to use"
    )]
    
    model_pretrained: Annotated[str, Field(
        default="laion2b_s34b_b79k",
        description="Pretrained weights to use for the CLIP model"
    )]
    
    database_url: Annotated[str, Field(
        default="postgresql+asyncpg://postgres:postgres@postgres/nfhm",
        description="PostgreSQL connection string",
    )]
    
    pool_size: Annotated[int, Field(
        default=5,
        ge=1,
        description="The number of connections to keep open in the connection pool"
    )]
    
    max_overflow: Annotated[int, Field(
        default=10,
        ge=0,
        description="The maximum number of connections to allow in the connection pool 'overflow'"
    )]
