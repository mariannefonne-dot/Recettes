"""API REST de l'application Recettes.

Le backend expose des routes /api/... qui renvoient du JSON.
Toutes les routes (sauf /api/auth/*) nécessitent un token JWT valide.
"""

import os
import uuid
from datetime import datetime, timezone, timedelta
from functools import wraps
from pathlib import Path

import jwt
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import base_donnees

app = Flask(__name__)
CORS(app, origins="*")

DOSSIER_IMAGES = Path(__file__).parent / "static" / "images"
EXTENSIONS_AUTORISEES = {"png", "jpg", "jpeg", "gif", "webp"}

# Clé secrète pour signer les tokens JWT. En production, définir SECRET_KEY dans les variables d'environnement.
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-non-securise")

base_donnees.initialiser_bd()


# ── Authentification ──────────────────────────────────────────────────────────

def _generer_token(utilisateur_id):
    """Crée un token JWT valable 30 jours."""
    payload = {
        "utilisateur_id": utilisateur_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=30),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def auth_requise(f):
    """Décorateur qui vérifie le token JWT avant d'exécuter la route."""
    @wraps(f)
    def decorateur(*args, **kwargs):
        entete = request.headers.get("Authorization", "")
        token = entete.removeprefix("Bearer ").strip()
        if not token:
            abort(401, description="Authentification requise.")
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            utilisateur = base_donnees.obtenir_utilisateur(payload["utilisateur_id"])
            if not utilisateur:
                abort(401, description="Utilisateur introuvable.")
            # On attache l'utilisateur à la requête pour y accéder dans la route.
            request.utilisateur_id = utilisateur["id"]
            request.utilisateur = utilisateur
        except jwt.ExpiredSignatureError:
            abort(401, description="Session expirée, veuillez vous reconnecter.")
        except jwt.InvalidTokenError:
            abort(401, description="Token invalide.")
        return f(*args, **kwargs)
    return decorateur


def admin_requis(f):
    """Décorateur qui vérifie que l'utilisateur est administrateur."""
    @wraps(f)
    @auth_requise
    def decorateur(*args, **kwargs):
        if not request.utilisateur.get("est_admin"):
            abort(403, description="Action réservée à l'administrateur.")
        return f(*args, **kwargs)
    return decorateur


# ── Routes d'authentification (publiques) ────────────────────────────────────

@app.post("/api/auth/setup")
def setup():
    """Crée le premier compte administrateur. Ne fonctionne que si aucun utilisateur n'existe."""
    if base_donnees.compter_utilisateurs() > 0:
        abort(403, description="Un compte administrateur existe déjà.")
    corps = request.get_json(silent=True) or {}
    email = corps.get("email", "").strip().lower()
    mot_de_passe = corps.get("mot_de_passe", "")
    nom = corps.get("nom", "").strip()
    if not email or not mot_de_passe or not nom:
        abort(400, description="Email, mot de passe et prénom requis.")
    hash_mdp = generate_password_hash(mot_de_passe)
    utilisateur = base_donnees.creer_utilisateur(email, hash_mdp, nom, est_admin=True)
    token = _generer_token(utilisateur["id"])
    return jsonify({"token": token, "utilisateur": utilisateur}), 201


@app.post("/api/auth/connexion")
def connexion():
    """Authentifie un utilisateur et retourne un token JWT."""
    corps = request.get_json(silent=True) or {}
    email = corps.get("email", "").strip().lower()
    mot_de_passe = corps.get("mot_de_passe", "")
    if not email or not mot_de_passe:
        abort(400, description="Email et mot de passe requis.")
    utilisateur_complet = base_donnees.obtenir_utilisateur_par_email(email)
    if not utilisateur_complet or not check_password_hash(utilisateur_complet["mot_de_passe_hash"], mot_de_passe):
        abort(401, description="Email ou mot de passe incorrect.")
    utilisateur = base_donnees.obtenir_utilisateur(utilisateur_complet["id"])
    token = _generer_token(utilisateur["id"])
    return jsonify({"token": token, "utilisateur": utilisateur})


@app.post("/api/auth/inscription")
def inscription():
    """Crée un compte à partir d'un token d'invitation valide."""
    corps = request.get_json(silent=True) or {}
    token_invitation = corps.get("token", "").strip()
    nom = corps.get("nom", "").strip()
    mot_de_passe = corps.get("mot_de_passe", "")
    email = corps.get("email", "").strip().lower()
    if not token_invitation or not nom or not mot_de_passe or not email:
        abort(400, description="Token, email, prénom et mot de passe requis.")
    if len(mot_de_passe) < 6:
        abort(400, description="Le mot de passe doit contenir au moins 6 caractères.")
    if not base_donnees.invitation_valide(token_invitation):
        abort(400, description="Lien d'invitation invalide ou déjà utilisé.")
    if base_donnees.obtenir_utilisateur_par_email(email):
        abort(400, description="Un compte existe déjà avec cet email.")
    hash_mdp = generate_password_hash(mot_de_passe)
    utilisateur = base_donnees.creer_utilisateur(email, hash_mdp, nom)
    base_donnees.consommer_invitation(token_invitation)
    token = _generer_token(utilisateur["id"])
    return jsonify({"token": token, "utilisateur": utilisateur}), 201


@app.get("/api/auth/moi")
@auth_requise
def moi():
    """Retourne les informations de l'utilisateur connecté."""
    return jsonify(request.utilisateur)


@app.post("/api/auth/inviter")
@admin_requis
def inviter():
    """Génère un token d'invitation (admin uniquement)."""
    token_invitation = base_donnees.creer_invitation(request.utilisateur_id)
    return jsonify({"token": token_invitation}), 201


# ── Recettes ──────────────────────────────────────────────────────────────────

def _extension_autorisee(nom_fichier):
    return "." in nom_fichier and \
        nom_fichier.rsplit(".", 1)[1].lower() in EXTENSIONS_AUTORISEES


def _lire_donnees_recette(corps):
    """Extrait et valide les champs d'une recette depuis le JSON reçu."""
    try:
        return {
            "titre": corps["titre"].strip(),
            "categorie": corps.get("categorie", "").strip(),
            "ingredients": [i.strip() for i in corps["ingredients"] if i.strip()],
            "etapes": [e.strip() for e in corps["etapes"] if e.strip()],
            "temps_preparation": int(corps["temps_preparation"]),
            "portions": int(corps["portions"]),
            "image": corps.get("image", "").strip(),
        }
    except (KeyError, TypeError, ValueError):
        abort(400, description="Données de recette invalides ou incomplètes.")


@app.get("/api/recettes")
@auth_requise
def lister():
    recherche = request.args.get("recherche", "")
    categorie = request.args.get("categorie", "")
    return jsonify(base_donnees.lister_recettes(recherche, categorie, request.utilisateur_id))


@app.get("/api/categories")
@auth_requise
def categories():
    return jsonify(base_donnees.lister_categories())


@app.get("/api/recettes/<int:id_recette>")
@auth_requise
def detail(id_recette):
    recette = base_donnees.obtenir_recette(id_recette, request.utilisateur_id)
    if recette is None:
        abort(404, description="Recette introuvable.")
    return jsonify(recette)


@app.post("/api/recettes")
@auth_requise
def creer():
    donnees = _lire_donnees_recette(request.get_json(silent=True) or {})
    return jsonify(base_donnees.creer_recette(donnees)), 201


@app.put("/api/recettes/<int:id_recette>")
@auth_requise
def modifier(id_recette):
    donnees = _lire_donnees_recette(request.get_json(silent=True) or {})
    recette = base_donnees.modifier_recette(id_recette, donnees)
    if recette is None:
        abort(404, description="Recette introuvable.")
    return jsonify(recette)


@app.post("/api/recettes/<int:id_recette>/selection")
@auth_requise
def basculer_selection(id_recette):
    recette = base_donnees.basculer_selection(id_recette, request.utilisateur_id)
    if recette is None:
        abort(404, description="Recette introuvable.")
    return jsonify(recette)


@app.post("/api/recettes/<int:id_recette>/favori")
@auth_requise
def basculer_favori(id_recette):
    recette = base_donnees.basculer_favori(id_recette, request.utilisateur_id)
    if recette is None:
        abort(404, description="Recette introuvable.")
    return jsonify(recette)


@app.delete("/api/recettes/<int:id_recette>")
@auth_requise
def supprimer(id_recette):
    if not base_donnees.supprimer_recette(id_recette):
        abort(404, description="Recette introuvable.")
    return "", 204


# ── Calendrier ────────────────────────────────────────────────────────────────

@app.get("/api/calendrier")
@auth_requise
def lister_calendrier():
    debut = request.args.get("debut", "")
    fin = request.args.get("fin", "")
    if not debut or not fin:
        abort(400, description="Paramètres 'debut' et 'fin' requis (format YYYY-MM-DD).")
    return jsonify(base_donnees.lister_calendrier(debut, fin, request.utilisateur_id))


@app.post("/api/calendrier")
@auth_requise
def ajouter_calendrier():
    corps = request.get_json(silent=True) or {}
    try:
        date = corps["date"]
        recette_id = int(corps["recette_id"])
        moment = corps.get("moment", "diner")
    except (KeyError, TypeError, ValueError):
        abort(400, description="Champs requis : date, recette_id.")
    id_entree = base_donnees.ajouter_au_calendrier(date, recette_id, moment, request.utilisateur_id)
    return jsonify({"id": id_entree}), 201


@app.delete("/api/calendrier/<int:id_entree>")
@auth_requise
def supprimer_calendrier(id_entree):
    if not base_donnees.supprimer_du_calendrier(id_entree):
        abort(404, description="Entrée introuvable.")
    return "", 204


# ── Images ────────────────────────────────────────────────────────────────────

@app.post("/api/televerser-image")
@auth_requise
def televerser_image():
    if "image" not in request.files:
        abort(400, description="Aucun fichier image fourni.")
    fichier = request.files["image"]
    if fichier.filename == "":
        abort(400, description="Aucun fichier sélectionné.")
    if not _extension_autorisee(fichier.filename):
        abort(400, description="Format d'image non autorisé.")
    nom_securise = secure_filename(fichier.filename)
    nom_final = f"{uuid.uuid4().hex}_{nom_securise}"
    DOSSIER_IMAGES.mkdir(parents=True, exist_ok=True)
    fichier.save(DOSSIER_IMAGES / nom_final)
    return jsonify({"image": nom_final}), 201


# ── Gestion des erreurs ───────────────────────────────────────────────────────

@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(403)
@app.errorhandler(404)
def gerer_erreur(erreur):
    return jsonify({"erreur": erreur.description}), erreur.code


if __name__ == "__main__":
    app.run(debug=True)
