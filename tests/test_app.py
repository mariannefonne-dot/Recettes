"""Tests de l'API REST.

Chaque test tourne sur une base SQLite temporaire isolée (grâce à tmp_path),
ce qui évite de toucher la vraie base recettes.db.
"""

import io
import pytest

import base_donnees
from app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    base_test = tmp_path / "test.db"
    monkeypatch.setattr(base_donnees, "CHEMIN_BD", str(base_test))
    base_donnees.initialiser_bd()
    base_donnees.creer_recette({
        "titre": "Tarte aux pommes",
        "categorie": "dessert",
        "ingredients": ["3 pommes", "1 pâte brisée", "50g sucre"],
        "etapes": ["Éplucher les pommes", "Étaler la pâte", "Cuire 30 min"],
        "temps_preparation": 45,
        "portions": 6,
    })
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def _id_premiere_recette(client):
    return client.get("/api/recettes").get_json()[0]["id"]


def test_lister_recettes(client):
    reponse = client.get("/api/recettes")
    assert reponse.status_code == 200
    recettes = reponse.get_json()
    assert len(recettes) == 1
    assert recettes[0]["titre"] == "Tarte aux pommes"


def test_recherche_par_titre(client):
    recettes = client.get("/api/recettes?recherche=pommes").get_json()
    assert len(recettes) == 1


def test_recherche_par_ingredient(client):
    recettes = client.get("/api/recettes?recherche=sucre").get_json()
    assert len(recettes) == 1


def test_recherche_sans_resultats(client):
    recettes = client.get("/api/recettes?recherche=pizza").get_json()
    assert recettes == []


def test_filtre_par_categorie(client):
    recettes = client.get("/api/recettes?categorie=dessert").get_json()
    assert len(recettes) == 1


def test_filtre_categorie_inexistante(client):
    recettes = client.get("/api/recettes?categorie=entree").get_json()
    assert recettes == []


def test_lister_categories(client):
    categories = client.get("/api/categories").get_json()
    assert categories == ["dessert"]


def test_detail_recette(client):
    id_recette = _id_premiere_recette(client)
    reponse = client.get(f"/api/recettes/{id_recette}")
    assert reponse.status_code == 200
    recette = reponse.get_json()
    assert recette["titre"] == "Tarte aux pommes"
    assert "3 pommes" in recette["ingredients"]


def test_detail_recette_inexistante(client):
    reponse = client.get("/api/recettes/9999")
    assert reponse.status_code == 404


def test_creer_recette(client):
    reponse = client.post("/api/recettes", json={
        "titre": "Soupe aux oignons",
        "categorie": "soupe",
        "ingredients": ["3 oignons", "1L bouillon"],
        "etapes": ["Faire revenir les oignons", "Ajouter le bouillon"],
        "temps_preparation": 30,
        "portions": 4,
    })
    assert reponse.status_code == 201
    assert reponse.get_json()["titre"] == "Soupe aux oignons"
    assert len(client.get("/api/recettes").get_json()) == 2


def test_creer_recette_invalide(client):
    reponse = client.post("/api/recettes", json={"titre": "Incomplète"})
    assert reponse.status_code == 400


def test_modifier_recette(client):
    id_recette = _id_premiere_recette(client)
    reponse = client.put(f"/api/recettes/{id_recette}", json={
        "titre": "Tarte aux poires",
        "categorie": "dessert",
        "ingredients": ["3 poires", "1 pâte brisée"],
        "etapes": ["Éplucher les poires", "Cuire 25 min"],
        "temps_preparation": 40,
        "portions": 4,
    })
    assert reponse.status_code == 200
    assert reponse.get_json()["titre"] == "Tarte aux poires"


def test_modifier_recette_inexistante(client):
    reponse = client.put("/api/recettes/9999", json={
        "titre": "X",
        "ingredients": ["a"],
        "etapes": ["b"],
        "temps_preparation": 1,
        "portions": 1,
    })
    assert reponse.status_code == 404


def test_supprimer_recette(client):
    id_recette = _id_premiere_recette(client)
    reponse = client.delete(f"/api/recettes/{id_recette}")
    assert reponse.status_code == 204
    assert client.get("/api/recettes").get_json() == []


def test_supprimer_recette_inexistante(client):
    reponse = client.delete("/api/recettes/9999")
    assert reponse.status_code == 404


def test_televerser_image(client):
    donnees = {"image": (io.BytesIO(b"faux contenu image"), "photo.jpg")}
    reponse = client.post("/api/televerser-image", data=donnees,
                          content_type="multipart/form-data")
    assert reponse.status_code == 201
    assert reponse.get_json()["image"].endswith("_photo.jpg")


def test_televerser_image_mauvais_format(client):
    donnees = {"image": (io.BytesIO(b"texte"), "document.txt")}
    reponse = client.post("/api/televerser-image", data=donnees,
                          content_type="multipart/form-data")
    assert reponse.status_code == 400
