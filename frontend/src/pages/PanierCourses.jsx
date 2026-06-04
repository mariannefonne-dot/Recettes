import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listerRecettes } from "../api.js";
import { grouperIngredients } from "../parseIngredient.js";

export default function PanierCourses() {
  const [recettes, setRecettes] = useState([]);
  const [coches, setCoches] = useState(() => {
    // On récupère les cases déjà cochées depuis le stockage local du navigateur.
    try {
      return JSON.parse(localStorage.getItem("panier-coches") || "{}");
    } catch {
      return {};
    }
  });
  const [chargement, setChargement] = useState(true);

  useEffect(() => {
    listerRecettes()
      .then((toutes) => setRecettes(toutes.filter((r) => r.selectionne)))
      .finally(() => setChargement(false));
  }, []);

  function toggleCoche(cle) {
    setCoches((prev) => {
      const nouveau = { ...prev, [cle]: !prev[cle] };
      localStorage.setItem("panier-coches", JSON.stringify(nouveau));
      return nouveau;
    });
  }

  function toutDecocher() {
    setCoches({});
    localStorage.removeItem("panier-coches");
  }

  if (chargement) return <p className="message-vide">Chargement…</p>;

  if (recettes.length === 0) {
    return (
      <p className="message-vide">
        Aucune recette dans votre sélection.{" "}
        <Link to="/mes-recettes">Aller à ma sélection</Link>
      </p>
    );
  }

  // Regroupe et additionne les ingrédients, les non-cochés apparaissent en premier.
  const tousLesIngredients = grouperIngredients(recettes)
    .sort((a, b) => (!!coches[a.cle] ? 1 : 0) - (!!coches[b.cle] ? 1 : 0));

  const nbCoches = Object.values(coches).filter(Boolean).length;
  const nbTotal = tousLesIngredients.length;

  return (
    <div className="panier-courses">
      <div className="panier-entete">
        <h1>🛒 Panier de courses</h1>
        <div className="panier-meta">
          <span className="panier-compte">{nbCoches} / {nbTotal} articles cochés</span>
          {nbCoches > 0 && (
            <button className="panier-reinitialiser" onClick={toutDecocher}>
              Tout décocher
            </button>
          )}
        </div>
      </div>

      <p className="panier-sous-titre">
        {recettes.length} recette{recettes.length > 1 ? "s" : ""} —{" "}
        <Link to="/mes-recettes">modifier la sélection</Link>
      </p>

      <div className="panier-groupe">
        <ul className="panier-ingredients">
          {tousLesIngredients.map(({ cle, texte }) => {
            const estCoche = !!coches[cle];
            return (
              <li
                key={cle}
                className={`panier-ingredient ${estCoche ? "coche" : ""}`}
                onClick={() => toggleCoche(cle)}
              >
                <span className="panier-checkbox">{estCoche ? "✅" : "⬜"}</span>
                <span className="panier-ingredient-texte">{texte}</span>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
