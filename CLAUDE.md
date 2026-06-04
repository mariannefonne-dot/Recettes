# Projet Recettes

Application web pour consulter, ajouter et rechercher des recettes de cuisine.

## Fonctionnalités implémentées

- [x] Afficher la liste des recettes avec photo (optionnelle), catégorie, temps et portions
- [x] Page de détail d'une recette (ingrédients, étapes, méta-données)
- [x] Ajouter une recette via un formulaire
- [x] Modifier une recette existante (catégorie via menu déroulant)
- [x] Supprimer une recette (avec confirmation)
- [x] Rechercher par titre ou ingrédient
- [x] Filtrer par catégorie (menu déroulant multi-sélection)
- [x] Téléverser une photo depuis le formulaire (upload)
- [x] Dockerisation multi-services avec `docker-compose.yml`
- [x] Page d'accueil avec grille de catégories cliquables + bouton ajouter en bas
- [x] Mettre une recette en favori (❤️) — persisté en base, filtrable depuis l'accueil
- [x] Sélectionner des recettes (🔖) pour les retrouver dans "Ma sélection"
- [x] Page "Ma sélection" — liste des recettes sélectionnées
- [x] Panier de courses — cumul et addition automatique des ingrédients des recettes sélectionnées, avec cases à cocher (état persisté dans localStorage), articles cochés repoussés en bas
- [x] Calendrier hebdomadaire — assigner des recettes à chaque jour (déjeuner/dîner), navigation entre semaines, bouton "📅 Calendrier" sur la page de détail
- [x] Sidebar droite — mini-calendrier mensuel (jours avec recettes surlignés en rouge) + encart "Ma sélection"

## Architecture

L'application est séparée en deux parties qui communiquent via une **API REST JSON** :

```
Front React (port 5173) ──/api──> Backend Flask (port 5000) ──> SQLite (recettes.db) [local]
                                              └──> images dans static/images/

En production :
Netlify (frontend) ──────────────> Railway (backend Flask) ──> Neon PostgreSQL
```

## Stack technique

- **Backend** : Python 3.12 + Flask 3.1.3 — expose une API REST (routes `/api/...`)
- **Stockage local** : base **SQLite** (`recettes.db`) via `base_donnees.py`
- **Stockage production** : **PostgreSQL** (Neon) — détecté automatiquement via la variable d'environnement `DATABASE_URL`
- **Dual DB** : `base_donnees.py` détecte `DATABASE_URL` et bascule entre SQLite (placeholder `?`) et PostgreSQL (placeholder `%s`)
- **Images** : téléversées vers `static/images/`, servies par Flask (en ligne, les images ne sont pas persistées)
- **Frontend** : **React** (Vite + React Router) dans `frontend/`, consomme l'API
- **Tests** : pytest sur l'API backend (base SQLite temporaire isolée par test)
- **Déploiement local** : Docker + Docker Compose (2 services : `backend`, `frontend`)

> `recettes.json` a servi de source à la migration initiale (`migrer_json_vers_sqlite.py`) puis a été supprimé. Les données vivent désormais dans `recettes.db` (local) ou Neon PostgreSQL (production).

## Déploiement en ligne

| Service | Rôle | URL |
|---|---|---|
| **Netlify** | Frontend React (statique, gratuit) | https://startling-centaur-d09681.netlify.app |
| **Railway** | Backend Flask (gratuit avec $5 crédit/mois) | https://recettes-backend-production-5087.up.railway.app |
| **Neon** | PostgreSQL hébergé (gratuit) | dashboard sur neon.tech |

**Variables d'environnement Railway** (à ne jamais committer) :
- `DATABASE_URL` — chaîne de connexion Neon PostgreSQL
- `PORT` — géré automatiquement par Railway

**Variable d'environnement Netlify** :
- `VITE_API_URL` — URL du backend Railway (ex: `https://recettes-backend-production-5087.up.railway.app`)

**Fichiers de configuration déploiement** :
- `netlify.toml` — indique à Netlify de builder depuis `frontend/`
- `requirements.txt` — inclut `psycopg2-binary` et `gunicorn` pour Railway

## Structure des fichiers frontend

```
frontend/src/
├── App.jsx                      — routes, header global, layout avec sidebar
├── api.js                       — toutes les fonctions d'appel à l'API
├── categories.js                — liste partagée des catégories
├── parseIngredient.js           — parser et additionneur d'ingrédients (panier)
├── index.css                    — styles globaux
├── components/
│   └── MiniCalendrier.jsx       — sidebar : mini-calendrier mensuel + encart Ma sélection
└── pages/
    ├── Accueil.jsx              — grille de catégories + bouton ajouter
    ├── ListeRecettes.jsx        — liste filtrée, multi-sélection de catégories
    ├── DetailRecette.jsx        — détail, favori, sélection, ajout au calendrier
    ├── FormulaireRecette.jsx    — ajout/modification
    ├── MesRecettes.jsx          — recettes marquées 🔖
    ├── PanierCourses.jsx        — liste de courses avec cases à cocher
    └── Calendrier.jsx           — calendrier hebdomadaire
```

## Principales routes de l'API

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/api/recettes?recherche=&categorie=` | Liste (avec recherche/filtre) |
| GET | `/api/recettes/<id>` | Détail d'une recette |
| POST | `/api/recettes` | Créer (JSON) |
| PUT | `/api/recettes/<id>` | Modifier (JSON) |
| DELETE | `/api/recettes/<id>` | Supprimer |
| POST | `/api/recettes/<id>/favori` | Basculer favori |
| POST | `/api/recettes/<id>/selection` | Basculer sélection (🔖) |
| GET | `/api/categories` | Liste des catégories existantes |
| POST | `/api/televerser-image` | Upload d'une image (multipart) |
| GET | `/api/calendrier?debut=&fin=` | Entrées du calendrier sur une période |
| POST | `/api/calendrier` | Ajouter une recette au calendrier |
| DELETE | `/api/calendrier/<id>` | Retirer une entrée du calendrier |

## Structure de la base de données

**Table `recettes`** : `id`, `titre`, `categorie`, `ingredients` (JSON), `etapes` (JSON), `temps_preparation`, `portions`, `image`, `favori` (0/1), `selectionne` (0/1)

**Table `calendrier`** : `id`, `date` (YYYY-MM-DD), `recette_id`, `moment` (dejeuner/diner)

## Catégories disponibles

Définies dans `frontend/src/categories.js` : Entrée, Plat, Pâtes, Sauces, Dessert, Boisson.
La page d'accueil ajoute aussi : Toutes les recettes (🍴), Favoris (⭐).

## Mise en page

La page utilise un layout en grille à 4 colonnes :
- Colonne 1 : espace vide (gauche)
- Colonne 2 : contenu principal (`<main>`, max 900 px)
- Colonne 3 : sidebar droite (`MiniCalendrier`, 210 px, sticky)
- Colonne 4 : espace vide (droite)

La sidebar est masquée sur la page `/calendrier` (trop peu de place).

## Comportement attendu de Claude

- **Serveurs** : avant toute action qui nécessite que l'app soit accessible (ouvrir la page, tester une route, vérifier un résultat), vérifier que le backend (port 5000) et le frontend (port 5173) sont lancés. Si ce n'est pas le cas, les démarrer automatiquement sans attendre que l'utilisateur le demande.

## Lancer le projet

```bash
# Avec Docker (recommandé) — lance backend + frontend
docker compose up --build
```

- Front (l'app à utiliser) : **http://localhost:5173**
- API backend : **http://localhost:5000/api/recettes**

```bash
# Sans Docker
pip install -r requirements.txt
python app.py                      # backend sur le port 5000
cd frontend && npm install && npm run dev   # front sur le port 5173
```

## Lancer les tests

```bash
pytest tests/
```

## Conventions de code

- **Langue** : tout le code doit être en français — noms de variables, fonctions, commentaires, messages d'interface.
- **Tests** : chaque fonctionnalité doit être couverte par des tests. Écrire les tests en même temps que le code, pas après.
- **Commentaires** : ajouter un commentaire uniquement quand le "pourquoi" n'est pas évident. Ne pas commenter ce que le nom de la variable ou fonction explique déjà.

## Structure d'une recette

Chaque recette doit contenir au minimum :

- `titre` — nom de la recette
- `ingredients` — liste des ingrédients avec quantités
- `etapes` — liste des étapes de préparation
- `temps_preparation` — durée en minutes
- `portions` — nombre de portions

## Style de collaboration

L'utilisateur est débutant en développement. Expliquer les parties non-évidentes du code mais sans sur-commenter. Proposer des choix technologiques simples et justifiés. Éviter le jargon sans l'expliquer.
