import { useEffect, useRef, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { listerRecettes, basculerFavori, basculerSelection, urlImage } from "../api.js";
import { CATEGORIES } from "../categories.js";

// Menu déroulant avec cases à cocher pour sélectionner plusieurs catégories.
function SelecteurCategories({ selection, onChange }) {
  const [ouvert, setOuvert] = useState(false);
  const ref = useRef(null);

  // Ferme le menu si on clique en dehors.
  useEffect(() => {
    function fermerSiExterieur(e) {
      if (ref.current && !ref.current.contains(e.target)) setOuvert(false);
    }
    document.addEventListener("mousedown", fermerSiExterieur);
    return () => document.removeEventListener("mousedown", fermerSiExterieur);
  }, []);

  function toggleCategorie(label) {
    if (selection.includes(label)) {
      onChange(selection.filter((c) => c !== label));
    } else {
      onChange([...selection, label]);
    }
  }

  const libelle =
    selection.length === 0
      ? "Toutes les catégories"
      : selection.join(", ");

  return (
    <div className="selecteur-categories" ref={ref}>
      <button
        className="selecteur-bouton"
        onClick={() => setOuvert(!ouvert)}
        type="button"
      >
        <span className="selecteur-libelle">{libelle}</span>
        <span className="selecteur-fleche">{ouvert ? "▲" : "▼"}</span>
      </button>

      {ouvert && (
        <div className="selecteur-liste">
          {CATEGORIES.map((cat) => (
            <label key={cat.label} className="selecteur-option">
              <input
                type="checkbox"
                checked={selection.includes(cat.label)}
                onChange={() => toggleCategorie(cat.label)}
              />
              <span>{cat.emoji} {cat.label}</span>
            </label>
          ))}
          {selection.length > 0 && (
            <button
              className="selecteur-reinitialiser"
              onClick={() => onChange([])}
              type="button"
            >
              Tout décocher
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default function ListeRecettes() {
  const { categorie: categorieUrl } = useParams();
  const navigate = useNavigate();
  const [toutesRecettes, setToutesRecettes] = useState([]);
  const [recherche, setRecherche] = useState("");
  const [categoriesSelectionnees, setCategoriesSelectionnees] = useState(
    categorieUrl ? [categorieUrl] : []
  );
  const [favorisUniquement, setFavorisUniquement] = useState(categorieUrl === "favoris");
  const [chargement, setChargement] = useState(true);

  // Synchronise la sélection si l'URL change (ex : clic depuis l'accueil).
  useEffect(() => {
    if (categorieUrl === "favoris") {
      setFavorisUniquement(true);
      setCategoriesSelectionnees([]);
    } else {
      setFavorisUniquement(false);
      setCategoriesSelectionnees(categorieUrl ? [categorieUrl] : []);
    }
  }, [categorieUrl]);

  // Recharge toutes les recettes à chaque changement de recherche.
  useEffect(() => {
    setChargement(true);
    listerRecettes({ recherche })
      .then(setToutesRecettes)
      .finally(() => setChargement(false));
  }, [recherche]);

  // Filtre par catégories et/ou favoris (côté client).
  const recettes = toutesRecettes
    .filter((r) => !favorisUniquement || r.favori)
    .filter((r) =>
      categoriesSelectionnees.length === 0 || categoriesSelectionnees.includes(r.categorie)
    );

  async function gererFavori(e, id) {
    e.preventDefault(); // empêche la navigation vers la page de détail
    const mise_a_jour = await basculerFavori(id);
    setToutesRecettes((prev) =>
      prev.map((r) => (r.id === mise_a_jour.id ? mise_a_jour : r))
    );
  }

  async function gererSelection(e, id) {
    e.preventDefault();
    const mise_a_jour = await basculerSelection(id);
    setToutesRecettes((prev) =>
      prev.map((r) => (r.id === mise_a_jour.id ? mise_a_jour : r))
    );
  }

  function handleChangementCategories(nouvelleSelection) {
    setCategoriesSelectionnees(nouvelleSelection);
    setFavorisUniquement(false);
    if (nouvelleSelection.length === 1) {
      navigate(`/recettes/${nouvelleSelection[0]}`, { replace: true });
    } else {
      navigate("/recettes", { replace: true });
    }
  }

  const aDesFlitres = recherche || categoriesSelectionnees.length > 0 || favorisUniquement;

  return (
    <>
      <div className="filtres">
        <input
          type="text"
          placeholder="Chercher une recette ou un ingrédient…"
          value={recherche}
          onChange={(e) => setRecherche(e.target.value)}
        />
        <SelecteurCategories
          selection={categoriesSelectionnees}
          onChange={handleChangementCategories}
        />
        {aDesFlitres && (
          <button
            className="lien-reinitialiser"
            onClick={() => {
              setRecherche("");
              setCategoriesSelectionnees([]);
              navigate("/recettes", { replace: true });
            }}
          >
            Réinitialiser
          </button>
        )}
      </div>

      {chargement ? (
        <p className="message-vide">Chargement…</p>
      ) : recettes.length === 0 ? (
        <p className="message-vide">
          Aucune recette trouvée. <Link to="/ajouter">Ajouter une recette ?</Link>
        </p>
      ) : (
        <div className="liste-recettes">
          {recettes.map((recette) => (
            <Link
              key={recette.id}
              to={`/recette/${recette.id}`}
              className="carte-recette"
            >
              <button
                className="bouton-favori-carte"
                onClick={(e) => gererFavori(e, recette.id)}
                title={recette.favori ? "Retirer des favoris" : "Ajouter aux favoris"}
              >
                {recette.favori ? "❤️" : "🤍"}
              </button>
              <button
                className="bouton-selection-carte"
                onClick={(e) => gererSelection(e, recette.id)}
                title={recette.selectionne ? "Retirer de mes recettes" : "Ajouter à mes recettes"}
              >
                {recette.selectionne ? "🔖" : "🔖"}
              </button>
              {recette.image && (
                <img
                  src={urlImage(recette.image)}
                  alt={recette.titre}
                  className="photo-carte"
                />
              )}
              <h2>{recette.titre}</h2>
              {recette.categorie && (
                <span className="etiquette">{recette.categorie}</span>
              )}
              <div className="infos">
                <span>{recette.temps_preparation} min</span>
                <span>
                  {recette.portions} portion{recette.portions > 1 ? "s" : ""}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
