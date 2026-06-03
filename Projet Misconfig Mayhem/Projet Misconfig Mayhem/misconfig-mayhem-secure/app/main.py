from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from pathlib import Path
from typing import List
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# ✅ CORRECTION M2 : Debug désactivé en production
app = FastAPI(
    debug=False,  # ✅ DEBUG DÉSACTIVÉ
    title="SharePy - Mini Dropbox (Secure)",
    version="2.0.0-secure"
)

# Configuration CORS plus stricte
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:80"],  # ✅ Origines spécifiques
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # ✅ Méthodes limitées
    allow_headers=["*"],
)

# Configuration
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ✅ CORRECTION M1 : Mot de passe depuis variable d'environnement
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "default-change-me")

# Logging en mode INFO (pas DEBUG)
logging.basicConfig(
    level=logging.INFO,  # ✅ Moins verbeux
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Base de données simulée
users_db = {
    "admin": ADMIN_PASSWORD,  # ✅ Utilise la variable d'environnement
    "user1": os.getenv("USER1_PASSWORD", "change-me")
}

files_db = []


@app.get("/")
def root():
    """Page d'accueil"""
    return {
        "message": "Bienvenue sur SharePy - Version Sécurisée",
        "version": "2.0.0-secure",
        "security": "✅ Hardened",
        "endpoints": {
            "login": "/login",
            "upload": "/upload",
            "files": "/files",
            "download": "/download/{filename}",
            "health": "/health"
        }
    }


@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    """
    Connexion utilisateur
    ✅ CORRECTION : Messages d'erreur génériques, pas de stack trace exposée
    """
    logger.info(f"Tentative de connexion pour : {username}")
    
    # Vérification des credentials
    if username not in users_db:
        # ✅ Message générique pour éviter l'énumération d'utilisateurs
        logger.warning(f"Tentative de connexion échouée pour : {username}")
        raise HTTPException(
            status_code=401,
            detail="Identifiants invalides"  # ✅ Message générique
        )
    
    if users_db[username] != password:
        logger.warning(f"Mot de passe incorrect pour : {username}")
        raise HTTPException(
            status_code=401,
            detail="Identifiants invalides"  # ✅ Message générique
        )
    
    logger.info(f"Connexion réussie pour : {username}")
    return {
        "status": "success",
        "message": f"Bienvenue {username}",
        "token": f"secure-jwt-token-{username}"
    }


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload un fichier
    ✅ Validation et gestion d'erreur sécurisée
    """
    try:
        # ✅ Validation du nom de fichier
        if not file.filename or len(file.filename) > 255:
            raise HTTPException(
                status_code=400,
                detail="Nom de fichier invalide"
            )
        
        # ✅ Empêcher les path traversal
        safe_filename = os.path.basename(file.filename)
        file_path = UPLOAD_DIR / safe_filename
        
        # Sauvegarder le fichier
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_info = {
            "filename": safe_filename,
            "size": file_path.stat().st_size
        }
        files_db.append(file_info)
        
        logger.info(f"Fichier uploadé : {safe_filename}")
        
        return {
            "status": "success",
            "message": "Fichier uploadé avec succès",
            "file": file_info
        }
    
    except Exception as e:
        # ✅ Log l'erreur mais ne l'expose PAS à l'utilisateur
        logger.error(f"Erreur lors de l'upload : {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de l'upload du fichier"  # ✅ Message générique
        )


@app.get("/files")
def list_files():
    """
    Liste les fichiers (authentification requise en production)
    """
    return {
        "total": len(files_db),
        "files": files_db
    }


@app.get("/download/{filename}")
def download_file(filename: str):
    """
    Télécharge un fichier
    ✅ Protection contre path traversal
    """
    # ✅ Nettoyer le nom de fichier
    safe_filename = os.path.basename(filename)
    file_path = UPLOAD_DIR / safe_filename
    
    # ✅ Vérifier que le fichier existe et est dans le bon dossier
    if not file_path.exists() or not str(file_path).startswith(str(UPLOAD_DIR)):
        logger.warning(f"Tentative d'accès à un fichier invalide : {filename}")
        raise HTTPException(
            status_code=404,
            detail="Fichier introuvable"
        )
    
    return FileResponse(
        path=file_path,
        filename=safe_filename,
        media_type='application/octet-stream'
    )


# ✅ CORRECTION : Endpoint /debug/info SUPPRIMÉ
# Il ne doit PAS exister en production


@app.get("/health")
def health_check():
    """Health check pour monitoring"""
    return {
        "status": "healthy",
        "version": "2.0.0-secure"
    }

# ============================================================
# ENDPOINT DE TEST : Pour démontrer que les erreurs sont masquées
# ============================================================

@app.get("/error-test")
def trigger_error():
    """
    Endpoint de test qui provoque une erreur volontaire.
    ✅ AVEC debug=False : L'erreur ne montre PAS la stack trace
    """
    # Ces variables sensibles NE seront PAS exposées grâce à debug=False
    database_url = os.getenv("DATABASE_URL", "postgresql://secret")
    admin_password = os.getenv("ADMIN_PASSWORD", "supersecret")
    
    # Provoquer une erreur intentionnelle
    result = 1 / 0
    
    return {"result": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
