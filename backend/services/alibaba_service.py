"""
Service Alibaba - Scraping B2B
"""

import httpx
from typing import List, Optional
from models import Product
import uuid
from config import get_settings
from bs4 import BeautifulSoup
import re


class AlibabaService:
    """Service dédié au scraping Alibaba (B2B)"""
    
    def __init__(self, debug: bool = False):
        settings = get_settings()
        # Utiliser la clé dédiée Alibaba, sinon la clé par défaut
        self.scraperapi_key = settings.scraperapi_key_alibaba or settings.scraperapi_key
        self.debug = debug
        self.scraperapi_url = "https://api.scraperapi.com"
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "text/html"
        }
        
        if debug:
            print(f"✅ Alibaba Service initialisé")
            key_type = "clé dédiée Alibaba" if settings.scraperapi_key_alibaba else "clé par défaut"
            print(f"   📡 ScraperAPI: ✅ Configuré ({key_type})")
    
    async def search_products(self, keywords: List[str], max_results: int = 10) -> List[Product]:
        """Scrape Alibaba - Produits B2B avec navigation multi-pages"""
        
        if not self.scraperapi_key:
            if self.debug:
                print("⚠️ SCRAPERAPI_KEY manquante pour Alibaba")
            return []
        
        products = []
        search_query = " ".join(keywords)
        formatted_query = "+".join(search_query.split())
        
        if self.debug:
            print(f"🏭 Alibaba: Recherche '{search_query}'")
        
        # Naviguer jusqu'à 10 pages ou jusqu'à avoir max_results produits
        for page in range(1, 11):
            if len(products) >= max_results:
                break
            
            url = f"https://www.alibaba.com/trade/search?tab=all&searchText={formatted_query}&page={page}"
            
            params = {
                "api_key": self.scraperapi_key,
                "url": url,
                "render": "false"
            }
            
            try:
                if self.debug:
                    print(f"   📄 Page {page}...")
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(self.scraperapi_url, params=params)
                    
                    if self.debug:
                        print(f"   📡 Status: {response.status_code}")
                    
                    if response.status_code != 200:
                        continue
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Trouver les conteneurs de produits Alibaba
                    product_containers = soup.find_all("div", class_="search-card-info__wrapper")
                    
                    if self.debug:
                        print(f"   🔍 {len(product_containers)} items trouvés sur page {page}")
                    
                    if not product_containers:
                        break
                    
                    for container in product_containers:
                        if len(products) >= max_results:
                            break
                        
                        try:
                            # Nom et URL du produit
                            product_link = container.select_one(".search-card-e-title a")
                            if not product_link:
                                continue
                            
                            product_name_span = product_link.select_one("span")
                            product_name = product_name_span.get_text(strip=True) if product_name_span else product_link.get_text(strip=True)
                            
                            if not product_name or len(product_name) < 5:
                                continue
                            
                            # URL du produit
                            href = product_link.get("href", "")
                            if href.startswith("//"):
                                product_url = "https:" + href
                            elif href.startswith("/"):
                                product_url = "https://www.alibaba.com" + href
                            else:
                                product_url = href
                            
                            # Prix (plusieurs méthodes)
                            price = 0.0
                            price_element = container.select_one(".search-card-e-price-main")
                            if price_element:
                                price_text = price_element.get_text(" ", strip=True)
                                price = self._clean_price(price_text)
                            
                            if price == 0.0:
                                price_alt = container.select_one(".search-card-e-price")
                                if price_alt:
                                    price = self._clean_price(price_alt.get_text(" ", strip=True))
                            
                            # Description
                            description = product_name
                            description_element = container.select_one(".search-card-e-sell-point")
                            if description_element:
                                desc_text = description_element.get_text(" ", strip=True)
                                if desc_text:
                                    description = f"{product_name} - {desc_text[:100]}"
                            
                            # MOQ (Minimum Order Quantity)
                            moq = None
                            moq_element = container.select_one(".search-card-m-sale-features__item")
                            if moq_element:
                                moq = moq_element.get_text(" ", strip=True)
                            
                            # Rating
                            rating = None
                            rating_element = container.select_one(".search-card-e-review strong")
                            if rating_element:
                                try:
                                    rating = float(rating_element.get_text(strip=True))
                                except:
                                    pass
                            
                            # Image URL (méthodes multiples)
                            image_url = self._extract_image(container)
                            
                            # Filtre qualité Alibaba (accepte sans prix - B2B)
                            if len(product_name) > 10:
                                product = Product(
                                    id=str(uuid.uuid4()),
                                    name=product_name,
                                    description=description,
                                    price=price,
                                    url=product_url,
                                    image_url=image_url,
                                    rating=rating,
                                    category="product",
                                    metadata={
                                        "source": "alibaba",
                                        "moq": moq,
                                        "real_product": True,
                                        "type": "B2B"
                                    }
                                )
                                
                                products.append(product)
                                
                                if self.debug:
                                    print(f"   ✅ [{len(products)}] {product_name[:50]}... - ${price:.2f}")
                                    
                        except Exception as e:
                            if self.debug:
                                print(f"   ⚠️ Erreur item: {e}")
                            continue
                    
                    if len(products) >= max_results:
                        break
                        
            except Exception as e:
                if self.debug:
                    print(f"   ❌ Erreur page {page}: {repr(e)}")
                continue
        
        if self.debug:
            print(f"🏭 Alibaba: {len(products)} produits B2B sur {page} page(s)")
        
        return products
    
    def _extract_image(self, container) -> str:
        """Extraction d'image améliorée pour Alibaba"""
        
        # Méthode 1: Sélecteurs spécifiques
        img_selectors = [
            "img.search-card-e-slider__img",
            "img.organic-list-offer-image",
            ".search-card-e-slider img",
            ".organic-list-offer-outter img",
            "img[src*='sc04']",
            "img[src*='sc01']",
            "img[src*='sc02']",
            "img[src*='sc03']",
            "img[data-src*='sc04']",
            "img[data-src*='sc01']",
            "img[data-src*='sc02']",
            "img[data-src*='sc03']",
        ]
        
        for selector in img_selectors:
            img_elem = container.select_one(selector)
            if img_elem:
                image_url = (img_elem.get("src") or 
                           img_elem.get("data-src") or 
                           img_elem.get("data-original") or 
                           img_elem.get("data-lazy-src") or "")
                
                if image_url and not any(x in image_url.lower() for x in ['placeholder', 'loading', 'default', 'blank']):
                    if 'alicdn.com' in image_url or 'alibaba.com' in image_url:
                        if image_url.startswith("//"):
                            image_url = "https:" + image_url
                        return image_url
        
        # Méthode 2: Toutes les images CDN
        all_imgs = container.find_all("img")
        for img in all_imgs:
            img_src = (img.get("src") or img.get("data-src") or 
                     img.get("data-original") or img.get("data-lazy-src") or "")
            
            if img_src and ('alicdn.com' in img_src or 'alibaba.com' in img_src):
                if not any(x in img_src.lower() for x in ['placeholder', 'loading', 'default', 'blank', 'icon', 'logo', 'sprite']):
                    if any(size in img_src for size in ['_300x300', '_220x220', '_350x350', '960x960', '640x640', '.jpg', '.png', '.webp']):
                        if img_src.startswith("//"):
                            img_src = "https:" + img_src
                        return img_src
        
        # Fallback: placeholder
        return "https://via.placeholder.com/300x300?text=Alibaba+Product"
    
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