from contextlib import asynccontextmanager
from pathlib import Path

from redis.asyncio import Redis
from redisvl.index import AsyncSearchIndex

#main.py
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
# from core.config import settings
from controllers.search_controller import router as search_router
from datetime import datetime

from settings import Settings

settings = Settings()
current_dir = Path(__file__).parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.redis = Redis(**settings.redis.model_dump())
    await app.redis.ping()
    app.searchindex = AsyncSearchIndex.from_yaml(str(current_dir / 'schema.yaml'))
    app.searchindex.set_client(app.redis)
    await app.searchindex.create()

    yield
    # Clean up the ML models and release the resources
    await app.redis.aclose()

app = FastAPI()

app.include_router(search_router, prefix="/api")

app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")

@app.get("/")
def hello_api(request: Request):
    # return {"msg":"Hello FastAPI🚀"}
    client: Redis = request.app.redis
    return FileResponse('../frontend/index.html')

def healthcheck():
    return {"status": "running", "now": datetime.now()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
