#!/usr/bin/env python3
"""
Script de vérification de sécurité - SharePy Version Sécurisée
Vérifie que les 3 misconfigurations M1, M2, M3 sont corrigées
Auteur : Projet Misconfig Mayhem
Date : Décembre 2025
"""

import os
import requests
import re
from pathlib import Path
import sys

# ========================================
# COULEURS POUR LE TERMINAL
# ========================================
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'


# ========================================
# FONCTIONS UTILITAIRES
# ========================================

def print_header(title):
    """Affiche un titre encadré"""
    print(f"\n{'='*70}")
    print(f"  {BOLD}{title}{RESET}")
    print(f"{'='*70}")


def print_result(passed, message, details=None):
    """Affiche le résultat d'un test avec une icône"""
    if passed:
        print(f"{GREEN}✅ PASS{RESET} - {message}")
    else:
        print(f"{RED}❌ FAIL{RESET} - {message}")
    
    if details:
        print(f"  {CYAN}ℹ{RESET} {details}")
    
    return passed


def print_warning(message):
    """Affiche un avertissement"""
    print(f"  {YELLOW}⚠ WARNING{RESET} - {message}")


def print_info(message):
    """Affiche une information"""
    print(f"  {CYAN}ℹ{RESET} {message}")


# ========================================
# CHECK M1 : MOTS DE PASSE SÉCURISÉS
# ========================================

def check_m1_passwords():
    """
    M1 : Vérifier que les mots de passe sont forts
    
    Tests effectués :
    1. Aucun mot de passe faible (admin123, password123, etc.)
    2. Longueur minimale de 12 caractères
    3. Présence de caractères spéciaux
    """
    print_header("CHECK M1 : MOTS DE PASSE SÉCURISÉS")
    
    # Vérifier que le fichier .env existe
    env_file = Path("app/.env")
    
    if not env_file.exists():
        return print_result(False, "Fichier .env introuvable", "Le fichier app/.env doit exister")
    
    print_info("Lecture du fichier .env...")
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Liste des mots de passe faibles à détecter
    weak_passwords = [
        'admin123', 'password123', 'changeme', 'secret123',
        '123456', 'password', 'admin', 'root', '12345678',
        'qwerty', 'letmein', 'welcome', 'monkey', 'dragon'
    ]
    
    print_info(f"Recherche de {len(weak_passwords)} mots de passe faibles...")
    
    # Vérifier la présence de mots de passe faibles
    found_weak = []
    for weak in weak_passwords:
        if weak.lower() in content.lower():
            found_weak.append(weak)
    
    if found_weak:
        return print_result(
            False, 
            "Mots de passe faibles détectés",
            f"Trouvés : {', '.join(found_weak)}"
        )
    
    print_info("✓ Aucun mot de passe faible détecté")
    
    # Extraire et vérifier la longueur des mots de passe
    password_lines = []
    for line in content.split('\n'):
        if 'PASSWORD' in line.upper() and '=' in line and not line.strip().startswith('#'):
            password_lines.append(line)
    
    if not password_lines:
        print_warning("Aucune ligne PASSWORD trouvée dans .env")
    
    print_info(f"Vérification de {len(password_lines)} mot(s) de passe...")
    
    all_strong = True
    for line in password_lines:
        try:
            key, password = line.split('=', 1)
            password = password.strip()
            
            # Vérifier la longueur
            if len(password) < 12:
                print_warning(f"{key.strip()} : mot de passe trop court ({len(password)} caractères < 12)")
                all_strong = False
            else:
                print_info(f"✓ {key.strip()} : {len(password)} caractères")
            
            # Vérifier la présence de caractères spéciaux
            has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
            has_digit = bool(re.search(r'\d', password))
            has_upper = bool(re.search(r'[A-Z]', password))
            has_lower = bool(re.search(r'[a-z]', password))
            
            complexity = sum([has_special, has_digit, has_upper, has_lower])
            
            if complexity < 3:
                print_warning(f"{key.strip()} : complexité faible (manque majuscules/chiffres/symboles)")
                all_strong = False
            
        except Exception as e:
            print_warning(f"Erreur lors de l'analyse de : {line[:30]}...")
    
    if not all_strong:
        return print_result(
            False,
            "Certains mots de passe ne respectent pas les critères",
            "Minimum 12 caractères + majuscules + chiffres + symboles"
        )
    
    return print_result(
        True,
        "Tous les mots de passe sont forts",
        "Longueur >= 12 caractères avec complexité suffisante"
    )


# ========================================
# CHECK M2 : DEBUG MODE DÉSACTIVÉ
# ========================================

def check_m2_debug_mode():
    """
    M2 : Vérifier que le debug mode est désactivé
    
    Tests effectués :
    1. debug=False dans le code FastAPI
    2. Endpoint /debug/info supprimé du code
    3. Endpoint /debug/info inaccessible via HTTP
    4. Logs en mode INFO (pas DEBUG)
    """
    print_header("CHECK M2 : DEBUG MODE DÉSACTIVÉ")
    
    # Vérifier le fichier main.py
    main_file = Path("app/main.py")
    
    if not main_file.exists():
        return print_result(False, "Fichier main.py introuvable", "Le fichier app/main.py doit exister")
    
    print_info("Analyse du fichier main.py...")
    
    with open(main_file, 'r') as f:
        content = f.read()
    
    checks_passed = 0
    total_checks = 0
    
    # CHECK 2.1 : Vérifier debug=True
    total_checks += 1
    if re.search(r'debug\s*=\s*True', content, re.IGNORECASE):
        print_result(False, "debug=True trouvé dans le code", "Changer en debug=False")
    else:
        print_info("✓ debug=True non trouvé")
        checks_passed += 1
    
    # CHECK 2.2 : Vérifier debug=False
    total_checks += 1
    if re.search(r'debug\s*=\s*False', content, re.IGNORECASE):
        print_info("✓ debug=False explicitement défini")
        checks_passed += 1
    else:
        print_warning("debug=False non trouvé explicitement (mais pas de debug=True)")
        checks_passed += 0.5
    
    # CHECK 2.3 : Vérifier l'absence de l'endpoint /debug
    total_checks += 1
    if 'def debug_info' in content or '@app.get("/debug' in content.lower():
        print_result(False, "Endpoint /debug trouvé dans le code", "Supprimer complètement cet endpoint")
    else:
        print_info("✓ Endpoint /debug non trouvé dans le code")
        checks_passed += 1
    
    # CHECK 2.4 : Vérifier le niveau de logging
    total_checks += 1
    if re.search(r'logging\.basicConfig.*level\s*=\s*logging\.DEBUG', content):
        print_warning("Niveau de logging DEBUG trouvé (verbeux)")
    elif re.search(r'logging\.basicConfig.*level\s*=\s*logging\.INFO', content):
        print_info("✓ Niveau de logging INFO configuré")
        checks_passed += 1
    else:
        print_warning("Niveau de logging non trouvé dans le code")
    
    print_info(f"Résultat code : {checks_passed}/{total_checks} checks passés")
    
    # CHECK 2.5 : Test HTTP de l'endpoint /debug/info
    print_info("Test HTTP de l'endpoint /debug/info...")
    
    try:
        response = requests.get('http://localhost:8000/debug/info', timeout=5)
        
        if response.status_code == 200:
            return print_result(
                False,
                "Endpoint /debug/info toujours accessible via HTTP",
                f"Code HTTP : {response.status_code}"
            )
        elif response.status_code == 404:
            print_info(f"✓ Endpoint retourne 404 (supprimé)")
            checks_passed += 1
        else:
            print_info(f"✓ Endpoint retourne {response.status_code} (pas accessible)")
            checks_passed += 1
        
        total_checks += 1
        
    except requests.exceptions.ConnectionError:
        print_warning("Impossible de se connecter à http://localhost:8000 (serveur down?)")
    except requests.exceptions.RequestException as e:
        print_warning(f"Erreur lors du test HTTP : {e}")
    
    # Résultat final
    if checks_passed >= total_checks * 0.8:  # Au moins 80%
        return print_result(
            True,
            "Debug mode correctement désactivé",
            f"{checks_passed}/{total_checks} vérifications passées"
        )
    else:
        return print_result(
            False,
            "Debug mode partiellement désactivé",
            f"Seulement {checks_passed}/{total_checks} vérifications passées"
        )


# ========================================
# CHECK M3 : DIRECTORY LISTING DÉSACTIVÉ
# ========================================

def check_m3_directory_listing():
    """
    M3 : Vérifier que le directory listing est désactivé
    
    Tests effectués :
    1. autoindex off dans nginx.conf
    2. deny all dans la section /uploads
    3. Test HTTP : accès à /uploads/ retourne 403
    """
    print_header("CHECK M3 : DIRECTORY LISTING DÉSACTIVÉ")
    
    # Vérifier le fichier nginx.conf
    nginx_file = Path("nginx/nginx.conf")
    
    if not nginx_file.exists():
        return print_result(False, "Fichier nginx.conf introuvable", "Le fichier nginx/nginx.conf doit exister")
    
    print_info("Analyse du fichier nginx.conf...")
    
    with open(nginx_file, 'r') as f:
        content = f.read()
    
    checks_passed = 0
    total_checks = 0
    
    # CHECK 3.1 : Vérifier autoindex off
    total_checks += 1
    if re.search(r'autoindex\s+on', content, re.IGNORECASE):
        print_result(False, "autoindex on trouvé dans nginx.conf", "Changer en autoindex off")
    elif re.search(r'autoindex\s+off', content, re.IGNORECASE):
        print_info("✓ autoindex off trouvé")
        checks_passed += 1
    else:
        print_warning("autoindex non trouvé (par défaut = off)")
        checks_passed += 0.5
    
    # CHECK 3.2 : Vérifier deny all dans /uploads
    total_checks += 1
    uploads_section = re.search(r'location\s+/uploads\s*\{([^}]+)\}', content, re.DOTALL)
    
    if uploads_section:
        uploads_config = uploads_section.group(1)
        
        if 'deny all' in uploads_config:
            print_info("✓ 'deny all' trouvé dans location /uploads")
            checks_passed += 1
        else:
            print_warning("'deny all' non trouvé dans location /uploads (accès non restreint)")
    else:
        print_warning("Section location /uploads non trouvée dans nginx.conf")
    
    print_info(f"Résultat configuration : {checks_passed}/{total_checks} checks passés")
    
    # CHECK 3.3 : Test HTTP du directory listing
    print_info("Test HTTP de /uploads/...")
    
    try:
        response = requests.get('http://localhost/uploads/', timeout=5)
        
        # Vérifier le code de statut
        if response.status_code == 403:
            print_info(f"✓ Code HTTP 403 Forbidden (accès refusé)")
            checks_passed += 1
        elif response.status_code == 200:
            # Vérifier le contenu
            if 'Index of' in response.text or '<a href=' in response.text:
                return print_result(
                    False,
                    "Directory listing toujours actif",
                    "Liste des fichiers visible sur http://localhost/uploads/"
                )
            else:
                print_info("✓ Code 200 mais pas de liste de fichiers")
                checks_passed += 0.5
        else:
            print_info(f"✓ Code HTTP {response.status_code} (pas de directory listing)")
            checks_passed += 1
        
        total_checks += 1
        
    except requests.exceptions.ConnectionError:
        print_warning("Impossible de se connecter à http://localhost (nginx down?)")
    except requests.exceptions.RequestException as e:
        print_warning(f"Erreur lors du test HTTP : {e}")
    
    # Résultat final
    if checks_passed >= total_checks * 0.8:
        return print_result(
            True,
            "Directory listing correctement désactivé",
            f"{checks_passed}/{total_checks} vérifications passées"
        )
    else:
        return print_result(
            False,
            "Directory listing partiellement désactivé",
            f"Seulement {checks_passed}/{total_checks} vérifications passées"
        )


# ========================================
# CHECK BONUS 1 : .GITIGNORE
# ========================================

def check_gitignore():
    """
    BONUS : Vérifier que .gitignore protège les fichiers sensibles
    """
    print_header("CHECK BONUS 1 : .GITIGNORE")
    
    gitignore_file = Path(".gitignore")
    
    if not gitignore_file.exists():
        return print_result(False, "Fichier .gitignore introuvable", "Créer un .gitignore pour protéger les secrets")
    
    with open(gitignore_file, 'r') as f:
        content = f.read()
    
    # Éléments à vérifier
    checks = {
        '.env': ('.env' in content or '*.env' in content),
        'uploads/': ('uploads/' in content or 'uploads/*' in content),
        '__pycache__': '__pycache__' in content,
        '*.log': ('*.log' in content or 'logs/' in content),
        '*.pyc': '*.pyc' in content or '*.py[cod]' in content
    }
    
    print_info("Vérification des entrées dans .gitignore :")
    
    for item, found in checks.items():
        symbol = f"{GREEN}✅{RESET}" if found else f"{RED}❌{RESET}"
        print(f"  {symbol} {item}")
    
    passed_count = sum(checks.values())
    total_count = len(checks)
    
    if passed_count == total_count:
        return print_result(True, "Tous les fichiers sensibles sont protégés", f"{passed_count}/{total_count}")
    elif passed_count >= 3:
        return print_result(True, "Protection partielle des fichiers sensibles", f"{passed_count}/{total_count}")
    else:
        return print_result(False, "Fichiers sensibles non protégés", f"Seulement {passed_count}/{total_count}")


# ========================================
# CHECK BONUS 2 : HEADERS DE SÉCURITÉ
# ========================================

def check_security_headers():
    """
    BONUS : Vérifier les headers de sécurité HTTP
    """
    print_header("CHECK BONUS 2 : HEADERS DE SÉCURITÉ HTTP")
    
    try:
        response = requests.get('http://localhost/', timeout=5)
        headers = response.headers
        
        # Headers de sécurité recommandés
        security_headers = {
            'X-Frame-Options': 'X-Frame-Options' in headers,
            'X-Content-Type-Options': 'X-Content-Type-Options' in headers,
            'X-XSS-Protection': 'X-XSS-Protection' in headers,
            'Referrer-Policy': 'Referrer-Policy' in headers,
            'Content-Security-Policy': 'Content-Security-Policy' in headers,
        }
        
        print_info("Vérification des headers HTTP :")
        
        for header, present in security_headers.items():
            if present:
                value = headers.get(header, '')
                print(f"  {GREEN}✅{RESET} {header}: {value}")
            else:
                print(f"  {YELLOW}⚠{RESET} {header}: absent")
        
        found_count = sum(security_headers.values())
        total_count = len(security_headers)
        
        if found_count >= 4:
            return print_result(True, f"{found_count}/{total_count} headers de sécurité présents", "Excellente protection")
        elif found_count >= 2:
            return print_result(True, f"{found_count}/{total_count} headers de sécurité présents", "Protection minimale")
        else:
            return print_result(False, f"Seulement {found_count}/{total_count} headers présents", "Ajouter plus de headers")
        
    except requests.exceptions.RequestException as e:
        return print_result(False, "Impossible de tester les headers", str(e))


# ========================================
# CHECK BONUS 3 : SERVER TOKENS
# ========================================

def check_server_tokens():
    """
    BONUS : Vérifier que les versions de serveur sont masquées
    """
    print_header("CHECK BONUS 3 : MASQUAGE DE VERSION SERVEUR")
    
    try:
        response = requests.get('http://localhost/', timeout=5)
        server_header = response.headers.get('Server', '')
        
        print_info(f"Header Server: '{server_header}'")
        
        # Vérifier si une version est exposée
        if re.search(r'nginx/\d+\.\d+', server_header, re.IGNORECASE):
            return print_result(False, "Version Nginx exposée", f"Trouvée : {server_header}")
        elif re.search(r'uvicorn/\d+\.\d+', server_header, re.IGNORECASE):
            return print_result(False, "Version Uvicorn exposée", f"Trouvée : {server_header}")
        elif server_header == 'nginx' or server_header == '':
            return print_result(True, "Version serveur masquée", "server_tokens off activé")
        else:
            return print_result(True, "Header Server personnalisé", f"Valeur : {server_header}")
        
    except requests.exceptions.RequestException as e:
        return print_result(False, "Impossible de tester", str(e))


# ========================================
# CHECK BONUS 4 : ANCIEN MOT DE PASSE
# ========================================

def check_old_password():
    """
    BONUS : Vérifier que l'ancien mot de passe vulnérable ne fonctionne plus
    """
    print_header("CHECK BONUS 4 : ANCIEN MOT DE PASSE INVALIDE")
    
    print_info("Test de connexion avec l'ancien mot de passe 'admin123'...")
    
    try:
        response = requests.post(
            'http://localhost:8000/login',
            data={'username': 'admin', 'password': 'admin123'},
            timeout=5
        )
        
        print_info(f"Code HTTP : {response.status_code}")
        
        if response.status_code == 200:
            return print_result(
                False,
                "L'ancien mot de passe 'admin123' fonctionne encore !",
                "CRITIQUE : Changer le mot de passe immédiatement"
            )
        elif response.status_code == 401:
            return print_result(True, "Ancien mot de passe rejeté", "Authentification échouée (401)")
        else:
            return print_result(True, "Ancien mot de passe rejeté", f"Code : {response.status_code}")
        
    except requests.exceptions.RequestException as e:
        return print_result(False, "Impossible de tester", str(e))


# ========================================
# FONCTION PRINCIPALE
# ========================================

def main():
    """
    Fonction principale : exécute tous les checks
    """
    # Bannière
    print("\n")
    print(f"{BLUE}╔══════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BLUE}║     VÉRIFICATION DE SÉCURITÉ - SharePy Version Sécurisée        ║{RESET}")
    print(f"{BLUE}║              Misconfig Mayhem - Script Automatique              ║{RESET}")
    print(f"{BLUE}╚══════════════════════════════════════════════════════════════════╝{RESET}")
    
    # Dictionnaire des résultats
    results = {}
    
    # ========== CHECKS OBLIGATOIRES ==========
    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}  CHECKS OBLIGATOIRES (3 Misconfigurations){RESET}")
    print(f"{BOLD}{'='*70}{RESET}")
    
    results['M1 - Mots de passe forts'] = check_m1_passwords()
    results['M2 - Debug désactivé'] = check_m2_debug_mode()
    results['M3 - Directory listing off'] = check_m3_directory_listing()
    
    # ========== CHECKS BONUS ==========
    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}  CHECKS BONUS (Améliorations supplémentaires){RESET}")
    print(f"{BOLD}{'='*70}{RESET}")
    
    results['BONUS 1 - .gitignore'] = check_gitignore()
    results['BONUS 2 - Headers sécurité'] = check_security_headers()
    results['BONUS 3 - Server tokens'] = check_server_tokens()
    results['BONUS 4 - Ancien mot de passe'] = check_old_password()
    
    # ========== RÉSUMÉ FINAL ==========
    print_header("RÉSUMÉ FINAL")
    
    # Séparer obligatoires et bonus
    mandatory_results = {k: v for k, v in list(results.items())[:3]}
    bonus_results = {k: v for k, v in list(results.items())[3:]}
    
    # Afficher les résultats
    print(f"\n{BOLD}Checks obligatoires :{RESET}")
    for check, result in mandatory_results.items():
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"  {status} - {check}")
    
    print(f"\n{BOLD}Checks bonus :{RESET}")
    for check, result in bonus_results.items():
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{YELLOW}⚠ FAIL{RESET}"
        print(f"  {status} - {check}")
    
    # Calcul du score
    mandatory_passed = sum(mandatory_results.values())
    mandatory_total = len(mandatory_results)
    bonus_passed = sum(bonus_results.values())
    bonus_total = len(bonus_results)
    total_passed = mandatory_passed + bonus_passed
    total_checks = mandatory_total + bonus_total
    
    print(f"\n{'='*70}")
    print(f"{BOLD}Score obligatoire : {mandatory_passed}/{mandatory_total}{RESET}")
    print(f"{BOLD}Score bonus : {bonus_passed}/{bonus_total}{RESET}")
    print(f"{BOLD}Score total : {total_passed}/{total_checks}{RESET}")
    
    percentage = (total_passed / total_checks) * 100
    print(f"{BOLD}Pourcentage : {percentage:.1f}%{RESET}")
    
    # Message final
    print(f"\n{'='*70}")
    
    if mandatory_passed == mandatory_total:
        if total_passed == total_checks:
            print(f"{GREEN}{BOLD}🎉 PARFAIT ! Application entièrement sécurisée !{RESET}")
            print(f"{GREEN}Toutes les vulnérabilités sont corrigées + améliorations bonus{RESET}")
            exit_code = 0
        else:
            print(f"{GREEN}{BOLD}✅ EXCELLENT ! Toutes les vulnérabilités critiques sont corrigées{RESET}")
            print(f"{YELLOW}Quelques améliorations bonus possibles{RESET}")
            exit_code = 0
    elif mandatory_passed >= 2:
        print(f"{YELLOW}{BOLD}⚠ BIEN ! Mais des vulnérabilités subsistent{RESET}")
        print(f"{YELLOW}Corriger les checks obligatoires restants{RESET}")
        exit_code = 1
    else:
        print(f"{RED}{BOLD}❌ ATTENTION ! Des vulnérabilités critiques subsistent{RESET}")
        print(f"{RED}Corriger immédiatement les misconfigurations M1, M2, M3{RESET}")
        exit_code = 2
    
    print(f"{'='*70}\n")
    
    return exit_code


# ========================================
# POINT D'ENTRÉE
# ========================================

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Script interrompu par l'utilisateur{RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{RED}Erreur inattendue : {e}{RESET}")
        sys.exit(1)
