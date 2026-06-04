import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// En développement, le front et le backend tournent sur des ports différents.
// Le proxy redirige les appels /api et /static vers le backend Flask, ce qui
// évite les problèmes de CORS et permet d'utiliser des URLs relatives partout.
// VITE_PROXY_TARGET vaut le nom du service Docker (backend) ou localhost en local.
const cible = process.env.VITE_PROXY_TARGET || "http://localhost:5000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": cible,
      "/static": cible,
    },
  },
});
