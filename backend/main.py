# main.py
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
import torch
import open_clip
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.pool import AsyncAdaptedQueuePool
from config.settings import Settings

from controllers.search_controller import router as search_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


settings = Settings()

def get_db_engine() -> AsyncEngine:
    return create_async_engine(
        settings.database_url,
        echo=True,
        poolclass=AsyncAdaptedQueuePool,
        pool_size=settings.pool_size,
        max_overflow=settings.max_overflow
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up application...")
    try:
        # MPS is for apple silicon GPU, cuda is ofc nvidia.
        device = torch.device("mps:0" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {device}")
        
        model, _, preprocess = open_clip.create_model_and_transforms(settings.model_name, pretrained=settings.model_pretrained, device=device)
        model = model.to(device)
        tokenizer = open_clip.get_tokenizer(settings.model_name)
        
        app.state.model = model
        app.state.preprocess = preprocess
        app.state.device = device
        app.state.tokenizer = tokenizer
        app.state.db_engine = get_db_engine()
        
        logger.info("Application startup complete.")
        yield
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    finally:
        logger.info("Shutting down application...")
        # Clean up resources
        del app.state.model
        del app.state.preprocess
        del app.state.tokenizer
        await app.state.db_engine.dispose()
        torch.cuda.empty_cache()
        logger.info("Application shutdown complete.")

app = FastAPI(lifespan=lifespan)

app.include_router(search_router, prefix="/api")

@app.get("/")
async def healthcheck():
    try:
        # You might want to add a database connection check here
        return {"status": "running", "now": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Healthcheck failed: {str(e)}")
        return {"status": "error", "message": "Healthcheck failed"}

def get_settings() -> Settings:
    return settings

app.dependency_overrides[get_settings] = get_settings

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)