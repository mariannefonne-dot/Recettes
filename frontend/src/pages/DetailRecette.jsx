import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { obtenirRecette, supprimerRecette, basculerFavori, basculerSelection, ajouterAuCalendrier, urlImage } from "../api.js";

function formatDate(date) {
  return date.toISOString().slice(0, 10);
}

function ModalCalendrier({ recette, onFermer }) {
  const [date, setDate] = useState(formatDate(new Date()));
  const [moment, setMoment] = useState("diner");
  const [succes, setSucces] = useState(false);

  async function confirmer() {
    await ajouterAuCalendrier(date, recette.id, moment);
    setSucces(true);
    setTimeout(onFermer, 1200);
  }

  return (
    <div className="cal-modal-fond" onClick={onFermer}>
      <div className="cal-modal" onClick={(e) => e.stopPropagation()}>
        {succes ? (
          <p className="modal-succes">✅ Ajouté au calendrier !</p>
        ) : (
          <>
            <h2 className="cal-modal-titre">
              📅 Ajouter au calendrier<br />
              <small>{recette.titre}</small>
            </h2>

            <div className="champ">
              <label>Date</label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </div>

            <div className="champ">
              <label>Repas</label>
              <select value={moment} onChange={(e) => setMoment(e.target.value)}>
                <option value="dejeuner">🍽 Déjeuner</option>
                <option value="diner">🌙 Dîner</option>
              </select>
            </div>

            <div className="cal-modal-actions">
              <button className="bouton-sauvegarder" onClick={confirmer}>
                Ajouter
              </button>
              <button className="lien-annuler" onClick={onFermer}>Annuler</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default function DetailRecette() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [recette, setRecette] = useState(null);
  const [erreur, setErreur] = useState("");
  const [modalCalendrier, setModalCalendrier] = useState(false);

  useEffect(() => {
    obtenirRecette(id).then(setRecette).catch((e) => setErreur(e.message));
  }, [id]);

  async function gererFavori() {
    const mise_a_jour = await basculerFavori(id);
    setRecette(mise_a_jour);
  }

  async function gererSelection() {
    const mise_a_jour = await basculerSelection(id);
    setRecette(mise_a_jour);
  }

  async function gererSuppression() {
    if (!window.confirm("Supprimer cette recette définitivement ?")) return;
    await supprimerRecette(id);
    navigate("/");
  }

  if (erreur) return <p className="message-vide">{erreur}</p>;
  if (!recette) return <p className="message-vide">Chargement…</p>;

  return (
    <>
      <article className="detail-recette">
        <div className="entete-recette">
          <h1>{recette.titre}</h1>
          <div className="actions">
            <button
              onClick={gererSelection}
              className={`bouton-favori ${recette.selectionne ? "selection-actif" : ""}`}
              title={recette.selectionne ? "Retirer de mes recettes" : "Ajouter à mes recettes"}
            >
              🔖
            </button>
            <button
              onClick={gererFavori}
              className={`bouton-favori ${recette.favori ? "favori-actif" : ""}`}
              title={recette.favori ? "Retirer des favoris" : "Ajouter aux favoris"}
            >
              {recette.favori ? "❤️" : "🤍"}
            </button>
            <button
              onClick={() => setModalCalendrier(true)}
              className="bouton-modifier"
              title="Ajouter au calendrier"
            >
              📅 Calendrier
            </button>
            <Link to={`/modifier/${recette.id}`} className="bouton-modifier">
              Modifier
            </Link>
            <button onClick={gererSuppression} className="bouton-supprimer">
              Supprimer
            </button>
          </div>
        </div>

        {recette.image && (
          <img
            src={urlImage(recette.image)}
            alt={recette.titre}
            className="photo-recette"
          />
        )}

        {recette.categorie && (
          <span className="etiquette">{recette.categorie}</span>
        )}

        <div className="meta-recette">
          <span>{recette.temps_preparation} minutes</span>
          <span>
            {recette.portions} portion{recette.portions > 1 ? "s" : ""}
          </span>
        </div>

        <section>
          <h2>Ingrédients</h2>
          <ul>
            {recette.ingredients.map((ing, i) => <li key={i}>{ing}</li>)}
          </ul>
        </section>

        <section>
          <h2>Préparation</h2>
          <ol>
            {recette.etapes.map((etape, i) => <li key={i}>{etape}</li>)}
          </ol>
        </section>
      </article>

      <Link to="/" className="lien-retour">← Retour aux recettes</Link>

      {modalCalendrier && (
        <ModalCalendrier
          recette={recette}
          onFermer={() => setModalCalendrier(false)}
        />
      )}
    </>
  );
}
