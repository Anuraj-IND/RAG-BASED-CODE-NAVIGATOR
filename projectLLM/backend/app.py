from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os, shutil, zipfile
from fastapi.responses import JSONResponse
app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (you can restrict this to specific domains)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_REPO = "data/repo"
os.makedirs(DATA_REPO, exist_ok=True)

@app.get("/")
def health():
    return {"status": "ok"}

from rag.indexer import index_repo

from rag.query import ask_question
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_REPO = os.path.join(BASE_DIR, "data", "repo")
DATA_INDEX = os.path.join(BASE_DIR, "data", "index")


DATA_REPO = "data/repo"
DATA_INDEX = "data/index"


import subprocess

import subprocess
import os
import shutil
from urllib.parse import urlparse

@app.post("/load-github")
def load_github(repo_url: str):
    # clean previous state
    shutil.rmtree(DATA_REPO, ignore_errors=True)
    shutil.rmtree(DATA_INDEX, ignore_errors=True)

    os.makedirs(DATA_REPO, exist_ok=True)
    os.makedirs(DATA_INDEX, exist_ok=True)

    # extract repo name from URL
    repo_name = os.path.splitext(
        os.path.basename(urlparse(repo_url).path)
    )[0]

    target_path = os.path.join(DATA_REPO, repo_name)

    try:
        subprocess.run(
            ["git", "clone", repo_url, target_path],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        return {
            "error": "Git clone failed",
            "details": e.stderr
        }

    return {
        "message": "GitHub repo cloned successfully",
        "repo_path": target_path
    }


import stat
import time
import gc

def _force_delete(func, path, exc_info):
    # Windows fix: remove read-only + retry
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass

@app.post("/reset")
def reset():
    gc.collect()
    time.sleep(0.3)

    for path in [DATA_REPO, DATA_INDEX]:
        if os.path.exists(path):
            try:
                shutil.rmtree(path, onerror=_force_delete)
            except Exception as e:
                return {
                    "error": "Failed to fully reset",
                    "details": str(e)
                }

    return {"message": "reset done"}




@app.post("/ask")
def ask_api(query: str):
    try:
        answer = ask_question(DATA_INDEX, query)
        return JSONResponse(content={"answer": answer})
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

DATA_INDEX = "data/index"
os.makedirs(DATA_INDEX, exist_ok=True)

@app.post("/index-repo")
def index_repo_api():
    count = index_repo(DATA_REPO, DATA_INDEX)
    return {"indexed_chunks": count}


@app.post("/upload-repo")
def upload_repo(file: UploadFile = File(...)):
    shutil.rmtree(DATA_REPO, ignore_errors=True)
    os.makedirs(DATA_REPO, exist_ok=True)

    zip_path = os.path.join(DATA_REPO, file.filename)
    with open(zip_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # unzip
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(DATA_REPO)

    os.remove(zip_path)

    return {"message": "repo uploaded and extracted"}
