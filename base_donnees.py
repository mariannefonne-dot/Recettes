"""Couche d'accès aux données.

En développement local : SQLite (aucune configuration nécessaire).
En production sur Railway : PostgreSQL, détecté via la variable DATABASE_URL.
"""

import json
import os
import sqlite3
import uuid

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


def initialiser_bd():
    conn = obtenir_connexion()
    try:
        if USE_POSTGRES:
            # En PostgreSQL, on utilise autocommit pour les DDL afin qu'une erreur
            # sur une instruction n'annule pas toutes les autres.
            conn.autocommit = True
            cur = conn.cursor()
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
                CREATE TABLE IF NOT EXISTS utilisateurs (
                    id SERIAL PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    mot_de_passe_hash TEXT NOT NULL,
                    nom TEXT NOT NULL,
                    est_admin BOOLEAN DEFAULT FALSE,
                    cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS invitations (
                    id SERIAL PRIMARY KEY,
                    token TEXT NOT NULL UNIQUE,
                    utilise BOOLEAN DEFAULT FALSE,
                    cree_par INTEGER REFERENCES utilisateurs(id),
                    cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS favoris (
                    utilisateur_id INTEGER NOT NULL REFERENCES utilisateurs(id),
                    recette_id INTEGER NOT NULL REFERENCES recettes(id),
                    PRIMARY KEY (utilisateur_id, recette_id)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS selections (
                    utilisateur_id INTEGER NOT NULL REFERENCES utilisateurs(id),
                    recette_id INTEGER NOT NULL REFERENCES recettes(id),
                    PRIMARY KEY (utilisateur_id, recette_id)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS calendrier (
                    id SERIAL PRIMARY KEY,
                    date TEXT NOT NULL,
                    recette_id INTEGER NOT NULL REFERENCES recettes(id),
                    moment TEXT DEFAULT 'diner',
                    utilisateur_id INTEGER REFERENCES utilisateurs(id)
                )
            """)
            # Migration : ajoute utilisateur_id à calendrier si la colonne manque.
            try:
                cur.execute("ALTER TABLE calendrier ADD COLUMN utilisateur_id INTEGER REFERENCES utilisateurs(id)")
            except Exception:
                pass  # La colonne existe déjà, c'est normal.
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
            cur.execute("""
                CREATE TABLE IF NOT EXISTS utilisateurs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    mot_de_passe_hash TEXT NOT NULL,
                    nom TEXT NOT NULL,
                    est_admin INTEGER DEFAULT 0,
                    cree_le TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS invitations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token TEXT NOT NULL UNIQUE,
                    utilise INTEGER DEFAULT 0,
                    cree_par INTEGER,
                    cree_le TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (cree_par) REFERENCES utilisateurs(id)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS favoris (
                    utilisateur_id INTEGER NOT NULL,
                    recette_id INTEGER NOT NULL,
                    PRIMARY KEY (utilisateur_id, recette_id),
                    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id),
                    FOREIGN KEY (recette_id) REFERENCES recettes(id)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS selections (
                    utilisateur_id INTEGER NOT NULL,
                    recette_id INTEGER NOT NULL,
                    PRIMARY KEY (utilisateur_id, recette_id),
                    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id),
                    FOREIGN KEY (recette_id) REFERENCES recettes(id)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS calendrier (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    recette_id INTEGER NOT NULL,
                    moment TEXT DEFAULT 'diner',
                    utilisateur_id INTEGER,
                    FOREIGN KEY (recette_id) REFERENCES recettes(id),
                    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
                )
            """)
            # Migrations sur tables existantes (colonnes ajoutées après la création initiale).
            for col_def in [
                "favori INTEGER DEFAULT 0",
                "selectionne INTEGER DEFAULT 0",
            ]:
                try:
                    cur.execute(f"ALTER TABLE recettes ADD COLUMN {col_def}")
                except Exception:
                    pass
            try:
                cur.execute("ALTER TABLE calendrier ADD COLUMN utilisateur_id INTEGER")
            except Exception:
                pass
        if not USE_POSTGRES:
            conn.commit()
    finally:
        conn.close()


# ── Utilitaires internes ──────────────────────────────────────────────────────

def _ligne_vers_recette(ligne):
    """Transforme une ligne DB en dictionnaire recette (sans favori/selectionne)."""
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
        # favori et selectionne seront ajoutés selon l'utilisateur connecté.
        "favori": False,
        "selectionne": False,
    }


def _enrichir_recettes(recettes, utilisateur_id):
    """Ajoute les champs favori et selectionne selon l'utilisateur."""
    if not utilisateur_id or not recettes:
        return recettes
    fav = obtenir_favoris_utilisateur(utilisateur_id)
    sel = obtenir_selections_utilisateur(utilisateur_id)
    for r in recettes:
        r["favori"] = r["id"] in fav
        r["selectionne"] = r["id"] in sel
    return recettes


# ── Recettes ─────────────────────────────────────────────────────────────────

def lister_recettes(recherche="", categorie="", utilisateur_id=None):
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
    return _enrichir_recettes(recettes, utilisateur_id)


def obtenir_recette(id_recette, utilisateur_id=None):
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM recettes WHERE id = {PH}", (id_recette,))
        ligne = cur.fetchone()
    finally:
        conn.close()
    if ligne is None:
        return None
    recette = _ligne_vers_recette(ligne)
    _enrichir_recettes([recette], utilisateur_id)
    return recette


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


def supprimer_recette(id_recette):
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        # Supprime d'abord les entrées liées dans les tables dépendantes.
        cur.execute(f"DELETE FROM favoris WHERE recette_id={PH}", (id_recette,))
        cur.execute(f"DELETE FROM selections WHERE recette_id={PH}", (id_recette,))
        cur.execute(f"DELETE FROM calendrier WHERE recette_id={PH}", (id_recette,))
        cur.execute(f"DELETE FROM recettes WHERE id={PH}", (id_recette,))
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


# ── Favoris et sélections (par utilisateur) ───────────────────────────────────

def obtenir_favoris_utilisateur(utilisateur_id):
    """Retourne l'ensemble des IDs de recettes favorites pour cet utilisateur."""
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT recette_id FROM favoris WHERE utilisateur_id={PH}", (utilisateur_id,))
        return {dict(r)["recette_id"] for r in cur.fetchall()}
    finally:
        conn.close()


def basculer_favori(id_recette, utilisateur_id):
    """Ajoute ou retire la recette des favoris de l'utilisateur."""
    favoris = obtenir_favoris_utilisateur(utilisateur_id)
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        if id_recette in favoris:
            cur.execute(
                f"DELETE FROM favoris WHERE utilisateur_id={PH} AND recette_id={PH}",
                (utilisateur_id, id_recette),
            )
        else:
            cur.execute(
                f"INSERT INTO favoris (utilisateur_id, recette_id) VALUES ({PH},{PH})",
                (utilisateur_id, id_recette),
            )
        conn.commit()
    finally:
        conn.close()
    return obtenir_recette(id_recette, utilisateur_id)


def obtenir_selections_utilisateur(utilisateur_id):
    """Retourne l'ensemble des IDs de recettes sélectionnées pour cet utilisateur."""
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT recette_id FROM selections WHERE utilisateur_id={PH}", (utilisateur_id,))
        return {dict(r)["recette_id"] for r in cur.fetchall()}
    finally:
        conn.close()


def basculer_selection(id_recette, utilisateur_id):
    """Ajoute ou retire la recette de la sélection de l'utilisateur."""
    selections = obtenir_selections_utilisateur(utilisateur_id)
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        if id_recette in selections:
            cur.execute(
                f"DELETE FROM selections WHERE utilisateur_id={PH} AND recette_id={PH}",
                (utilisateur_id, id_recette),
            )
        else:
            cur.execute(
                f"INSERT INTO selections (utilisateur_id, recette_id) VALUES ({PH},{PH})",
                (utilisateur_id, id_recette),
            )
        conn.commit()
    finally:
        conn.close()
    return obtenir_recette(id_recette, utilisateur_id)


def lister_recettes_selectionnees(utilisateur_id):
    """Retourne la liste complète des recettes sélectionnées par l'utilisateur."""
    ids = obtenir_selections_utilisateur(utilisateur_id)
    if not ids:
        return []
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        placeholders = ",".join([PH] * len(ids))
        cur.execute(f"SELECT * FROM recettes WHERE id IN ({placeholders})", tuple(ids))
        recettes = [_ligne_vers_recette(r) for r in cur.fetchall()]
    finally:
        conn.close()
    return _enrichir_recettes(recettes, utilisateur_id)


# ── Calendrier ────────────────────────────────────────────────────────────────

def lister_calendrier(debut, fin, utilisateur_id=None):
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        if utilisateur_id:
            cur.execute(
                f"""SELECT c.id, c.date, c.moment,
                    r.id as recette_id, r.titre, r.image, r.temps_preparation, r.portions
                    FROM calendrier c
                    JOIN recettes r ON c.recette_id = r.id
                    WHERE c.date BETWEEN {PH} AND {PH} AND c.utilisateur_id = {PH}
                    ORDER BY c.date, c.moment""",
                (debut, fin, utilisateur_id),
            )
        else:
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


def ajouter_au_calendrier(date, recette_id, moment, utilisateur_id=None):
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute(
                f"INSERT INTO calendrier (date, recette_id, moment, utilisateur_id) VALUES ({PH},{PH},{PH},{PH}) RETURNING id",
                (date, recette_id, moment, utilisateur_id),
            )
            new_id = cur.fetchone()["id"]
        else:
            cur.execute(
                f"INSERT INTO calendrier (date, recette_id, moment, utilisateur_id) VALUES ({PH},{PH},{PH},{PH})",
                (date, recette_id, moment, utilisateur_id),
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


# ── Utilisateurs ──────────────────────────────────────────────────────────────

def _ligne_vers_utilisateur(ligne):
    """Transforme une ligne DB en dictionnaire utilisateur (sans le mot de passe)."""
    d = dict(ligne)
    return {
        "id": d["id"],
        "email": d["email"],
        "nom": d["nom"],
        "est_admin": bool(d["est_admin"]),
    }


def compter_utilisateurs():
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as n FROM utilisateurs")
        return dict(cur.fetchone())["n"]
    finally:
        conn.close()


def creer_utilisateur(email, mot_de_passe_hash, nom, est_admin=False):
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute(
                f"INSERT INTO utilisateurs (email, mot_de_passe_hash, nom, est_admin) VALUES ({PH},{PH},{PH},{PH}) RETURNING id",
                (email, mot_de_passe_hash, nom, est_admin),
            )
            new_id = cur.fetchone()["id"]
        else:
            cur.execute(
                f"INSERT INTO utilisateurs (email, mot_de_passe_hash, nom, est_admin) VALUES ({PH},{PH},{PH},{PH})",
                (email, mot_de_passe_hash, nom, int(est_admin)),
            )
            new_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()
    return obtenir_utilisateur(new_id)


def obtenir_utilisateur(id_utilisateur):
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM utilisateurs WHERE id={PH}", (id_utilisateur,))
        ligne = cur.fetchone()
    finally:
        conn.close()
    return _ligne_vers_utilisateur(ligne) if ligne else None


def obtenir_utilisateur_par_email(email):
    """Retourne l'utilisateur avec son hash (pour la vérification du mot de passe)."""
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM utilisateurs WHERE email={PH}", (email,))
        ligne = cur.fetchone()
    finally:
        conn.close()
    return dict(ligne) if ligne else None


# ── Invitations ───────────────────────────────────────────────────────────────

def creer_invitation(cree_par_id):
    """Génère un token d'invitation unique et le persiste en base."""
    token = uuid.uuid4().hex
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        cur.execute(
            f"INSERT INTO invitations (token, cree_par) VALUES ({PH},{PH})",
            (token, cree_par_id),
        )
        conn.commit()
    finally:
        conn.close()
    return token


def invitation_valide(token):
    """Vérifie qu'un token d'invitation existe et n'a pas encore été utilisé."""
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        cur.execute(
            f"SELECT id FROM invitations WHERE token={PH} AND utilise={PH}",
            (token, False if USE_POSTGRES else 0),
        )
        return cur.fetchone() is not None
    finally:
        conn.close()


def reinitialiser_mot_de_passe_admin(mot_de_passe_hash):
    """Met à jour le mot de passe de tous les comptes admin. Retourne le nombre de comptes modifiés."""
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        valeur_admin = True if USE_POSTGRES else 1
        cur.execute(
            f"UPDATE utilisateurs SET mot_de_passe_hash={PH} WHERE est_admin={PH}",
            (mot_de_passe_hash, valeur_admin),
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def consommer_invitation(token):
    """Marque le token comme utilisé."""
    conn = obtenir_connexion()
    try:
        cur = conn.cursor()
        cur.execute(
            f"UPDATE invitations SET utilise={PH} WHERE token={PH}",
            (True if USE_POSTGRES else 1, token),
        )
        conn.commit()
    finally:
        conn.close()
