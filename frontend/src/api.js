// Toutes les fonctions qui parlent au backend sont regroupées ici.
// Les URLs sont relatives (/api/...) : en développement le proxy Vite les
// redirige vers Flask, en production le serveur sert front et API au même endroit.

async function lireReponse(reponse) {
  if (!reponse.ok) {
    const corps = await reponse.json().catch(() => ({}));
    throw new Error(corps.erreur || "Une erreur est survenue.");
  }
  if (reponse.status === 204) return null;
  return reponse.json();
}

export function listerRecettes({ recherche = "", categorie = "" } = {}) {
  const params = new URLSearchParams();
  if (recherche) params.set("recherche", recherche);
  if (categorie) params.set("categorie", categorie);
  return fetch(`/api/recettes?${params}`).then(lireReponse);
}

export function listerCategories() {
  return fetch("/api/categories").then(lireReponse);
}

export function obtenirRecette(id) {
  return fetch(`/api/recettes/${id}`).then(lireReponse);
}

export function creerRecette(donnees) {
  return fetch("/api/recettes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(donnees),
  }).then(lireReponse);
}

export function modifierRecette(id, donnees) {
  return fetch(`/api/recettes/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(donnees),
  }).then(lireReponse);
}

export function basculerSelection(id) {
  return fetch(`/api/recettes/${id}/selection`, { method: "POST" }).then(lireReponse);
}

export function basculerFavori(id) {
  return fetch(`/api/recettes/${id}/favori`, { method: "POST" }).then(lireReponse);
}

export function supprimerRecette(id) {
  return fetch(`/api/recettes/${id}`, { method: "DELETE" }).then(lireReponse);
}

export function televerserImage(fichier) {
  const donnees = new FormData();
  donnees.append("image", fichier);
  return fetch("/api/televerser-image", {
    method: "POST",
    body: donnees,
  }).then(lireReponse);
}

export function listerCalendrier(debut, fin) {
  return fetch(`/api/calendrier?debut=${debut}&fin=${fin}`).then(lireReponse);
}

export function ajouterAuCalendrier(date, recette_id, moment) {
  return fetch("/api/calendrier", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ date, recette_id, moment }),
  }).then(lireReponse);
}

export function supprimerDuCalendrier(id) {
  return fetch(`/api/calendrier/${id}`, { method: "DELETE" }).then(lireReponse);
}

// Construit l'URL d'affichage d'une image stockée côté backend.
export function urlImage(nomFichier) {
  return `/static/images/${nomFichier}`;
}
