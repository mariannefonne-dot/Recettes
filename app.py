"""API REST de l'application Recettes.

Le backend ne renvoie plus de pages HTML : il expose des routes /api/...
qui renvoient du JSON. C'est le front React qui affiche les pages en
consommant cette API. Les images téléversées sont servies depuis static/images.
"""

import uuid
from pathlib import Path

from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from werkzeug.utils import secure_filename

import base_donnees

app = Flask(__name__)
# Autorise le front React (servi sur un autre port) à appeler l'API.
CORS(app, origins="*")

DOSSIER_IMAGES = Path(__file__).parent / "static" / "images"
EXTENSIONS_AUTORISEES = {"png", "jpg", "jpeg", "gif", "webp"}

base_donnees.initialiser_bd()


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
def lister():
    recherche = request.args.get("recherche", "")
    categorie = request.args.get("categorie", "")
    return jsonify(base_donnees.lister_recettes(recherche, categorie))


@app.get("/api/categories")
def categories():
    return jsonify(base_donnees.lister_categories())


@app.get("/api/recettes/<int:id_recette>")
def detail(id_recette):
    recette = base_donnees.obtenir_recette(id_recette)
    if recette is None:
        abort(404, description="Recette introuvable.")
    return jsonify(recette)


@app.post("/api/recettes")
def creer():
    donnees = _lire_donnees_recette(request.get_json(silent=True) or {})
    return jsonify(base_donnees.creer_recette(donnees)), 201


@app.put("/api/recettes/<int:id_recette>")
def modifier(id_recette):
    donnees = _lire_donnees_recette(request.get_json(silent=True) or {})
    recette = base_donnees.modifier_recette(id_recette, donnees)
    if recette is None:
        abort(404, description="Recette introuvable.")
    return jsonify(recette)


@app.post("/api/recettes/<int:id_recette>/selection")
def basculer_selection(id_recette):
    recette = base_donnees.basculer_selection(id_recette)
    if recette is None:
        abort(404, description="Recette introuvable.")
    return jsonify(recette)


@app.post("/api/recettes/<int:id_recette>/favori")
def basculer_favori(id_recette):
    recette = base_donnees.basculer_favori(id_recette)
    if recette is None:
        abort(404, description="Recette introuvable.")
    return jsonify(recette)


@app.delete("/api/recettes/<int:id_recette>")
def supprimer(id_recette):
    if not base_donnees.supprimer_recette(id_recette):
        abort(404, description="Recette introuvable.")
    return "", 204


@app.get("/api/calendrier")
def lister_calendrier():
    debut = request.args.get("debut", "")
    fin = request.args.get("fin", "")
    if not debut or not fin:
        abort(400, description="Paramètres 'debut' et 'fin' requis (format YYYY-MM-DD).")
    return jsonify(base_donnees.lister_calendrier(debut, fin))


@app.post("/api/calendrier")
def ajouter_calendrier():
    corps = request.get_json(silent=True) or {}
    try:
        date = corps["date"]
        recette_id = int(corps["recette_id"])
        moment = corps.get("moment", "diner")
    except (KeyError, TypeError, ValueError):
        abort(400, description="Champs requis : date, recette_id.")
    id_entree = base_donnees.ajouter_au_calendrier(date, recette_id, moment)
    return jsonify({"id": id_entree}), 201


@app.delete("/api/calendrier/<int:id_entree>")
def supprimer_calendrier(id_entree):
    if not base_donnees.supprimer_du_calendrier(id_entree):
        abort(404, description="Entrée introuvable.")
    return "", 204


@app.post("/api/televerser-image")
def televerser_image():
    if "image" not in request.files:
        abort(400, description="Aucun fichier image fourni.")
    fichier = request.files["image"]
    if fichier.filename == "":
        abort(400, description="Aucun fichier sélectionné.")
    if not _extension_autorisee(fichier.filename):
        abort(400, description="Format d'image non autorisé.")

    # Un préfixe unique évite que deux images du même nom s'écrasent.
    nom_securise = secure_filename(fichier.filename)
    nom_final = f"{uuid.uuid4().hex}_{nom_securise}"
    DOSSIER_IMAGES.mkdir(parents=True, exist_ok=True)
    fichier.save(DOSSIER_IMAGES / nom_final)

    return jsonify({"image": nom_final}), 201


@app.errorhandler(400)
@app.errorhandler(404)
def gerer_erreur(erreur):
    return jsonify({"erreur": erreur.description}), erreur.code


if __name__ == "__main__":
    app.run(debug=True)
