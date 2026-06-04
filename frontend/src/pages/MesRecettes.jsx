import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listerRecettes, basculerSelection, urlImage } from "../api.js";

export default function MesRecettes() {
  const [recettes, setRecettes] = useState([]);
  const [chargement, setChargement] = useState(true);

  useEffect(() => {
    listerRecettes()
      .then((toutes) => setRecettes(toutes.filter((r) => r.selectionne)))
      .finally(() => setChargement(false));
  }, []);

  async function gererSelection(e, id) {
    e.preventDefault();
    const mise_a_jour = await basculerSelection(id);
    setRecettes((prev) =>
      prev.filter((r) => r.id !== mise_a_jour.id || mise_a_jour.selectionne)
    );
  }

  if (chargement) return <p className="message-vide">Chargement…</p>;

  return (
    <>
      <div className="mes-recettes-entete">
        <h1 className="titre-mes-recettes">🔖 Mes recettes</h1>
        {recettes.length > 0 && (
          <Link to="/panier" className="bouton-sauvegarder">
            🛒 Voir le panier de courses
          </Link>
        )}
      </div>

      {recettes.length === 0 ? (
        <p className="message-vide">
          Aucune recette sélectionnée.{" "}
          <Link to="/recettes">Parcourir les recettes</Link> et cliquer sur 🔖 pour en ajouter.
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
                className="bouton-selection-carte actif"
                onClick={(e) => gererSelection(e, recette.id)}
                title="Retirer de mes recettes"
              >
                🔖
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
                <span>{recette.portions} portion{recette.portions > 1 ? "s" : ""}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
