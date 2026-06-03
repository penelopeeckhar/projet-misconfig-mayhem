from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from pathlib import Path
from typing import List
import logging

# ❌ MISCONFIGURATION M2 : Debug mode activé en production
app = FastAPI(
    debug=True,  # ← VULNÉRABILITÉ : Stack traces complètes exposées
    title="SharePy - Mini Dropbox",
    version="1.0.0"
)

# Configuration CORS permissive (bonus misconfiguration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Logging
logging.basicConfig(level=logging.DEBUG)  # ← Logs verbeux
logger = logging.getLogger(__name__)

# Simulated database (en mémoire pour simplifier)
users_db = {
    "admin": "admin123",  # ← VULNÉRABILITÉ : Mot de passe hardcodé
    "user1": "password123"
}

files_db = []  # Liste des fichiers uploadés


@app.get("/")
def root():
    """Page d'accueil"""
    return {
        "message": "Bienvenue sur SharePy - Mini Dropbox",
        "version": "1.0.0",
        "endpoints": {
            "login": "/login",
            "upload": "/upload",
            "files": "/files",
            "download": "/download/{filename}"
        }
    }


@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    """
    Connexion utilisateur
    ❌ VULNÉRABILITÉ : Si erreur, le debug mode révèle tout
    """
    logger.debug(f"Tentative de connexion : {username}")
    
    # Vérification des credentials
    if username not in users_db:
        # ❌ Cette exception va révéler la stack trace complète en debug mode
        raise HTTPException(
            status_code=401,
            detail=f"Utilisateur {username} introuvable dans la base"
        )
    
    if users_db[username] != password:
        # ❌ Même problème ici
        raise HTTPException(
            status_code=401,
            detail="Mot de passe incorrect"
        )
    
    return {
        "status": "success",
        "message": f"Bienvenue {username}",
        "token": f"fake-jwt-token-{username}"
    }


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload un fichier
    """
    try:
        file_path = UPLOAD_DIR / file.filename
        
        # Sauvegarder le fichier
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Ajouter à la "base de données"
        file_info = {
            "filename": file.filename,
            "path": f"/uploads/{file.filename}",
            "size": file_path.stat().st_size
        }
        files_db.append(file_info)
        
        logger.info(f"Fichier uploadé : {file.filename}")
        
        return {
            "status": "success",
            "message": "Fichier uploadé avec succès",
            "file": file_info
        }
    
    except Exception as e:
        # ❌ En debug mode, cette erreur révélera tout le stack trace
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files")
def list_files():
    """
    Liste tous les fichiers uploadés
    """
    return {
        "total": len(files_db),
        "files": files_db
    }


@app.get("/download/{filename}")
def download_file(filename: str):
    """
    Télécharge un fichier
    """
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Fichier {filename} introuvable"
        )
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )


@app.get("/debug/info")
def debug_info():
    """
    ❌ BONUS VULNERABILITY : Endpoint qui expose des infos sensibles
    """
    return {
        "environment": dict(os.environ),  # ← Expose toutes les variables d'env
        "upload_dir": str(UPLOAD_DIR),
        "users": list(users_db.keys()),
        "files_count": len(files_db)
    }


@app.get("/health")
def health_check():
    """Health check"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
