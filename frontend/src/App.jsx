import { Routes, Route, Link, useLocation } from "react-router-dom";
import MiniCalendrier from "./components/MiniCalendrier.jsx";
import Accueil from "./pages/Accueil.jsx";
import ListeRecettes from "./pages/ListeRecettes.jsx";
import MesRecettes from "./pages/MesRecettes.jsx";
import PanierCourses from "./pages/PanierCourses.jsx";
import Calendrier from "./pages/Calendrier.jsx";
import DetailRecette from "./pages/DetailRecette.jsx";
import FormulaireRecette from "./pages/FormulaireRecette.jsx";

export default function App() {
  const location = useLocation();
  // On masque la sidebar sur le calendrier (elle prendrait trop de place).
  const sansSidebar = location.pathname === "/calendrier";

  return (
    <>
      <header>
        <Link to="/" className="logo">Mes Recettes</Link>
        <div className="header-actions">
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
        </Routes>
      </main>
      {!sansSidebar && <MiniCalendrier />}
      </div>
    </>
  );
}
