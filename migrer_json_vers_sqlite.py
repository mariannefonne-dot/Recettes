"""Script à lancer une seule fois pour importer les recettes du fichier
recettes.json dans la base SQLite. Une fois la migration faite, recettes.json
n'est plus utilisé par l'application.

Usage : python migrer_json_vers_sqlite.py
"""

import json
from pathlib import Path

import base_donnees

FICHIER_JSON = Path(__file__).parent / "recettes.json"


def migrer():
    base_donnees.initialiser_bd()

    if not FICHIER_JSON.exists():
        print("Aucun fichier recettes.json trouvé, rien à migrer.")
        return

    with open(FICHIER_JSON, encoding="utf-8") as f:
        recettes = json.load(f)

    # On évite de réimporter si la base contient déjà des recettes.
    if base_donnees.lister_recettes():
        print("La base contient déjà des recettes, migration ignorée.")
        return

    for recette in recettes:
        base_donnees.creer_recette({
            "titre": recette["titre"],
            "categorie": recette.get("categorie", ""),
            "ingredients": recette["ingredients"],
            "etapes": recette["etapes"],
            "temps_preparation": recette["temps_preparation"],
            "portions": recette["portions"],
            "image": recette.get("image", ""),
        })

    print(f"{len(recettes)} recette(s) importée(s) dans {base_donnees.CHEMIN_BD}.")


if __name__ == "__main__":
    migrer()
