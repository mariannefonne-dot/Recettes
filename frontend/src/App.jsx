import { Routes, Route, Link, useLocation, Navigate } from "react-router-dom";
import { useState } from "react";
import { FournisseurAuth, useAuth } from "./contexte/Auth.jsx";
import MiniCalendrier from "./components/MiniCalendrier.jsx";
import Accueil from "./pages/Accueil.jsx";
import ListeRecettes from "./pages/ListeRecettes.jsx";
import MesRecettes from "./pages/MesRecettes.jsx";
import PanierCourses from "./pages/PanierCourses.jsx";
import Calendrier from "./pages/Calendrier.jsx";
import DetailRecette from "./pages/DetailRecette.jsx";
import FormulaireRecette from "./pages/FormulaireRecette.jsx";
import Connexion from "./pages/Connexion.jsx";
import Inscription from "./pages/Inscription.jsx";
import Setup from "./pages/Setup.jsx";
import { creerInvitation } from "./api.js";

// Bouton réservé à l'admin pour générer et copier un lien d'invitation.
function BoutonInviter() {
  const [message, setMessage] = useState("");

  async function genererLien() {
    try {
      const data = await creerInvitation();
      const lien = `${window.location.origin}/inscription?token=${data.token}`;
      await navigator.clipboard.writeText(lien);
      setMessage("Lien copié !");
    } catch {
      setMessage("Erreur lors de la génération.");
    }
    setTimeout(() => setMessage(""), 3000);
  }

  return (
    <span className="bouton-inviter-conteneur">
      <button onClick={genererLien} className="bouton-mes-recettes" title="Générer un lien d'invitation">
        ✉️ Inviter
      </button>
      {message && <span className="message-copie">{message}</span>}
    </span>
  );
}

// Layout principal (header + sidebar) — affiché uniquement quand l'utilisateur est connecté.
function MiseEnPage() {
  const { utilisateur, deconnexion } = useAuth();
  const location = useLocation();
  const sansSidebar = location.pathname === "/calendrier";

  return (
    <>
      <header>
        <Link to="/" className="logo">Mes Recettes</Link>
        <div className="header-actions">
          <span className="utilisateur-nom">👤 {utilisateur?.nom}</span>
          {utilisateur?.est_admin && <BoutonInviter />}
          <Link to="/mes-recettes" className="bouton-mes-recettes">🔖 Ma sélection</Link>
          <Link to="/panier" className="bouton-mes-recettes">🛒 Panier</Link>
          <button onClick={deconnexion} className="bouton-deconnexion">Déconnexion</button>
        </div>
      </header>
      <div className={`mise-en-page ${sansSidebar ? "sans-sidebar" : ""}`}>
        <main>
          <Routes>
            <Route path="/" element={<Accueil />} />
            <Route path="/calendrier" element={<Calendrier />} />
            <Route path="/mes-recettes" element={<MesRecettes />} />
            <Route path="/panier" element={<PanierCourses />} />
            <Route path="/recettes" element={<ListeRecettes />} />
            <Route path="/recettes/:categorie" element={<ListeRecettes />} />
            <Route path="/recette/:id" element={<DetailRecette />} />
            <Route path="/ajouter" element={<FormulaireRecette />} />
            <Route path="/modifier/:id" element={<FormulaireRecette />} />
          </Routes>
        </main>
        {!sansSidebar && <MiniCalendrier />}
      </div>
    </>
  );
}

// Routeur principal qui sépare les pages publiques des pages protégées.
function AppContenu() {
  const { estConnecte } = useAuth();

  return (
    <Routes>
      {/* Pages publiques : accessibles sans être connecté */}
      <Route path="/connexion" element={<Connexion />} />
      <Route path="/inscription" element={<Inscription />} />
      <Route path="/setup" element={<Setup />} />

      {/* Toutes les autres pages nécessitent d'être connecté */}
      <Route
        path="/*"
        element={estConnecte ? <MiseEnPage /> : <Navigate to="/connexion" replace />}
      />
    </Routes>
  );
}

export default function App() {
  return (
    <FournisseurAuth>
      <AppContenu />
    </FournisseurAuth>
  );
}
