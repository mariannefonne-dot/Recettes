import { Routes, Route, Link, useLocation, Navigate } from "react-router-dom";
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
import Compte from "./pages/Compte.jsx";

// Layout principal (header + sidebar) — affiché uniquement quand l'utilisateur est connecté.
function MiseEnPage() {
  const { utilisateur } = useAuth();
  const location = useLocation();
  const sansSidebar = location.pathname === "/calendrier";

  return (
    <>
      <header>
        <Link to="/" className="logo">Mes Recettes</Link>
        <div className="header-actions">
          <Link to="/compte" className="utilisateur-nom-lien">👤 {utilisateur?.nom}</Link>
          <Link to="/mes-recettes" className="bouton-mes-recettes">🔖 Ma sélection</Link>
          <Link to="/panier" className="bouton-mes-recettes">🛒 Panier</Link>
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
            <Route path="/compte" element={<Compte />} />
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
