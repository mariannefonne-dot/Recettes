import { createContext, useContext, useState } from "react";

const ContexteAuth = createContext(null);

export function FournisseurAuth({ children }) {
  // On relit le token et l'utilisateur depuis localStorage au démarrage.
  const [token, setToken] = useState(() => localStorage.getItem("token") || null);
  const [utilisateur, setUtilisateur] = useState(() => {
    const sauvegarde = localStorage.getItem("utilisateur");
    return sauvegarde ? JSON.parse(sauvegarde) : null;
  });

  function connexion({ token: t, utilisateur: u }) {
    localStorage.setItem("token", t);
    localStorage.setItem("utilisateur", JSON.stringify(u));
    setToken(t);
    setUtilisateur(u);
  }

  function deconnexion() {
    localStorage.removeItem("token");
    localStorage.removeItem("utilisateur");
    setToken(null);
    setUtilisateur(null);
  }

  return (
    <ContexteAuth.Provider value={{ token, utilisateur, connexion, deconnexion, estConnecte: !!token }}>
      {children}
    </ContexteAuth.Provider>
  );
}

export function useAuth() {
  return useContext(ContexteAuth);
}
