// Utilitaire pour parser, regrouper et additionner les ingrédients.

const FRACTIONS = { '½': 1/2, '¾': 3/4, '⅓': 1/3, '¼': 1/4, '⅔': 2/3, '⅛': 1/8 };

// Unités reconnues, du plus long au plus court pour éviter les faux positifs.
const UNITES = [
  'sachets', 'sachet',
  'paquets', 'paquet',
  'pièces', 'pièce',
  'tranches', 'tranche',
  'gousses', 'gousse',
  'pincées', 'pincée',
  'bottes', 'botte',
  'filets', 'filet',
  'pots', 'pot',
  'kg', 'cl', 'ml', 'cs', 'cc', 'g', 'l',
];

const SINGULIERS = {
  sachets: 'sachet', paquets: 'paquet', pièces: 'pièce',
  tranches: 'tranche', gousses: 'gousse', pincées: 'pincée',
  bottes: 'botte', filets: 'filet', pots: 'pot',
};

function singulariser(u) {
  return SINGULIERS[u] || u;
}

function parseNombre(s) {
  if (!s) return null;
  let val = 0;
  let str = s.trim();
  for (const [f, v] of Object.entries(FRACTIONS)) {
    if (str.includes(f)) { val += v; str = str.replace(f, '').trim(); }
  }
  const frac = str.match(/^(\d+)\/(\d+)$/);
  if (frac) return val + parseInt(frac[1]) / parseInt(frac[2]);
  if (str === '') return val || null;
  const n = parseFloat(str.replace(',', '.'));
  return isNaN(n) ? (val || null) : val + n;
}

function formaterNombre(n) {
  if (n === null) return '';
  if (Number.isInteger(n)) return String(n);
  const entier = Math.floor(n);
  const decimal = n - entier;
  for (const [f, v] of Object.entries(FRACTIONS)) {
    if (Math.abs(decimal - v) < 0.02) return entier > 0 ? `${entier}${f}` : f;
  }
  return String(Math.round(n * 10) / 10);
}

function parseIngredient(texte) {
  let t = texte.trim();

  // 1. Extraire le nombre en début (chiffres et fractions unicode).
  const mNombre = t.match(/^([½¾⅓¼⅔⅛\d][½¾⅓¼⅔⅛\d/.,]*)/);
  if (!mNombre) {
    return { quantite: null, unite: null, nom: t.toLowerCase(), original: t };
  }

  const quantite = parseNombre(mNombre[1]);
  t = t.slice(mNombre[1].length).trim();

  // 2. Extraire l'unité (optionnelle).
  let unite = null;
  for (const u of UNITES) {
    const regex = new RegExp(`^${u}(?:\\(s\\))?\\s*`, 'i');
    if (regex.test(t)) {
      unite = singulariser(u.toLowerCase());
      t = t.replace(regex, '').trim();
      break;
    }
  }

  // 3. Supprimer la préposition "de" ou "d'" entre l'unité et le nom.
  t = t.replace(/^d[e']?\s*/i, '').trim();

  return { quantite, unite, nom: t.toLowerCase(), original: texte.trim() };
}

function elision(nom) {
  // En français : "de" devient "d'" devant une voyelle.
  return /^[aeéèêëiïîoùuyhâ]/i.test(nom) ? "d'" : "de ";
}

function reconstruire({ quantite, unite, nom }) {
  if (quantite === null) return nom;
  const q = formaterNombre(quantite);
  if (unite) return `${q} ${unite} ${elision(nom)}${nom}`;
  return `${q} ${nom}`;
}

export function grouperIngredients(recettes) {
  const map = new Map();

  recettes.forEach((recette) => {
    recette.ingredients.forEach((ing) => {
      const parsed = parseIngredient(ing);
      const cle = `${parsed.nom}|||${parsed.unite || ''}`;

      if (map.has(cle)) {
        const g = map.get(cle);
        // On additionne uniquement si les deux ont une quantité.
        if (parsed.quantite !== null && g.quantite !== null) {
          g.quantite += parsed.quantite;
        }
      } else {
        map.set(cle, { ...parsed, cle });
      }
    });
  });

  return Array.from(map.values()).map((g) => ({
    cle: g.cle,
    // Si la quantité a été additionnée, on reconstruit l'affichage.
    // Sinon on garde le texte original.
    texte: g.quantite !== null ? reconstruire(g) : g.original,
  }));
}
