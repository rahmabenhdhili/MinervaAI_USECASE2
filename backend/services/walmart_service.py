"""
Service Walmart - Scraping avec Firecrawl
Utilise extract() comme dans le code fonctionnel
"""

from firecrawl import FirecrawlApp
from typing import List, Optional
from models import Product
import uuid
from config import get_settings
import json
import asyncio  # ⚡ Ajouté pour asyncio.to_thread()


class WalmartService:
    """Service dédié au scraping Walmart avec Firecrawl"""
    
    def __init__(self, debug: bool = False):
        settings = get_settings()
        # 🔐 CLÉ API FIRECRAWL - Utiliser la clé dédiée Walmart, sinon la clé par défaut
        api_key = settings.firecrawl_api_key_walmart or settings.firecrawl_api_key
        self.app = FirecrawlApp(api_key=api_key)
        self.debug = debug
        
        if debug:
            print(f"✅ Walmart Service initialisé")
            key_type = "clé dédiée Walmart" if settings.firecrawl_api_key_walmart else "clé par défaut"
            print(f"   🔥 Firecrawl: ✅ Configuré ({key_type})")
    
    def _translate_to_english(self, query: str) -> str:
        """Traduit les termes français courants en anglais pour Walmart"""
        translations = {
            # Électronique
            "ordinateur": "laptop",
            "ordinateurs": "laptops",
            "portable": "laptop",
            "portables": "laptops",
            "téléphone": "phone",
            "telephone": "phone",
            "téléphones": "phones",
            "telephones": "phones",
            "smartphone": "smartphone",
            "smartphones": "smartphones",
            "tablette": "tablet",
            "tablettes": "tablets",
            "écouteurs": "headphones",
            "ecouteurs": "headphones",
            "casque": "headphones",
            "casques": "headphones",
            "souris": "mouse",
            "clavier": "keyboard",
            "claviers": "keyboards",
            "moniteur": "monitor",
            "moniteurs": "monitors",
            "écran": "screen",
            "ecran": "screen",
            "caméra": "camera",
            "camera": "camera",
            "appareil photo": "camera",
            
            # Mots communs
            "pour": "for",
            "avec": "with",
            "sans": "without",
            "fil": "wire",
            "gaming": "gaming",
            "jeu": "gaming",
            "jeux": "gaming",
            "travail": "work",
            "bureau": "office",
        }
        
        # Convertir en minuscules pour la comparaison
        query_lower = query.lower().strip()
        
        # Traduction directe si le terme existe
        if query_lower in translations:
            translated = translations[query_lower]
            if self.debug:
                print(f"   🌐 Traduction: '{query}' → '{translated}'")
            return translated
        
        # Traduction mot par mot
        words = query_lower.split()
        translated_words = []
        for word in words:
            if word in translations:
                translated_words.append(translations[word])
            else:
                translated_words.append(word)
        
        translated = " ".join(translated_words)
        
        if translated != query_lower and self.debug:
            print(f"   🌐 Traduction: '{query}' → '{translated}'")
        
        return translated
    
    async def search_products(self, keywords: List[str], max_results: int = 10) -> List[Product]:
        """Scrape Walmart - Produits B2C avec Firecrawl (CODE 100% FONCTIONNEL)"""
        
        if not self.app:
            if self.debug:
                print("⚠️ Firecrawl API Key manquante pour Walmart")
            return []
        
        search_query = " ".join(keywords)
        
        # 🌐 Traduction automatique français → anglais (Walmart est en anglais)
        search_query_en = self._translate_to_english(search_query)
        
        # 🔄 Nettoyage : espaces → +
        product_name = search_query_en.strip().replace(" ", "+")
        
        # 🔗 Construire l'URL Walmart (avec .html)
        PRODUCT_URL = f"https://www.walmart.com/search?q={product_name}"
        
        if self.debug:
            print(f"🛍️ Walmart: Recherche '{search_query}' → '{search_query_en}'")
            print(f"   🔗 URL: {PRODUCT_URL}")
        
        try:
            if self.debug:
                print(f"   🔥 Lancement Firecrawl extract()...")
            
            # 🔍 EXTRACTION FIRECRAWL (CODE UTILISATEUR)
            # ⚡ IMPORTANT: Exécuter dans un thread pour ne pas bloquer l'event loop
            result = await asyncio.to_thread(
                self.app.extract,
                urls=[PRODUCT_URL],
                prompt="""Extract a 3 product information from this Walmart product page.
Return clean JSON with:
- product_name
- price
- currency
- product_url
- main_image_url
- description
- availability
- brand"""
            )
            
            if self.debug:
                print(f"   📡 Firecrawl: Extraction terminée")
            
            # ✅ RÉCUPÉRATION DES DONNÉES (1 URL → result.data est un dict)
            if not result.data:
                if self.debug:
                    print("   ❌ Aucune donnée retournée par Firecrawl")
                return []
            
            product_data = result.data  # ✅ PAS [0]
            
            if self.debug:
                print(f"   📊 Type données: {type(product_data)}")
                if isinstance(product_data, dict):
                    print(f"   📊 Clés: {list(product_data.keys())}")
            
            # Convertir en objets Product
            products = self._parse_walmart_products(product_data, max_results)
            
            if self.debug:
                print(f"🛍️ Walmart: {len(products)} produits B2C")
            
            return products
            
        except Exception as e:
            if self.debug:
                print(f"❌ Erreur Walmart: {repr(e)}")
                import traceback
                print(f"   Traceback: {traceback.format_exc()}")
            return []
    
    def _parse_walmart_products(self, data, max_results: int) -> List[Product]:
        """Parse les données Walmart en objets Product"""
        
        products = []
        
        try:
            # Si data contient une liste de produits
            if isinstance(data, dict) and 'products' in data:
                product_list = data['products']
            elif isinstance(data, list):
                product_list = data
            else:
                # Si c'est un seul produit
                product_list = [data]
            
            for item in product_list[:max_results]:
                try:
                    # Extraction des champs (avec fallbacks)
                    name = item.get('product_name', item.get('name', 'Produit Walmart'))
                    price_str = item.get('price', '0')
                    currency = item.get('currency', 'USD')
                    url = item.get('product_url', item.get('url', ''))
                    image_url = item.get('main_image_url', item.get('image', ''))
                    description = item.get('description', name)
                    availability = item.get('availability', 'Unknown')
                    brand = item.get('brand', 'Walmart')
                    
                    # Nettoyer le prix
                    price = self._clean_price(price_str)
                    
                    # Créer le produit
                    if len(name) > 5:  # Filtre qualité
                        product = Product(
                            id=str(uuid.uuid4()),
                            name=name,
                            description=f"{description} - {brand}",
                            price=price,
                            url=url if url.startswith('http') else f"https://www.walmart.com{url}",
                            image_url=image_url,
                            rating=None,  # Walmart rating pas dans le prompt
                            category="product",
                            metadata={
                                "source": "walmart",
                                "brand": brand,
                                "availability": availability,
                                "currency": currency,
                                "real_product": True,
                                "type": "B2C"
                            }
                        )
                        
                        products.append(product)
                        
                        if self.debug:
                            print(f"   ✅ [{len(products)}] {name[:50]}... - ${price:.2f}")
                
                except Exception as e:
                    if self.debug:
                        print(f"   ⚠️ Erreur item: {e}")
                    continue
        
        except Exception as e:
            if self.debug:
                print(f"   ❌ Erreur parsing: {e}")
        
        return products
    
    def _clean_price(self, value) -> float:
        """Nettoie et convertit un prix"""
        if not value:
            return 0.0
        
        try:
            # Supprimer symboles et texte
            text = str(value).strip()
            text = text.replace(',', '').replace('$', '').replace('€', '').replace('¥', '').replace('£', '')
            text = text.replace('USD', '').replace('EUR', '').replace('CNY', '').replace('CAD', '')
            
            # Extraire le premier nombre
            import re
            numbers = re.findall(r'\d+\.?\d*', text)
            if numbers:
                price = float(numbers[0])
                if 0.01 < price < 1000000:
                    return price
        except:
            pass
        
        return 0.0
