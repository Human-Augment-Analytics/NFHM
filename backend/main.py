#main.py

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
# from core.config import settings

# app = FastAPI(title=settings.PROJECT_NAME,version=settings.PROJECT_VERSION)
app = FastAPI()

print("Hello FastAPI🚀")

app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")

@app.get("/")
def hello_api():
    # return {"msg":"Hello FastAPI🚀"}
    return FileResponse('../frontend/index3.html')