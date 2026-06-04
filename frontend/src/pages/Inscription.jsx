import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../contexte/Auth.jsx";
import { sInscrire } from "../api.js";

export default function Inscription() {
  const [searchParams] = useSearchParams();
  const tokenInvitation = searchParams.get("token") || "";

  const [email, setEmail] = useState("");
  const [nom, setNom] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [erreur, setErreur] = useState("");
  const [chargement, setChargement] = useState(false);
  const { connexion } = useAuth();
  const navigate = useNavigate();

  if (!tokenInvitation) {
    return (
      <div className="page-auth">
        <div className="carte-auth">
          <p className="erreur-auth">Lien d'invitation invalide ou manquant.</p>
        </div>
      </div>
    );
  }

  async function gererSoumission(e) {
    e.preventDefault();
    setErreur("");
    setChargement(true);
    try {
      const data = await sInscrire(tokenInvitation, email, nom, motDePasse);
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
        <p className="sous-titre-auth">Créez votre compte</p>
        <form onSubmit={gererSoumission} className="formulaire-auth">
          <div className="champ">
            <label htmlFor="nom">Prénom</label>
            <input
              id="nom"
              type="text"
              value={nom}
              onChange={(e) => setNom(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div className="champ">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="champ">
            <label htmlFor="mot-de-passe">Mot de passe (6 caractères min.)</label>
            <input
              id="mot-de-passe"
              type="password"
              value={motDePasse}
              onChange={(e) => setMotDePasse(e.target.value)}
              required
              minLength={6}
            />
          </div>
          {erreur && <p className="erreur-auth">{erreur}</p>}
          <button type="submit" className="bouton-auth" disabled={chargement}>
            {chargement ? "Création…" : "Créer mon compte"}
          </button>
        </form>
      </div>
    </div>
  );
}
