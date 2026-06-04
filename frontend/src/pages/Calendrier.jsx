import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listerCalendrier, ajouterAuCalendrier, supprimerDuCalendrier, listerRecettes, urlImage } from "../api.js";

const JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"];
const MOMENTS = ["dejeuner", "diner"];
const LABELS_MOMENTS = { dejeuner: "🍽 Déjeuner", diner: "🌙 Dîner" };

function lundiDeLaSemaine(date) {
  const d = new Date(date);
  const jour = d.getDay() || 7; // dimanche = 7
  d.setDate(d.getDate() - jour + 1);
  d.setHours(0, 0, 0, 0);
  return d;
}

function formatDate(date) {
  return date.toISOString().slice(0, 10);
}

function formatAffichage(dateStr) {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
}

export default function Calendrier() {
  const [lundi, setLundi] = useState(() => lundiDeLaSemaine(new Date()));
  const [entrees, setEntrees] = useState([]);
  const [recettes, setRecettes] = useState([]);
  const [ajout, setAjout] = useState(null); // { date, moment }
  const [recetteChoisie, setRecetteChoisie] = useState("");

  const dimanche = new Date(lundi);
  dimanche.setDate(lundi.getDate() + 6);

  useEffect(() => {
    listerRecettes().then(setRecettes);
  }, []);

  useEffect(() => {
    listerCalendrier(formatDate(lundi), formatDate(dimanche)).then(setEntrees);
  }, [lundi]);

  function semainePrec() {
    const d = new Date(lundi);
    d.setDate(d.getDate() - 7);
    setLundi(d);
  }

  function semaineSuiv() {
    const d = new Date(lundi);
    d.setDate(d.getDate() + 7);
    setLundi(d);
  }

  function aujourdHui() {
    setLundi(lundiDeLaSemaine(new Date()));
  }

  async function confirmerAjout() {
    if (!recetteChoisie || !ajout) return;
    const res = await ajouterAuCalendrier(ajout.date, parseInt(recetteChoisie), ajout.moment);
    const recette = recettes.find((r) => r.id === parseInt(recetteChoisie));
    setEntrees((prev) => [
      ...prev,
      { id: res.id, date: ajout.date, moment: ajout.moment, recette },
    ]);
    setAjout(null);
    setRecetteChoisie("");
  }

  async function supprimer(id) {
    await supprimerDuCalendrier(id);
    setEntrees((prev) => prev.filter((e) => e.id !== id));
  }

  // Génère les 7 dates de la semaine
  const dates = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(lundi);
    d.setDate(lundi.getDate() + i);
    return formatDate(d);
  });

  const entreedParDateMoment = (date, moment) =>
    entrees.filter((e) => e.date === date && e.moment === moment);

  const aujourdhuiStr = formatDate(new Date());

  return (
    <div className="calendrier-page">
      {/* Navigation semaine */}
      <div className="calendrier-nav">
        <button onClick={semainePrec} className="cal-nav-bouton">‹</button>
        <div className="cal-nav-centre">
          <span className="cal-titre-semaine">
            Semaine du {formatAffichage(formatDate(lundi))} au {formatAffichage(formatDate(dimanche))}
          </span>
          <button onClick={aujourdHui} className="cal-bouton-aujourdhui">Aujourd'hui</button>
        </div>
        <button onClick={semaineSuiv} className="cal-nav-bouton">›</button>
      </div>

      {/* Grille */}
      <div className="calendrier-grille">
        {dates.map((date, i) => (
          <div key={date} className={`cal-jour ${date === aujourdhuiStr ? "cal-jour-actif" : ""}`}>
            <div className="cal-jour-entete">
              <span className="cal-jour-nom">{JOURS[i]}</span>
              <span className="cal-jour-date">{formatAffichage(date)}</span>
            </div>

            {MOMENTS.map((moment) => (
              <div key={moment} className="cal-repas">
                <div className="cal-repas-label">{LABELS_MOMENTS[moment]}</div>
                {entreedParDateMoment(date, moment).map((entree) => (
                  <div key={entree.id} className="cal-recette-chip">
                    <Link to={`/recette/${entree.recette.id}`} className="cal-recette-nom">
                      {entree.recette.image && (
                        <img src={urlImage(entree.recette.image)} alt="" className="cal-recette-img" />
                      )}
                      {entree.recette.titre}
                    </Link>
                    <button
                      className="cal-supprimer"
                      onClick={() => supprimer(entree.id)}
                      title="Retirer"
                    >×</button>
                  </div>
                ))}
                <button
                  className="cal-ajouter-btn"
                  onClick={() => { setAjout({ date, moment }); setRecetteChoisie(""); }}
                >+ ajouter</button>
              </div>
            ))}
          </div>
        ))}
      </div>

      {/* Modal d'ajout */}
      {ajout && (
        <div className="cal-modal-fond" onClick={() => setAjout(null)}>
          <div className="cal-modal" onClick={(e) => e.stopPropagation()}>
            <h2 className="cal-modal-titre">
              Ajouter une recette<br />
              <small>{JOURS[dates.indexOf(ajout.date)]} — {LABELS_MOMENTS[ajout.moment]}</small>
            </h2>
            <select
              className="cal-modal-select"
              value={recetteChoisie}
              onChange={(e) => setRecetteChoisie(e.target.value)}
              autoFocus
            >
              <option value="">— Choisir une recette —</option>
              {recettes.map((r) => (
                <option key={r.id} value={r.id}>{r.titre}</option>
              ))}
            </select>
            <div className="cal-modal-actions">
              <button
                className="bouton-sauvegarder"
                onClick={confirmerAjout}
                disabled={!recetteChoisie}
              >
                Ajouter
              </button>
              <button className="lien-annuler" onClick={() => setAjout(null)}>Annuler</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
