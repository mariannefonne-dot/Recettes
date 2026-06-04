"""Couche d'accès aux données.

En développement local : SQLite (aucune configuration nécessaire).
En production sur Render : PostgreSQL, détecté via la variable DATABASE_URL.
"""

import json
import os
import sqlite3

# Render injecte automatiquement DATABASE_URL quand une base PostgreSQL est liée.
DATABASE_URL = os.environ.get("DATABASE_URL")
USE_POSTGRES = bool(DATABASE_URL)
CHEMIN_BD = os.environ.get("CHEMIN_BD", "recettes.db")

# Placeholder SQL : ? pour SQLite, %s pour PostgreSQL.
PH = "%s" if USE_POSTGRES else "?"

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras


def obtenir_connexion():
    if USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    conn = sqlite3.connect(CHEMIN_BD)
    conn.row_factory = sqlite3.Row
    return conn


def _exec(conn, sql, params=()):
    cur = conn.cursor()
    cur.execute(sql, params)
    return cur


def initialiser_bd():
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS recettes (
                    id SERIAL PRIMARY KEY,
                    titre TEXT NOT NULL,
                    categorie TEXT DEFAULT '',
                    ingredients TEXT NOT NULL,
                    etapes TEXT NOT NULL,
                    temps_preparation INTEGER NOT NULL,
                    portions INTEGER NOT NULL,
                    image TEXT DEFAULT '',
                    favori BOOLEAN DEFAULT FALSE,
                    selectionne BOOLEAN DEFAULT FALSE
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS calendrier (
                    id SERIAL PRIMARY KEY,
                    date TEXT NOT NULL,
                    recette_id INTEGER NOT NULL REFERENCES recettes(id),
                    moment TEXT DEFAULT 'diner'
                )
            """)
        else:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS recettes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titre TEXT NOT NULL,
                    categorie TEXT DEFAULT '',
                    ingredients TEXT NOT NULL,
                    etapes TEXT NOT NULL,
                    temps_preparation INTEGER NOT NULL,
                    portions INTEGER NOT NULL,
                    image TEXT DEFAULT '',
                    favori INTEGER DEFAULT 0,
                    selectionne INTEGER DEFAULT 0
                )
            """)
            for col in ["favori INTEGER DEFAULT 0", "selectionne INTEGER DEFAULT 0"]:
                try:
                    cur.execute(f"ALTER TABLE recettes ADD COLUMN {col}")
                except Exception:
                    pass
            cur.execute("""
                CREATE TABLE IF NOT EXISTS calendrier (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    recette_id INTEGER NOT NULL,
                    moment TEXT DEFAULT 'diner',
                    FOREIGN KEY (recette_id) REFERENCES recettes(id)
                )
            """)
        conn.commit()
    finally:
        conn.close()


def _ligne_vers_recette(ligne):
    """Transforme une ligne en dictionnaire recette."""
    d = dict(ligne)
    return {
        "id": d["id"],
        "titre": d["titre"],
        "categorie": d["categorie"] or "",
        "ingredients": json.loads(d["ingredients"]),
        "etapes": json.loads(d["etapes"]),
        "temps_preparation": d["temps_preparation"],
        "portions": d["portions"],
        "image": d["image"] or "",
        "favori": bool(d["favori"]),
        "selectionne": bool(d["selectionne"]),
    }


def lister_recettes(recherche="", categorie=""):
    recherche = recherche.strip().lower()
    categorie = categorie.strip()
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM recettes ORDER BY id DESC")
        recettes = [_ligne_vers_recette(r) for r in cur.fetchall()]
    finally:
        conn.close()

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
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM recettes WHERE id = {PH}", (id_recette,))
        ligne = cur.fetchone()
    finally:
        conn.close()
    return _ligne_vers_recette(ligne) if ligne else None


def creer_recette(donnees):
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute(
                f"""INSERT INTO recettes
                    (titre, categorie, ingredients, etapes, temps_preparation, portions, image)
                    VALUES ({PH},{PH},{PH},{PH},{PH},{PH},{PH}) RETURNING id""",
                (
                    donnees["titre"], donnees.get("categorie", ""),
                    json.dumps(donnees["ingredients"], ensure_ascii=False),
                    json.dumps(donnees["etapes"], ensure_ascii=False),
                    donnees["temps_preparation"], donnees["portions"],
                    donnees.get("image", ""),
                ),
            )
            new_id = cur.fetchone()["id"]
        else:
            cur.execute(
                f"""INSERT INTO recettes
                    (titre, categorie, ingredients, etapes, temps_preparation, portions, image)
                    VALUES ({PH},{PH},{PH},{PH},{PH},{PH},{PH})""",
                (
                    donnees["titre"], donnees.get("categorie", ""),
                    json.dumps(donnees["ingredients"], ensure_ascii=False),
                    json.dumps(donnees["etapes"], ensure_ascii=False),
                    donnees["temps_preparation"], donnees["portions"],
                    donnees.get("image", ""),
                ),
            )
            new_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()
    return obtenir_recette(new_id)


def modifier_recette(id_recette, donnees):
    if obtenir_recette(id_recette) is None:
        return None
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        cur.execute(
            f"""UPDATE recettes SET
                titre={PH}, categorie={PH}, ingredients={PH}, etapes={PH},
                temps_preparation={PH}, portions={PH}, image={PH}
                WHERE id={PH}""",
            (
                donnees["titre"], donnees.get("categorie", ""),
                json.dumps(donnees["ingredients"], ensure_ascii=False),
                json.dumps(donnees["etapes"], ensure_ascii=False),
                donnees["temps_preparation"], donnees["portions"],
                donnees.get("image", ""), id_recette,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return obtenir_recette(id_recette)


def basculer_favori(id_recette):
    recette = obtenir_recette(id_recette)
    if recette is None:
        return None
    nouveau = not recette["favori"]
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        cur.execute(f"UPDATE recettes SET favori={PH} WHERE id={PH}", (nouveau, id_recette))
        conn.commit()
    finally:
        conn.close()
    return obtenir_recette(id_recette)


def basculer_selection(id_recette):
    recette = obtenir_recette(id_recette)
    if recette is None:
        return None
    nouveau = not recette["selectionne"]
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        cur.execute(f"UPDATE recettes SET selectionne={PH} WHERE id={PH}", (nouveau, id_recette))
        conn.commit()
    finally:
        conn.close()
    return obtenir_recette(id_recette)


def supprimer_recette(id_recette):
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM recettes WHERE id={PH}", (id_recette,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def lister_calendrier(debut, fin):
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        cur.execute(
            f"""SELECT c.id, c.date, c.moment,
                r.id as recette_id, r.titre, r.image, r.temps_preparation, r.portions
                FROM calendrier c
                JOIN recettes r ON c.recette_id = r.id
                WHERE c.date BETWEEN {PH} AND {PH}
                ORDER BY c.date, c.moment""",
            (debut, fin),
        )
        lignes = cur.fetchall()
    finally:
        conn.close()
    return [
        {
            "id": dict(l)["id"], "date": dict(l)["date"], "moment": dict(l)["moment"],
            "recette": {
                "id": dict(l)["recette_id"], "titre": dict(l)["titre"],
                "image": dict(l)["image"] or "",
                "temps_preparation": dict(l)["temps_preparation"],
                "portions": dict(l)["portions"],
            },
        }
        for l in lignes
    ]


def ajouter_au_calendrier(date, recette_id, moment):
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute(
                f"INSERT INTO calendrier (date, recette_id, moment) VALUES ({PH},{PH},{PH}) RETURNING id",
                (date, recette_id, moment),
            )
            new_id = cur.fetchone()["id"]
        else:
            cur.execute(
                f"INSERT INTO calendrier (date, recette_id, moment) VALUES ({PH},{PH},{PH})",
                (date, recette_id, moment),
            )
            new_id = cur.lastrowid
        conn.commit()
        return new_id
    finally:
        conn.close()


def supprimer_du_calendrier(id_entree):
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM calendrier WHERE id={PH}", (id_entree,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def lister_categories():
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT categorie FROM recettes WHERE categorie != '' ORDER BY categorie")
        lignes = cur.fetchall()
    finally:
        conn.close()
    return [dict(l)["categorie"] for l in lignes]
