import { Link } from "react-router-dom";
import { CATEGORIES } from "../categories.js";

const CATEGORIES_ACCUEIL = [
  { label: "Toutes les recettes", lien: "/recettes",           emoji: "🍴" },
  { label: "Favoris",             lien: "/recettes/favoris",   emoji: "⭐" },
  ...CATEGORIES.map((cat) => ({ ...cat, lien: `/recettes/${cat.label}` })),
];

export default function Accueil() {
  return (
    <div className="accueil">
      <h1 className="accueil-titre">Que voulez-vous cuisiner ?</h1>
      <div className="grille-categories">
        {CATEGORIES_ACCUEIL.map((cat) => (
          <Link key={cat.lien} to={cat.lien} className="carte-categorie">
            <span className="categorie-emoji">{cat.emoji}</span>
            <span className="categorie-label">{cat.label}</span>
          </Link>
        ))}
      </div>

      <Link to="/ajouter" className="bouton-ajouter-accueil">
        + Ajouter une recette
      </Link>
    </div>
  );
}
