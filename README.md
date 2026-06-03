# 🔐 Misconfig Mayhem — Analyse et Correction de Vulnérabilités Web

> Projet de cybersécurité appliquée — Red Team / Blue Team  
> Déploiement Docker · FastAPI · Nginx · PostgreSQL · MinIO

---

## 👩‍💻 À propos

Projet réalisé dans le cadre de ma formation en **Développement Numérique & Cybersécurité**.  
Il simule un cycle complet d'audit de sécurité sur une application web intentionnellement vulnérable, depuis l'exploitation des failles jusqu'à leur correction et validation.

**Profil :** Étudiante ingénieure en 4ième année en développement numérique et cybersécurité ·

---

## 🎯 Objectifs du projet

- Déployer une application web **volontairement vulnérable** dans un environnement isolé (VM)
- Identifier et **exploiter** trois misconfiguration critiques (approche Red Team)
- **Corriger** les failles et durcir l'infrastructure (approche Blue Team)
- Valider les corrections avec des **outils professionnels** (Nmap, Nikto) et un script automatisé

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                   Docker Compose                │
│                                                 │
│  ┌──────────┐    ┌──────────┐    ┌───────────┐  │
│  │  Nginx   │───▶│  FastAPI │───▶│ PostgreSQL│  │
│  │ (Reverse │    │ (Python) │    │ (ShareDB) │  │
│  │  Proxy)  │    └──────────┘    └───────────┘  │
│  └──────────┘         │                         │
│                       ▼                         │
│                  ┌─────────┐                    │
│                  │  MinIO  │                    │
│                  │ (S3-like│                    │
│                  │ Storage)│                    │
│                  └─────────┘                    │
└─────────────────────────────────────────────────┘
```

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| Reverse Proxy | Nginx | Routage HTTP, headers de sécurité |
| Application | FastAPI (Python) | API REST, authentification, upload |
| Base de données | PostgreSQL 15 | Persistance des données |
| Stockage objets | MinIO | Gestion des fichiers (compatible S3) |
| Orchestration | Docker Compose | Déploiement multi-conteneurs |

---

## 🗂️ Structure du projet

```
projet-misconfig-mayhem/
│
├── 📁 Projet Misconfig Mayhem/
│   │
│   ├── 📁 misconfig-mayhem/              # Version vulnérable (Red Team)
│   │   ├── app/
│   │   │   ├── main.py                   # Application FastAPI vulnérable
│   │   │   ├── Dockerfile
│   │   │   ├── requirements.txt
│   │   │   └── .env                      # ⚠️ Credentials de démo (fictifs)
│   │   ├── nginx/
│   │   │   ├── nginx.conf                # Config vulnérable (M3)
│   │   │   └── nginx.conf.backup
│   │   ├── scans/
│   │   │   ├── nmap_vulnerable.txt       # Scan avant hardening
│   │   │   └── nikto_vulnerable_full.txt
│   │   ├── uploads/                      # Fichiers de démo
│   │   ├── docker-compose.yml
│   │   └── .gitignore
│   │
│   └── 📁 misconfig-mayhem-secure/       # Version sécurisée (Blue Team)
│       ├── app/
│       │   ├── main.py                   # Application FastAPI durcie
│       │   ├── main.py.vulnerable        # Référence : version avant correction
│       │   ├── Dockerfile
│       │   ├── requirements.txt
│       │   └── .env.example             # ✅ Template sans credentials réels
│       ├── nginx/
│       │   ├── nginx.conf                # Config sécurisée (headers, deny all)
│       │   └── nginx.conf.vulnerable     # Référence : version avant correction
│       ├── scans/
│       │   ├── nmap_secure.txt           # Scan après hardening
│       │   ├── nikto_secure.txt
│       │   ├── nmap_scan_vulnerable.txt  # Comparaison avant/après
│       │   └── nikto_scan_vulnerable.txt
│       ├── uploads/
│       │   └── .gitkeep
│       ├── docker-compose.yml
│       ├── docker-compose.yml.vulnerable
│       ├── check_security.py            # Script de vérification automatique
│       └── .gitignore
│
└── README.pdf
```

---

## 🚨 Vulnérabilités étudiées

### M1 — Credentials en clair `[CRITIQUE]`

**Problème :** Les mots de passe sont stockés en clair dans le fichier `.env` et dans le code.

```python
# ❌ VULNÉRABLE
users_db = {"admin": "admin123", "user1": "password123"}
DATABASE_URL = "postgresql://admin:password123@db:5432/sharedb"
```

**Correction :**
```python
# ✅ SÉCURISÉ
load_dotenv()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "default-change-me")
users_db = {"admin": ADMIN_PASSWORD, "user1": os.getenv("USER1_PASSWORD", "change-me")}
```

**Impact :** Accès complet à la base de données · Compromission de tous les comptes · Élévation de privilèges

---

### M2 — Mode Debug activé en production `[CRITIQUE]`

**Problème :** Le mode debug expose la stack trace complète, les variables d'environnement et un endpoint `/debug/info` non protégé.

```python
# ❌ VULNÉRABLE
app = FastAPI(debug=True)

@app.get("/debug/info")
def debug_info():
    return {"environment": dict(os.environ)}  # Expose TOUS les secrets
```

**Correction :**
```python
# ✅ SÉCURISÉ
app = FastAPI(debug=False)
# Endpoint /debug/info supprimé
logging.basicConfig(level=logging.INFO)  # Pas de DEBUG en production
```

**Impact :** Exposition de la structure interne · Révélation des chemins système · Information disclosure

---

### M3 — Directory Listing activé `[ÉLEVÉ]`

**Problème :** Nginx liste publiquement le contenu du dossier `uploads/`, permettant le téléchargement des fichiers privés d'autres utilisateurs.

```nginx
# ❌ VULNÉRABLE
location /uploads {
    alias /app/uploads/;
    autoindex on;  # Liste tous les fichiers
}
```

**Correction :**
```nginx
# ✅ SÉCURISÉ
location /uploads {
    alias /app/uploads/;
    autoindex off;
    deny all;  # Accès uniquement via /download/{filename}
}
location /debug { deny all; return 404; }
```

**Impact :** Violation de confidentialité · Accès non autorisé aux fichiers · Fuite de données

---

## 🛡️ Améliorations apportées (Blue Team)

| Mesure | Détail |
|--------|--------|
| **Secrets** | Variables d'environnement via `.env` (jamais commités) |
| **Debug** | `debug=False` + suppression de `/debug/info` |
| **Nginx** | `autoindex off` · `deny all` sur `/uploads` · `server_tokens off` |
| **Headers HTTP** | X-Frame-Options · X-Content-Type-Options · CSP · X-XSS-Protection · Referrer-Policy |
| **CORS** | Origines explicites au lieu de `*` |
| **Upload** | Validation du nom de fichier · Protection path traversal · `client_max_body_size` |
| **Logging** | Niveau INFO (pas DEBUG) · Messages d'erreur génériques côté client |
| **Réseau Docker** | Ports internes liés à `127.0.0.1` uniquement |

---

## 📊 Résultats — Comparaison avant/après

### Scans Nmap

| Port | Avant (vulnérable) | Après (sécurisé) |
|------|--------------------|------------------|
| 80 | Ouvert (nginx 1.29.4) | Ouvert (nginx, version masquée) |
| 5432 | **Ouvert** (PostgreSQL exposé) | Fermé (accès interne uniquement) |
| 8000 | **Ouvert** (Uvicorn exposé) | Fermé (accès via Nginx uniquement) |
| 9000/9001 | **Ouvert** (MinIO exposé) | Fermé (accès interne uniquement) |

### Scans Nikto

| Alerte | Avant | Après |
|--------|-------|-------|
| X-Frame-Options manquant | ❌ | ✅ |
| Content-Security-Policy manquant | ❌ | ✅ |
| X-Content-Type-Options manquant | ❌ | ✅ |
| Version serveur exposée | ❌ nginx/1.29.4 | ✅ masquée |
| CORS permissif (`*`) | ❌ | ✅ |

**Réduction globale du risque : ~85%**

### Script de vérification automatique

```bash
python3 check_security.py
```

```
CHECKS OBLIGATOIRES (3 Misconfigurations)
✅ PASS - M2 - Debug mode correctement désactivé
✅ PASS - M3 - Directory listing correctement désactivé

CHECKS BONUS (Améliorations supplémentaires)
✅ PASS - BONUS 1 - .gitignore
✅ PASS - BONUS 2 - Headers sécurité (5/5 présents)
✅ PASS - BONUS 3 - Server tokens masqués
✅ PASS - BONUS 4 - Ancien mot de passe rejeté

Score total : 6/7 — Pourcentage : 85.7%
```

---

## 🚀 Démarrage rapide

### Prérequis

- Docker ≥ 24.x
- Docker Compose ≥ v2.x

### Version vulnérable (démonstration Red Team)

```bash
cd "Projet Misconfig Mayhem/misconfig-mayhem"
docker-compose build
docker-compose up -d
# Application disponible sur http://localhost:80
```

### Version sécurisée (Blue Team)

```bash
cd "Projet Misconfig Mayhem/misconfig-mayhem-secure"

# 1. Copier et configurer les variables d'environnement
cp app/.env.example app/.env
# Éditer app/.env avec vos propres valeurs

# 2. Lancer
docker-compose build
docker-compose up -d

# 3. Vérifier la sécurité
python3 check_security.py
```

### Tester les vulnérabilités (version vulnérable uniquement)

```bash
# M1 — Voir les credentials en clair
cat app/.env

# M2 — Accéder à l'endpoint debug
curl http://localhost:8000/debug/info | jq

# M3 — Voir le directory listing
curl http://localhost/uploads/
```

### Valider les corrections (version sécurisée)

```bash
# M1 — L'ancien mot de passe ne fonctionne plus
curl -X POST http://localhost/login -d "username=admin&password=admin123"
# → {"detail":"Identifiants invalides"}

# M2 — Endpoint debug supprimé
curl http://localhost/debug/info
# → 404 Not Found

# M3 — Directory listing désactivé
curl http://localhost/uploads/
# → 403 Forbidden
```

---

## 🛠️ Stack technique

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green?logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)
![Nginx](https://img.shields.io/badge/Nginx-1.29-009639?logo=nginx)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)
![MinIO](https://img.shields.io/badge/MinIO-S3--compatible-C72E49?logo=minio)

**Outils de sécurité utilisés :** Nmap · Nikto · curl · Docker Exec

---

## 📚 Apprentissages clés

1. **La configuration est aussi critique que le code** — Les 3 vulnérabilités exploitées étaient des erreurs de configuration, pas des bugs logiques
2. **Defense in Depth** — La sécurité repose sur plusieurs couches complémentaires, pas sur une seule mesure
3. **Validation outillée** — Les scans Nmap/Nikto et le script automatique permettent de mesurer objectivement l'efficacité des corrections
4. **Séparation des secrets** — Les credentials ne doivent jamais être versionnés ; `.env.example` suffit pour la documentation

---

## DEMO

> version accélérée et expliquée : https://drive.google.com/file/d/1DnCVxZtxUxzv8Z2Nl-TPwiX7uwfLlcem/view?usp=sharing            

> version bien détaillée étape par étape : https://drive.google.com/file/d/1LwocpI1v_eGkhRuwchrtbljWwAjF-J5Y/view?usp=sharing

## 👩‍🎓 Auteure

**Abir Majdi**  
Étudiante en 4ième année en Développement Numérique & Cybersécurité à l'ENSA de fés
📍 Maroc · 🎯 fés

[![GitHub](https://img.shields.io/badge/GitHub-penelopeeckhar-181717?logo=github)](https://github.com/penelopeeckhar/projet-misconfig-mayhem)

---

> *"La sécurité n'est pas une fonctionnalité qu'on ajoute à la fin, c'est une discipline qui s'intègre à chaque étape du cycle de développement."*
