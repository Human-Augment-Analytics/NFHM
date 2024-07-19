# main.py
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
import torch
import open_clip

# from core.config import settings
from controllers.search_controller import router as search_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    if torch.backends.mps.is_available():
        device = torch.device("mps:0")
        print("Using MPS")
    else:
        device = torch.device("cpu")
    model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k', device=device)
    model = model.to(device)
    tokenizer = open_clip.get_tokenizer('ViT-B-32')
    app.model = model
    app.preprocess = preprocess
    app.device = device
    app.tokenizer = tokenizer
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(search_router, prefix="/api")

# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import FileResponse

# app.mount("/static", StaticFiles(directory="./frontend/static"), name="static")

# @app.get("/")
# def hello_api():
#     # return {"msg":"Hello FastAPI🚀"}
#     return FileResponse('./frontend/index.html')

def healthcheck():
    return {"status": "running", "now": datetime.now()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
