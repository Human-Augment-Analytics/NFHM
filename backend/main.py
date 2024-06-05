#main.py
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
# from core.config import settings
from controllers.search_controller import router as search_router
from datetime import datetime

app = FastAPI()

app.include_router(search_router, prefix="/api")

app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")

@app.get("/")
def hello_api():
    # return {"msg":"Hello FastAPI🚀"}
    return FileResponse('../frontend/index.html')

def healthcheck():
    return {"status": "running", "now": datetime.now()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
