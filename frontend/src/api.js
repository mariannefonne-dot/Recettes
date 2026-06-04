// Toutes les fonctions qui parlent au backend sont regroupées ici.
// En développement, VITE_API_URL n'est pas défini et les URLs sont relatives (/api/...).
// En production (Netlify), VITE_API_URL pointe vers le backend Railway.
const BASE = import.meta.env.VITE_API_URL || "";

async function lireReponse(reponse) {
  if (!reponse.ok) {
    const corps = await reponse.json().catch(() => ({}));
    throw new Error(corps.erreur || "Une erreur est survenue.");
  }
  if (reponse.status === 204) return null;
  return reponse.json();
}

// Retourne les en-têtes avec le token JWT si l'utilisateur est connecté.
function enTetesAuth(avecJson = false) {
  const token = localStorage.getItem("token") || "";
  const entetes = {};
  if (token) entetes["Authorization"] = `Bearer ${token}`;
  if (avecJson) entetes["Content-Type"] = "application/json";
  return entetes;
}

// ── Authentification ──────────────────────────────────────────────────────────

export function seConnecter(email, mot_de_passe) {
  return fetch(`${BASE}/api/auth/connexion`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, mot_de_passe }),
  }).then(lireReponse);
}

export function sInscrire(token, email, nom, mot_de_passe) {
  return fetch(`${BASE}/api/auth/inscription`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, email, nom, mot_de_passe }),
  }).then(lireReponse);
}

export function creerCompteAdmin(email, nom, mot_de_passe) {
  return fetch(`${BASE}/api/auth/setup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, nom, mot_de_passe }),
  }).then(lireReponse);
}

export function creerInvitation() {
  return fetch(`${BASE}/api/auth/inviter`, {
    method: "POST",
    headers: enTetesAuth(),
  }).then(lireReponse);
}

// ── Recettes ──────────────────────────────────────────────────────────────────

export function listerRecettes({ recherche = "", categorie = "" } = {}) {
  const params = new URLSearchParams();
  if (recherche) params.set("recherche", recherche);
  if (categorie) params.set("categorie", categorie);
  return fetch(`${BASE}/api/recettes?${params}`, {
    headers: enTetesAuth(),
  }).then(lireReponse);
}

export function listerCategories() {
  return fetch(`${BASE}/api/categories`, {
    headers: enTetesAuth(),
  }).then(lireReponse);
}

export function obtenirRecette(id) {
  return fetch(`${BASE}/api/recettes/${id}`, {
    headers: enTetesAuth(),
  }).then(lireReponse);
}

export function creerRecette(donnees) {
  return fetch(`${BASE}/api/recettes`, {
    method: "POST",
    headers: enTetesAuth(true),
    body: JSON.stringify(donnees),
  }).then(lireReponse);
}

export function modifierRecette(id, donnees) {
  return fetch(`${BASE}/api/recettes/${id}`, {
    method: "PUT",
    headers: enTetesAuth(true),
    body: JSON.stringify(donnees),
  }).then(lireReponse);
}

export function basculerSelection(id) {
  return fetch(`${BASE}/api/recettes/${id}/selection`, {
    method: "POST",
    headers: enTetesAuth(),
  }).then(lireReponse);
}

export function basculerFavori(id) {
  return fetch(`${BASE}/api/recettes/${id}/favori`, {
    method: "POST",
    headers: enTetesAuth(),
  }).then(lireReponse);
}

export function supprimerRecette(id) {
  return fetch(`${BASE}/api/recettes/${id}`, {
    method: "DELETE",
    headers: enTetesAuth(),
  }).then(lireReponse);
}

export function televerserImage(fichier) {
  const donnees = new FormData();
  donnees.append("image", fichier);
  return fetch(`${BASE}/api/televerser-image`, {
    method: "POST",
    headers: enTetesAuth(), // pas avecJson=true : FormData gère son propre Content-Type
    body: donnees,
  }).then(lireReponse);
}

// ── Calendrier ────────────────────────────────────────────────────────────────

export function listerCalendrier(debut, fin) {
  return fetch(`${BASE}/api/calendrier?debut=${debut}&fin=${fin}`, {
    headers: enTetesAuth(),
  }).then(lireReponse);
}

export function ajouterAuCalendrier(date, recette_id, moment) {
  return fetch(`${BASE}/api/calendrier`, {
    method: "POST",
    headers: enTetesAuth(true),
    body: JSON.stringify({ date, recette_id, moment }),
  }).then(lireReponse);
}

export function supprimerDuCalendrier(id) {
  return fetch(`${BASE}/api/calendrier/${id}`, {
    method: "DELETE",
    headers: enTetesAuth(),
  }).then(lireReponse);
}

// Construit l'URL d'affichage d'une image stockée côté backend.
export function urlImage(nomFichier) {
  return `${BASE}/static/images/${nomFichier}`;
}
