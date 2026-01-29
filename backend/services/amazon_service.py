"""
Service Amazon - Scraping B2C
"""

import httpx
from typing import List, Optional
from models import Product
import uuid
from config import get_settings
from bs4 import BeautifulSoup
import re


class AmazonService:
    """Service dédié au scraping Amazon (B2C)"""
    
    def __init__(self, debug: bool = False):
        settings = get_settings()
        # Utiliser la clé dédiée Amazon, sinon la clé par défaut
        self.scraperapi_key = settings.scraperapi_key_amazon or settings.scraperapi_key
        self.debug = debug
        self.scraperapi_url = "https://api.scraperapi.com"
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "text/html"
        }
        
        if debug:
            print(f"✅ Amazon Service initialisé")
            key_type = "clé dédiée Amazon" if settings.scraperapi_key_amazon else "clé par défaut"
            print(f"   📡 ScraperAPI: ✅ Configuré ({key_type})")
    
    async def search_products(self, keywords: List[str], max_results: int = 10) -> List[Product]:
        """Scrape Amazon - Produits B2C"""
        
        if not self.scraperapi_key:
            if self.debug:
                print("⚠️ SCRAPERAPI_KEY manquante pour Amazon")
            return []
        
        search_query = " ".join(keywords)
        url = f"https://www.amazon.com/s?k={search_query.replace(' ', '+')}"
        
        params = {
            "api_key": self.scraperapi_key,
            "url": url,
            "render": "false"
        }
        
        try:
            if self.debug:
                print(f"🛒 Amazon: Recherche '{search_query}'")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.scraperapi_url, params=params)
                
                if self.debug:
                    print(f"   📡 Status: {response.status_code}")
                
                if response.status_code != 200:
                    return []
                
                soup = BeautifulSoup(response.text, 'html.parser')
                products = []
                
                items = soup.find_all('div', {'data-asin': True})
                items = [i for i in items if i.get('data-asin') and len(i.get('data-asin')) > 5]
                
                if self.debug:
                    print(f"   🔍 {len(items)} items trouvés")
                
                for item in items[:max_results + 10]:
                    try:
                        asin = item.get('data-asin', '').strip()
                        if not asin or len(asin) < 5:
                            continue
                        
                        # Titre
                        title_elem = item.find('h2')
                        if not title_elem:
                            continue
                        title = title_elem.get_text(strip=True)
                        
                        if not title or len(title) < 5:
                            continue
                        
                        # Prix
                        price = 0.0
                        price_whole = item.find('span', class_='a-price-whole')
                        if price_whole:
                            price = self._clean_price(price_whole.get_text())
                        
                        if price == 0.0:
                            price_offscreen = item.find('span', class_='a-offscreen')
                            if price_offscreen:
                                price = self._clean_price(price_offscreen.get_text())
                        
                        if price == 0.0:
                            price_span = item.find('span', class_='a-price')
                            if price_span:
                                price = self._clean_price(price_span.get_text())
                        
                        # Image
                        image_url = ""
                        img_elem = item.find('img', class_='s-image')
                        if img_elem:
                            image_url = img_elem.get('src', '')
                        
                        # Rating
                        rating = None
                        rating_elem = item.find('span', class_='a-icon-alt')
                        if rating_elem:
                            rating_text = rating_elem.get_text()
                            match = re.search(r'(\d+\.?\d*)', rating_text)
                            if match:
                                try:
                                    rating = float(match.group(1))
                                except:
                                    pass
                        
                        # Filtre qualité Amazon (exige un prix)
                        if price > 0 and len(title) > 10:
                            product = Product(
                                id=str(uuid.uuid4()),
                                name=title,
                                description=f"{title} - Amazon Product",
                                price=price,
                                url=f"https://www.amazon.com/dp/{asin}",
                                image_url=image_url,
                                rating=rating,
                                category="product",
                                metadata={
                                    "source": "amazon",
                                    "asin": asin,
                                    "real_product": True,
                                    "type": "B2C"
                                }
                            )
                            
                            products.append(product)
                            
                            if self.debug:
                                print(f"   ✅ [{len(products)}] {title[:50]}... - ${price:.2f}")
                            
                            if len(products) >= max_results:
                                break
                                
                    except Exception as e:
                        if self.debug:
                            print(f"   ⚠️ Erreur item: {e}")
                        continue
                
                if self.debug:
                    print(f"🛒 Amazon: {len(products)} produits B2C")
                
                return products
                
        except Exception as e:
            if self.debug:
                print(f"❌ Erreur Amazon: {repr(e)}")
            return []
    
    def _clean_price(self, value) -> float:
        """Nettoie et convertit un prix"""
        if not value:
            return 0.0
        
        try:
            text = str(value).strip()
            text = text.replace(',', '').replace('$', '').replace('€', '').replace('¥', '').replace('£', '')
            text = text.replace('US', '').replace('USD', '').replace('EUR', '').replace('CNY', '')
            
            import re
            numbers = re.findall(r'\d+\.?\d*', text)
            if numbers:
                price = float(numbers[0])
                if 0.01 < price < 1000000:
                    return price
        except:
            pass
        
        return 0.0