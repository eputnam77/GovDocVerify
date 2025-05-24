import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.api import process_doc_endpoint

app = FastAPI(title="FAA-Document-Checker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # tighten this in prod
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

app.post("/process")(process_doc_endpoint)

# Optionally serve static files (for Docker deployment)
STATIC_DIR = os.getenv("STATIC_DIR")
if STATIC_DIR and os.path.isdir(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")