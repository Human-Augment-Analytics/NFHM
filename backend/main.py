# main.py
from fastapi import FastAPI
# from core.config import settings
from controllers.search_controller import router as search_router
from datetime import datetime

app = FastAPI()

app.include_router(search_router, prefix="/api")


def healthcheck():
    return {"status": "running", "now": datetime.now()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
