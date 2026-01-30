/**
 * Utilitaires pour la gestion des devises
 * Normalise l'affichage des prix en TND
 */

/**
 * Normalise l'affichage d'un prix en remplaçant toutes les devises par TND
 * Sans conversion - juste remplacement du symbole
 * 
 * @param {string} priceStr - Prix avec devise (ex: "50€", "$100", "75 EUR")
 * @returns {string} Prix normalisé en TND (ex: "50 TND")
 */
export const normalizePriceDisplay = (priceStr) => {
  if (!priceStr) return '0 TND';

  // Convertir en string
  let price = String(priceStr).trim();

  // Liste des symboles et codes de devises à remplacer
  const currencies = [
    '€', 'EUR', 'euro', 'euros',
    '$', 'USD', 'dollar', 'dollars',
    '£', 'GBP', 'pound', 'pounds',
    '¥', 'JPY', 'yen',
    'DT'
  ];

  // Remplacer chaque devise par rien
  currencies.forEach(currency => {
    price = price.replace(new RegExp(currency, 'gi'), '');
  });

  // Nettoyer les espaces multiples
  price = price.replace(/\s+/g, ' ').trim();

  // Si vide après nettoyage
  if (!price || price === '') return '0 TND';

  // Si TND déjà présent, retourner tel quel
  if (priceStr.toUpperCase().includes('TND')) {
    return price.includes('TND') ? price : `${price} TND`;
  }

  // Ajouter TND
  return `${price} TND`;
};

/**
 * Formate un prix numérique pour l'affichage en TND
 * 
 * @param {number} priceNum - Prix numérique
 * @returns {string} Prix formaté (ex: "50.00 TND")
 */
export const formatPriceForDisplay = (priceNum) => {
  if (typeof priceNum !== 'number') {
    priceNum = parseFloat(priceNum) || 0;
  }
  return `${priceNum.toFixed(2)} TND`;
};

/**
 * Extrait la valeur numérique d'un prix
 * 
 * @param {string} priceStr - Prix avec devise
 * @returns {number} Valeur numérique
 */
export const extractPriceValue = (priceStr) => {
  if (!priceStr) return 0;

  // Nettoyer et extraire le nombre
  const cleaned = String(priceStr)
    .replace(/[€$£¥]/g, '')
    .replace(/[A-Za-z]/g, '')
    .replace(',', '.')
    .trim();
  
  const match = cleaned.match(/\d+\.?\d*/);
  return match ? parseFloat(match[0]) : 0;
};