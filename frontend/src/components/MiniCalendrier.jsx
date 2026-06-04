import { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { listerCalendrier, listerRecettes, urlImage } from "../api.js";

const JOURS_COURTS = ["L", "M", "M", "J", "V", "S", "D"];
const MOIS = [
  "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
  "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
];

function formatDate(date) {
  return date.toISOString().slice(0, 10);
}

export default function MiniCalendrier() {
  const navigate = useNavigate();
  const [mois, setMois] = useState(() => {
    const d = new Date();
    return { annee: d.getFullYear(), mois: d.getMonth() };
  });
  const [joursAvecRecettes, setJoursAvecRecettes] = useState(new Set());
  const [selection, setSelection] = useState([]);

  useEffect(() => {
    const debut = new Date(mois.annee, mois.mois, 1);
    const fin = new Date(mois.annee, mois.mois + 1, 0);
    listerCalendrier(formatDate(debut), formatDate(fin)).then((entrees) => {
      setJoursAvecRecettes(new Set(entrees.map((e) => e.date)));
    });
  }, [mois]);

  useEffect(() => {
    listerRecettes().then((toutes) => setSelection(toutes.filter((r) => r.selectionne)));
  }, []);

  function moisPrec() {
    setMois((m) => {
      if (m.mois === 0) return { annee: m.annee - 1, mois: 11 };
      return { annee: m.annee, mois: m.mois - 1 };
    });
  }

  function moisSuiv() {
    setMois((m) => {
      if (m.mois === 11) return { annee: m.annee + 1, mois: 0 };
      return { annee: m.annee, mois: m.mois + 1 };
    });
  }

  // Génère les cases du calendrier (avec cases vides en début de mois).
  const premierJour = new Date(mois.annee, mois.mois, 1);
  // En Europe, la semaine commence le lundi (0=lundi … 6=dimanche).
  const decalage = (premierJour.getDay() + 6) % 7;
  const nbJours = new Date(mois.annee, mois.mois + 1, 0).getDate();

  const cases = [
    ...Array(decalage).fill(null),
    ...Array.from({ length: nbJours }, (_, i) => i + 1),
  ];

  const aujourdhuiStr = formatDate(new Date());

  function clickJour(jour) {
    const d = new Date(mois.annee, mois.mois, jour);
    navigate("/calendrier", { state: { date: formatDate(d) } });
  }

  return (
    <aside className="mini-cal">
      <div className="mini-cal-nav">
        <button onClick={moisPrec} className="mini-cal-btn">‹</button>
        <span className="mini-cal-titre">
          {MOIS[mois.mois]} {mois.annee}
        </span>
        <button onClick={moisSuiv} className="mini-cal-btn">›</button>
      </div>

      <div className="mini-cal-grille">
        {JOURS_COURTS.map((j, i) => (
          <div key={i} className="mini-cal-entete-jour">{j}</div>
        ))}
        {cases.map((jour, i) => {
          if (!jour) return <div key={`vide-${i}`} />;
          const dateStr = `${mois.annee}-${String(mois.mois + 1).padStart(2, "0")}-${String(jour).padStart(2, "0")}`;
          const aRecette = joursAvecRecettes.has(dateStr);
          const estAujourdhui = dateStr === aujourdhuiStr;
          return (
            <button
              key={dateStr}
              className={`mini-cal-jour ${aRecette ? "a-recette" : ""} ${estAujourdhui ? "aujourdhui" : ""}`}
              onClick={() => clickJour(jour)}
              title={aRecette ? "Recette(s) planifiée(s)" : ""}
            >
              {jour}
            </button>
          );
        })}
      </div>
      {/* Encart Ma sélection */}
      <div className="mini-selection">
        <div className="mini-selection-titre">
          🔖 Ma sélection
          <Link to="/mes-recettes" className="mini-selection-lien">voir tout</Link>
        </div>
        {selection.length === 0 ? (
          <p className="mini-selection-vide">Aucune recette sélectionnée.</p>
        ) : (
          <ul className="mini-selection-liste">
            {selection.slice(0, 5).map((r) => (
              <li key={r.id}>
                <Link to={`/recette/${r.id}`} className="mini-selection-item">
                  <span className="mini-selection-nom">{r.titre}</span>
                </Link>
              </li>
            ))}
            {selection.length > 5 && (
              <li className="mini-selection-plus">
                <Link to="/mes-recettes">+{selection.length - 5} de plus</Link>
              </li>
            )}
          </ul>
        )}
      </div>
    </aside>
  );
}
