#main.py
from fastapi import FastAPI
# from core.config import settings
from .controllers.search_controller import router as search_router
from datetime import datetime

app = FastAPI()

app.include_router(search_router, prefix="/api")

# <<<<<<< TODO: Make work with Jacob's changes @ https://github.com/Human-Augment-Analytics/NFHM/pull/21/commits/7fc86736f9b426b952704a041e37ac899670e818
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app.mount("/static", StaticFiles(directory="./frontend/static"), name="static")

@app.get("/")
def hello_api():
    # return {"msg":"Hello FastAPI🚀"}
    return FileResponse('./frontend/index.html')

# =======
# >>>>>>> END TODO: Make work with Jacob's changes @
def healthcheck():
    return {"status": "running", "now": datetime.now()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
