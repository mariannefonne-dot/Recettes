"""Couche d'accès aux données : tout passe par SQLite.

Les ingrédients et les étapes sont des listes. SQLite ne sait pas stocker
une liste directement, on les enregistre donc en JSON dans une colonne texte
et on les reconvertit en liste à la lecture. C'est volontairement simple :
pas de tables séparées pour les ingrédients, ce qui suffit largement ici.
"""

import json
import os
import sqlite3

CHEMIN_BD = os.environ.get("CHEMIN_BD", "recettes.db")


def obtenir_connexion():
    connexion = sqlite3.connect(CHEMIN_BD)
    # Accès aux colonnes par leur nom (ex : ligne["titre"]) plutôt que par index.
    connexion.row_factory = sqlite3.Row
    return connexion


def initialiser_bd():
    with obtenir_connexion() as connexion:
        connexion.execute("""
            CREATE TABLE IF NOT EXISTS recettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titre TEXT NOT NULL,
                categorie TEXT DEFAULT '',
                ingredients TEXT NOT NULL,
                etapes TEXT NOT NULL,
                temps_preparation INTEGER NOT NULL,
                portions INTEGER NOT NULL,
                image TEXT DEFAULT '',
                favori INTEGER DEFAULT 0
            )
        """)
        # Ajoute les colonnes si la table existait déjà sans elles.
        for colonne in ["favori INTEGER DEFAULT 0", "selectionne INTEGER DEFAULT 0"]:
            try:
                connexion.execute(f"ALTER TABLE recettes ADD COLUMN {colonne}")
            except Exception:
                pass
        connexion.commit()
        connexion.execute("""
            CREATE TABLE IF NOT EXISTS calendrier (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                recette_id INTEGER NOT NULL,
                moment TEXT DEFAULT 'diner',
                FOREIGN KEY (recette_id) REFERENCES recettes(id)
            )
        """)
        connexion.commit()


def _ligne_vers_recette(ligne):
    """Transforme une ligne SQLite en dictionnaire prêt à être envoyé en JSON."""
    return {
        "id": ligne["id"],
        "titre": ligne["titre"],
        "categorie": ligne["categorie"] or "",
        "ingredients": json.loads(ligne["ingredients"]),
        "etapes": json.loads(ligne["etapes"]),
        "temps_preparation": ligne["temps_preparation"],
        "portions": ligne["portions"],
        "image": ligne["image"] or "",
        "favori": bool(ligne["favori"]),
        "selectionne": bool(ligne["selectionne"]),
    }


def lister_recettes(recherche="", categorie=""):
    recherche = recherche.strip().lower()
    categorie = categorie.strip()

    with obtenir_connexion() as connexion:
        lignes = connexion.execute("SELECT * FROM recettes ORDER BY id DESC").fetchall()

    recettes = [_ligne_vers_recette(ligne) for ligne in lignes]

    # On filtre en Python plutôt qu'en SQL : la recherche doit aussi regarder
    # à l'intérieur de la liste d'ingrédients, ce qui est plus lisible ici.
    if recherche:
        recettes = [
            r for r in recettes
            if recherche in r["titre"].lower()
            or any(recherche in ing.lower() for ing in r["ingredients"])
        ]
    if categorie:
        recettes = [r for r in recettes if r["categorie"] == categorie]

    return recettes


def obtenir_recette(id_recette):
    with obtenir_connexion() as connexion:
        ligne = connexion.execute(
            "SELECT * FROM recettes WHERE id = ?", (id_recette,)
        ).fetchone()
    return _ligne_vers_recette(ligne) if ligne else None


def creer_recette(donnees):
    with obtenir_connexion() as connexion:
        curseur = connexion.execute(
            """
            INSERT INTO recettes
                (titre, categorie, ingredients, etapes, temps_preparation, portions, image)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                donnees["titre"],
                donnees.get("categorie", ""),
                json.dumps(donnees["ingredients"], ensure_ascii=False),
                json.dumps(donnees["etapes"], ensure_ascii=False),
                donnees["temps_preparation"],
                donnees["portions"],
                donnees.get("image", ""),
            ),
        )
        connexion.commit()
        return obtenir_recette(curseur.lastrowid)


def modifier_recette(id_recette, donnees):
    if obtenir_recette(id_recette) is None:
        return None
    with obtenir_connexion() as connexion:
        connexion.execute(
            """
            UPDATE recettes SET
                titre = ?, categorie = ?, ingredients = ?, etapes = ?,
                temps_preparation = ?, portions = ?, image = ?
            WHERE id = ?
            """,
            (
                donnees["titre"],
                donnees.get("categorie", ""),
                json.dumps(donnees["ingredients"], ensure_ascii=False),
                json.dumps(donnees["etapes"], ensure_ascii=False),
                donnees["temps_preparation"],
                donnees["portions"],
                donnees.get("image", ""),
                id_recette,
            ),
        )
        connexion.commit()
    return obtenir_recette(id_recette)


def basculer_selection(id_recette):
    """Ajoute ou retire la recette de la sélection personnelle."""
    recette = obtenir_recette(id_recette)
    if recette is None:
        return None
    nouveau = 0 if recette["selectionne"] else 1
    with obtenir_connexion() as connexion:
        connexion.execute(
            "UPDATE recettes SET selectionne = ? WHERE id = ?", (nouveau, id_recette)
        )
        connexion.commit()
    return obtenir_recette(id_recette)


def basculer_favori(id_recette):
    """Passe la recette en favori si elle ne l'est pas, et inversement."""
    recette = obtenir_recette(id_recette)
    if recette is None:
        return None
    nouveau = 0 if recette["favori"] else 1
    with obtenir_connexion() as connexion:
        connexion.execute(
            "UPDATE recettes SET favori = ? WHERE id = ?", (nouveau, id_recette)
        )
        connexion.commit()
    return obtenir_recette(id_recette)


def supprimer_recette(id_recette):
    with obtenir_connexion() as connexion:
        curseur = connexion.execute(
            "DELETE FROM recettes WHERE id = ?", (id_recette,)
        )
        connexion.commit()
        return curseur.rowcount > 0


def lister_calendrier(debut, fin):
    """Retourne toutes les entrées du calendrier entre deux dates (incluses)."""
    with obtenir_connexion() as connexion:
        lignes = connexion.execute(
            """
            SELECT c.id, c.date, c.moment,
                   r.id as recette_id, r.titre, r.image, r.temps_preparation, r.portions
            FROM calendrier c
            JOIN recettes r ON c.recette_id = r.id
            WHERE c.date BETWEEN ? AND ?
            ORDER BY c.date, c.moment
            """,
            (debut, fin),
        ).fetchall()
    return [
        {
            "id": l["id"],
            "date": l["date"],
            "moment": l["moment"],
            "recette": {
                "id": l["recette_id"],
                "titre": l["titre"],
                "image": l["image"] or "",
                "temps_preparation": l["temps_preparation"],
                "portions": l["portions"],
            },
        }
        for l in lignes
    ]


def ajouter_au_calendrier(date, recette_id, moment):
    with obtenir_connexion() as connexion:
        curseur = connexion.execute(
            "INSERT INTO calendrier (date, recette_id, moment) VALUES (?, ?, ?)",
            (date, recette_id, moment),
        )
        connexion.commit()
        return curseur.lastrowid


def supprimer_du_calendrier(id_entree):
    with obtenir_connexion() as connexion:
        curseur = connexion.execute("DELETE FROM calendrier WHERE id = ?", (id_entree,))
        connexion.commit()
        return curseur.rowcount > 0


def lister_categories():
    with obtenir_connexion() as connexion:
        lignes = connexion.execute(
            "SELECT DISTINCT categorie FROM recettes WHERE categorie != '' ORDER BY categorie"
        ).fetchall()
    return [ligne["categorie"] for ligne in lignes]
