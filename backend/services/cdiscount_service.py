"""
Service Cdiscount - Scraping avec Firecrawl
Même code que Walmart mais avec URL Cdiscount
"""

from firecrawl import FirecrawlApp
from typing import List, Optional
from models import Product
import uuid
from config import get_settings
import json
import asyncio  # ⚡ Ajouté pour asyncio.to_thread()


class CdiscountService:
    """Service dédié au scraping Cdiscount avec Firecrawl"""
    
    def __init__(self, debug: bool = False):
        settings = get_settings()
        # 🔐 CLÉ API FIRECRAWL - Utiliser la clé dédiée Cdiscount, sinon la clé par défaut
        api_key = settings.firecrawl_api_key_cdiscount or settings.firecrawl_api_key
        
        # Initialize Firecrawl only if API key is provided
        if api_key:
            self.app = FirecrawlApp(api_key=api_key)
        else:
            self.app = None
            if debug:
                print(f"⚠️ Cdiscount Service: No Firecrawl API key - service disabled")
        
        self.debug = debug
        
        if debug and self.app:
        self.app = FirecrawlApp(api_key=api_key)
        self.debug = debug
        
        if debug:
            print(f"✅ Cdiscount Service initialisé")
            key_type = "clé dédiée Cdiscount" if settings.firecrawl_api_key_cdiscount else "clé par défaut"
            print(f"   🔥 Firecrawl: ✅ Configuré ({key_type})")
    
    async def search_products(self, keywords: List[str], max_results: int = 10) -> List[Product]:
        """Scrape Cdiscount - Produits B2C avec Firecrawl"""
        
        if not self.app:
            if self.debug:
                print("⚠️ Firecrawl API Key manquante pour Cdiscount")
            return []
        
        search_query = " ".join(keywords)
        
        # 🔄 Nettoyage : espaces → +
        product_name = search_query.strip().replace(" ", "+")
        
        # 🔗 Construire l'URL Cdiscount
        PRODUCT_URL = f"https://www.cdiscount.com/search/10/{product_name}.html"
        
        if self.debug:
            print(f"🛒 Cdiscount: Recherche '{search_query}'")
            print(f"   🔗 URL: {PRODUCT_URL}")
        
        try:
            if self.debug:
                print(f"   🔥 Lancement Firecrawl extract()...")
            
            # 🔍 EXTRACTION FIRECRAWL
            # ⚡ IMPORTANT: Exécuter dans un thread pour ne pas bloquer l'event loop
            result = await asyncio.to_thread(
                self.app.extract,
                urls=[PRODUCT_URL],
                prompt="""Extract a 3 product information from this Cdiscount product page.
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
            
            # ✅ RÉCUPÉRATION DES DONNÉES
            if not result.data:
                if self.debug:
                    print("   ❌ Aucune donnée retournée par Firecrawl")
                return []
            
            product_data = result.data
            
            if self.debug:
                print(f"   📊 Type données: {type(product_data)}")
                if isinstance(product_data, dict):
                    print(f"   📊 Clés: {list(product_data.keys())}")
            
            # Convertir en objets Product
            products = self._parse_cdiscount_products(product_data, max_results)
            
            if self.debug:
                print(f"🛒 Cdiscount: {len(products)} produits B2C")
            
            return products
            
        except Exception as e:
            if self.debug:
                print(f"❌ Erreur Cdiscount: {repr(e)}")
                import traceback
                print(f"   Traceback: {traceback.format_exc()}")
            return []
    
    def _parse_cdiscount_products(self, data, max_results: int) -> List[Product]:
        """Parse les données Cdiscount en objets Product"""
        
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
                    name = item.get('product_name', item.get('name', 'Produit Cdiscount'))
                    price_str = item.get('price', '0')
                    currency = item.get('currency', 'EUR')
                    url = item.get('product_url', item.get('url', ''))
                    image_url = item.get('main_image_url', item.get('image', ''))
                    description = item.get('description', name)
                    availability = item.get('availability', 'Unknown')
                    brand = item.get('brand', 'Cdiscount')
                    
                    # Nettoyer le prix
                    price = self._clean_price(price_str)
                    
                    # Créer le produit
                    if len(name) > 5:  # Filtre qualité
                        product = Product(
                            id=str(uuid.uuid4()),
                            name=name,
                            description=f"{description} - {brand}",
                            price=price,
                            url=url if url.startswith('http') else f"https://www.cdiscount.com{url}",
                            image_url=image_url,
                            rating=None,
                            category="product",
                            metadata={
                                "source": "cdiscount",
                                "brand": brand,
                                "availability": availability,
                                "currency": currency,
                                "real_product": True,
                                "type": "B2C"
                            }
                        )
                        
                        products.append(product)
                        
                        if self.debug:
                            print(f"   ✅ [{len(products)}] {name[:50]}... - {price:.2f}€")
                
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
            text = text.replace(',', '.').replace('€', '').replace('EUR', '').replace('$', '').replace('USD', '')
            text = text.replace(' ', '')
            
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
