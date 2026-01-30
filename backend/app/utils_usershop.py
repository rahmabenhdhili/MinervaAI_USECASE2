"""
Utilitaires pour le système Usershop
"""
import re

def normalize_price_display(price_str: str) -> str:
    """
    Normalise l'affichage du prix en remplaçant toutes les devises par TND
    Sans conversion de valeur - juste remplacement du symbole
    
    Exemples:
        "50€" -> "50 TND"
        "$100" -> "100 TND"
        "75 EUR" -> "75 TND"
        "1000" -> "1000 TND"
    """
    if not price_str:
        return "0 TND"
    
    # Convertir en string
    price_str = str(price_str).strip()
    
    # Remplacer les symboles de devises par TND
    # Liste des symboles et codes de devises à remplacer
    currencies = [
        '€', 'EUR', 'euro', 'euros',
        '$', 'USD', 'dollar', 'dollars',
        '£', 'GBP', 'pound', 'pounds',
        '¥', 'JPY', 'yen',
        'DT', 'TND'  # Dinar Tunisien déjà présent
    ]
    
    # Nettoyer le prix
    clean_price = price_str
    
    # Remplacer chaque devise par rien (on va ajouter TND à la fin)
    for currency in currencies:
        clean_price = clean_price.replace(currency, '')
    
    # Nettoyer les espaces multiples
    clean_price = ' '.join(clean_price.split())
    clean_price = clean_price.strip()
    
    # Si le prix est vide après nettoyage, retourner 0 TND
    if not clean_price or clean_price == '':
        return "0 TND"
    
    # Ajouter TND à la fin si pas déjà présent
    if 'TND' not in price_str.upper():
        return f"{clean_price} TND"
    
    return clean_price

def format_price_for_display(price_numeric: float) -> str:
    """
    Formate un prix numérique pour l'affichage en TND
    
    Exemple:
        50.5 -> "50.50 TND"
        1000 -> "1000.00 TND"
    """
    return f"{price_numeric:.2f} TND"
