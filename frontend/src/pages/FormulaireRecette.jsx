import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { CATEGORIES } from "../categories.js";
import {
  obtenirRecette,
  creerRecette,
  modifierRecette,
  televerserImage,
  urlImage,
} from "../api.js";

export default function FormulaireRecette() {
  const { id } = useParams();
  const modeModification = Boolean(id);
  const navigate = useNavigate();

  const [titre, setTitre] = useState("");
  const [categorie, setCategorie] = useState("");
  const [ingredients, setIngredients] = useState("");
  const [etapes, setEtapes] = useState("");
  const [tempsPreparation, setTempsPreparation] = useState("");
  const [portions, setPortions] = useState("");
  const [image, setImage] = useState("");
  const [fichierImage, setFichierImage] = useState(null);
  const [erreur, setErreur] = useState("");
  const [envoiEnCours, setEnvoiEnCours] = useState(false);

  // En mode modification, on pré-remplit le formulaire avec la recette existante.
  // Les listes (ingrédients, étapes) sont affichées une par ligne dans le textarea.
  useEffect(() => {
    if (!modeModification) return;
    obtenirRecette(id).then((r) => {
      setTitre(r.titre);
      setCategorie(r.categorie);
      setIngredients(r.ingredients.join("\n"));
      setEtapes(r.etapes.join("\n"));
      setTempsPreparation(r.temps_preparation);
      setPortions(r.portions);
      setImage(r.image);
    });
  }, [id, modeModification]);

  async function gererEnvoi(e) {
    e.preventDefault();
    setEnvoiEnCours(true);
    setErreur("");
    try {
      // Si une nouvelle image a été choisie, on l'envoie d'abord pour récupérer
      // son nom de fichier, qu'on associe ensuite à la recette.
      let nomImage = image;
      if (fichierImage) {
        const resultat = await televerserImage(fichierImage);
        nomImage = resultat.image;
      }

      const donnees = {
        titre,
        categorie,
        ingredients: ingredients.split("\n").map((l) => l.trim()).filter(Boolean),
        etapes: etapes.split("\n").map((l) => l.trim()).filter(Boolean),
        temps_preparation: Number(tempsPreparation),
        portions: Number(portions),
        image: nomImage,
      };

      const recette = modeModification
        ? await modifierRecette(id, donnees)
        : await creerRecette(donnees);
      navigate(`/recette/${recette.id}`);
    } catch (e) {
      setErreur(e.message);
      setEnvoiEnCours(false);
    }
  }

  return (
    <div className="formulaire-recette">
      <h1>{modeModification ? "Modifier la recette" : "Nouvelle recette"}</h1>
      {erreur && <p className="message-erreur">{erreur}</p>}
      <form onSubmit={gererEnvoi}>
        <div className="champ">
          <label htmlFor="titre">Titre</label>
          <input id="titre" type="text" required
            value={titre} onChange={(e) => setTitre(e.target.value)} />
        </div>

        <div className="champ">
          <label htmlFor="categorie">
            Catégorie <span className="optionnel">(optionnel)</span>
          </label>
          <select id="categorie" value={categorie} onChange={(e) => setCategorie(e.target.value)}>
            <option value="">— Choisir une catégorie —</option>
            {CATEGORIES.map((cat) => (
              <option key={cat.label} value={cat.label}>
                {cat.emoji} {cat.label}
              </option>
            ))}
          </select>
        </div>

        <div className="champ">
          <label htmlFor="image">
            Photo <span className="optionnel">(optionnel)</span>
          </label>
          {image && !fichierImage && (
            <img src={urlImage(image)} alt="Aperçu" className="apercu-image" />
          )}
          <input id="image" type="file" accept="image/*"
            onChange={(e) => setFichierImage(e.target.files[0] || null)} />
        </div>

        <div className="champ">
          <label htmlFor="ingredients">
            Ingrédients <span className="aide">(un par ligne)</span>
          </label>
          <textarea id="ingredients" rows="6" required
            value={ingredients} onChange={(e) => setIngredients(e.target.value)} />
        </div>

        <div className="champ">
          <label htmlFor="etapes">
            Étapes de préparation <span className="aide">(une par ligne)</span>
          </label>
          <textarea id="etapes" rows="8" required
            value={etapes} onChange={(e) => setEtapes(e.target.value)} />
        </div>

        <div className="champ-ligne">
          <div className="champ">
            <label htmlFor="temps">Temps de préparation (minutes)</label>
            <input id="temps" type="number" min="1" required
              value={tempsPreparation}
              onChange={(e) => setTempsPreparation(e.target.value)} />
          </div>
          <div className="champ">
            <label htmlFor="portions">Nombre de portions</label>
            <input id="portions" type="number" min="1" required
              value={portions} onChange={(e) => setPortions(e.target.value)} />
          </div>
        </div>

        <div className="boutons-formulaire">
          <button type="submit" className="bouton-sauvegarder" disabled={envoiEnCours}>
            {envoiEnCours ? "Enregistrement…" : "Sauvegarder"}
          </button>
          <Link to="/" className="lien-annuler">Annuler</Link>
        </div>
      </form>
    </div>
  );
}
