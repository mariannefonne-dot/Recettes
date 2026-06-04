import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../contexte/Auth.jsx";
import { seConnecter } from "../api.js";

export default function Connexion() {
  const [email, setEmail] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [erreur, setErreur] = useState("");
  const [chargement, setChargement] = useState(false);
  const { connexion } = useAuth();
  const navigate = useNavigate();

  async function gererSoumission(e) {
    e.preventDefault();
    setErreur("");
    setChargement(true);
    try {
      const data = await seConnecter(email, motDePasse);
      connexion(data);
      navigate("/");
    } catch (err) {
      setErreur(err.message);
    } finally {
      setChargement(false);
    }
  }

  return (
    <div className="page-auth">
      <div className="carte-auth">
        <h1 className="titre-auth">🍴 Mes Recettes</h1>
        <p className="sous-titre-auth">Connectez-vous pour accéder à vos recettes</p>
        <form onSubmit={gererSoumission} className="formulaire-auth">
          <div className="champ">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div className="champ">
            <label htmlFor="mot-de-passe">Mot de passe</label>
            <input
              id="mot-de-passe"
              type="password"
              value={motDePasse}
              onChange={(e) => setMotDePasse(e.target.value)}
              required
            />
          </div>
          {erreur && <p className="erreur-auth">{erreur}</p>}
          <button type="submit" className="bouton-auth" disabled={chargement}>
            {chargement ? "Connexion…" : "Se connecter"}
          </button>
        </form>
      </div>
    </div>
  );
}
