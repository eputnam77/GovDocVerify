import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api import download_result, process_doc_endpoint

app = FastAPI(title="FAA-Document-Checker API")

allow_origins_env = os.getenv("ALLOW_ORIGINS")
if allow_origins_env:
    allow_origins = [o.strip() for o in allow_origins_env.split(",") if o.strip()]
else:
    allow_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

app.post("/process")(process_doc_endpoint)
app.get("/results/{result_id}.{fmt}")(download_result)

# Optionally serve static files (for Docker deployment)
STATIC_DIR = os.getenv("STATIC_DIR")
if STATIC_DIR and os.path.isdir(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
