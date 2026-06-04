import { useState } from "react";
import { useAuth } from "../contexte/Auth.jsx";
import { creerInvitation } from "../api.js";

export default function Compte() {
  const { utilisateur, deconnexion } = useAuth();
  const [lienInvitation, setLienInvitation] = useState("");
  const [copie, setCopie] = useState(false);
  const [erreur, setErreur] = useState("");

  async function genererInvitation() {
    setErreur("");
    setCopie(false);
    try {
      const data = await creerInvitation();
      const lien = `${window.location.origin}/inscription?token=${data.token}`;
      setLienInvitation(lien);
    } catch (err) {
      setErreur(err.message);
    }
  }

  async function copierLien() {
    await navigator.clipboard.writeText(lienInvitation);
    setCopie(true);
    setTimeout(() => setCopie(false), 3000);
  }

  return (
    <div className="page-compte">
      <h1>Mon compte</h1>

      <section className="carte-compte">
        <h2>Informations</h2>
        <div className="info-ligne">
          <span className="info-label">Prénom</span>
          <span>{utilisateur?.nom}</span>
        </div>
        <div className="info-ligne">
          <span className="info-label">Email</span>
          <span>{utilisateur?.email}</span>
        </div>
        <div className="info-ligne">
          <span className="info-label">Rôle</span>
          <span>{utilisateur?.est_admin ? "Administrateur" : "Membre"}</span>
        </div>
        <button onClick={deconnexion} className="bouton-supprimer" style={{ marginTop: "1rem" }}>
          Se déconnecter
        </button>
      </section>

      {utilisateur?.est_admin && (
        <section className="carte-compte">
          <h2>Inviter quelqu'un</h2>
          <p className="texte-invitation">
            Génère un lien unique à envoyer à un proche. Ce lien lui permettra de créer son propre compte. Il n'est utilisable qu'une seule fois.
          </p>
          <button onClick={genererInvitation} className="bouton-sauvegarder">
            Générer un lien d'invitation
          </button>

          {erreur && <p className="erreur" style={{ marginTop: "0.75rem" }}>{erreur}</p>}

          {lienInvitation && (
            <div className="bloc-lien-invitation">
              <input
                type="text"
                readOnly
                value={lienInvitation}
                className="champ-lien-invitation"
                onClick={(e) => e.target.select()}
              />
              <button onClick={copierLien} className="bouton-copier">
                {copie ? "✅ Copié !" : "📋 Copier"}
              </button>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
