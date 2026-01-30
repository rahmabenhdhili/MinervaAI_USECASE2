"""
Weekly web scraper for supermarket products using crawl4ai.
Extracts product images and prices from supermarket websites.
Stores data in SQLite database.
"""
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from PIL import Image
import requests
from io import BytesIO
import re
from datetime import datetime
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
from pathlib import Path
import hashlib

# Import database
from data_pipeline.product_database import product_db

# Browser configuration for crawl4ai
browser_config = BrowserConfig(
    browser_type="chromium",
    headless=True,
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    extra_args=[
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-blink-features=AutomationControlled",
    ],
)

class SupermarketScraper:
    """
    Scrapes supermarket websites for product data.
    Designed to run weekly to update discount/promo data.
    """
    
    def __init__(self):
        self.scraped_data = {}
        self.last_scrape_time = None
    
    def is_allowed_by_robots(self, url: str, user_agent: str = "*") -> bool:
        """Check if URL is allowed by robots.txt"""
        # Skip robots.txt check for demo purposes
        # In production, implement proper robots.txt checking with timeout
        return True
    
    async def scrape_aziza_online(self) -> List[Dict[str, Any]]:
        """
        Scrape Aziza online store (Angular SPA - requires JS rendering).
        Aziza uses Angular with infinite scroll pagination.
        URL: https://www.aziza.tn/promotions
        """
        products = []
        url = "https://www.aziza.tn/promotions"
        
        try:
            if not self.is_allowed_by_robots(url):
                print(f"  ⚠️ Blocked by robots.txt: {url}")
                return products
            
            print(f"  Crawling {url} (JS rendering + scrolling)...")
            
            # Aziza-specific browser config with JS rendering
            aziza_browser_config = BrowserConfig(
                browser_type="chromium",
                headless=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                extra_args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            
            async with AsyncWebCrawler(config=aziza_browser_config) as crawler:
                result = await crawler.arun(
                    url=url,
                    config=CrawlerRunConfig(
                        cache_mode=CacheMode.BYPASS,
                        session_id="aziza_scrape",
                        js_code=[
                            # Wait for Angular to load
                            "await new Promise(r => setTimeout(r, 3000));",
                            # Scroll to load more products (infinite scroll)
                            """
                            for (let i = 0; i < 5; i++) {
                                window.scrollTo(0, document.body.scrollHeight);
                                await new Promise(r => setTimeout(r, 2000));
                            }
                            """
                        ],
                        wait_for="css:div.article-block",
                        page_timeout=60000,
                    )
                )
                
                if not result.success or not result.html:
                    print(f"  ❌ Failed to fetch page")
                    return products
                
                soup = BeautifulSoup(result.html, 'html.parser')
                
                # Aziza uses div.article-block for each product
                product_cards = soup.find_all('div', class_='article-block')
                
                print(f"  Found {len(product_cards)} product cards")
                
                for card in product_cards[:100]:  # Limit to 100 products
                    try:
                        # Extract product name (.article-title)
                        name_elem = card.find(class_='article-title')
                        name = name_elem.text.strip() if name_elem else None
                        
                        # Extract brand (.article-marque)
                        brand_elem = card.find(class_='article-marque')
                        brand = brand_elem.text.strip() if brand_elem else ""
                        
                        # Extract quantity (.article-quantity)
                        quantity_elem = card.find(class_='article-quantity')
                        quantity = quantity_elem.text.strip() if quantity_elem else ""
                        
                        # Extract price (split into integer and decimal)
                        price_integer_elem = card.find(class_='price-integer')
                        price_decimal_elem = card.find(class_='price-decimal')
                        
                        price = None
                        if price_integer_elem and price_decimal_elem:
                            # Aziza splits price: "10," + "990" → 10.990 TND
                            integer_part = price_integer_elem.text.strip().replace(',', '').replace('.', '')
                            decimal_part = price_decimal_elem.text.strip()
                            try:
                                price = float(f"{integer_part}.{decimal_part}")
                            except ValueError:
                                pass
                        
                        # Extract currency (.price-currency)
                        currency_elem = card.find(class_='price-currency')
                        currency = currency_elem.text.strip() if currency_elem else "TND"
                        
                        # Extract promo percentage (optional, .promo-badge)
                        promo_elem = card.find(class_='promo-badge')
                        promo_percent = promo_elem.text.strip() if promo_elem else None
                        
                        # Extract image URL (img.fade-in-image)
                        img_elem = card.find('img', class_='fade-in-image')
                        img_url = None
                        if img_elem:
                            img_url = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('ng-src')
                        
                        # Download image
                        product_image = None
                        if img_url:
                            if not img_url.startswith('http'):
                                img_url = f"https://www.aziza.tn{img_url}"
                            
                            try:
                                img_response = requests.get(img_url, timeout=10)
                                if img_response.status_code == 200:
                                    product_image = Image.open(BytesIO(img_response.content))
                            except Exception as e:
                                print(f"    ⚠️ Failed to download image: {e}")
                        
                        # Build full product name with brand and quantity
                        full_name = name
                        if brand:
                            full_name = f"{brand} {name}"
                        if quantity:
                            full_name = f"{full_name} {quantity}"
                        
                        if name and price and product_image:
                            product_data = {
                                "name": full_name,
                                "price": price,
                                "market": "aziza",
                                "description": full_name,
                                "category": "food",
                                "image": product_image,
                                "image_url": img_url,
                                "brand": brand,
                                "quantity": quantity,
                                "scraped_at": datetime.now().isoformat()
                            }
                            
                            # Add promo info if available
                            if promo_percent:
                                product_data["promo"] = promo_percent
                            
                            products.append(product_data)
                    
                    except Exception as e:
                        continue
        
        except Exception as e:
            print(f"  ❌ Error scraping Aziza: {e}")
        
        return products
    
    async def scrape_mg_tunisia(self) -> List[Dict[str, Any]]:
        """
        Scrape MG Tunisia online store (traditional HTML with pagination).
        MG uses PrestaShop with standard pagination.
        URL: https://mg.tn/15-alimentaire
        """
        products = []
        base_url = "https://mg.tn"
        
        # Multiple category URLs to scrape
        category_urls = [
            "https://mg.tn/15-alimentaire",  # Food category
            "https://mg.tn/57-fraicheur-et-qualite",  # Fresh products
        ]
        
        try:
            async with AsyncWebCrawler(config=browser_config) as crawler:
                for category_url in category_urls:
                    if not self.is_allowed_by_robots(category_url):
                        print(f"  ⚠️ Blocked by robots.txt: {category_url}")
                        continue
                    
                    print(f"  Crawling {category_url}...")
                    
                    # Pagination: follow up to 3 pages per category
                    current_url = category_url
                    page_count = 0
                    max_pages = 3
                    
                    while current_url and page_count < max_pages:
                        page_count += 1
                        print(f"    Page {page_count}...")
                        
                        result = await crawler.arun(
                            url=current_url,
                            config=CrawlerRunConfig(
                                cache_mode=CacheMode.BYPASS,
                                session_id=f"mg_scrape_page_{page_count}",
                                wait_for="css:article.product-miniature",
                                page_timeout=30000,
                            )
                        )
                        
                        if not result.success or not result.html:
                            print(f"    ❌ Failed to fetch page {page_count}")
                            break
                        
                        soup = BeautifulSoup(result.html, 'html.parser')
                        
                        # MG uses article.product-miniature for each product
                        product_cards = soup.find_all('article', class_='product-miniature')
                        
                        print(f"    Found {len(product_cards)} products on page {page_count}")
                        
                        for card in product_cards:
                            try:
                                # Extract product name (h2.product-title a)
                                name_elem = card.find('h2', class_='product-title')
                                if name_elem:
                                    name_link = name_elem.find('a')
                                    name = name_link.text.strip() if name_link else None
                                    product_url = name_link.get('href') if name_link else None
                                else:
                                    name = None
                                    product_url = None
                                
                                # Extract category (div.product-category-name)
                                category_elem = card.find('div', class_='product-category-name')
                                category = category_elem.text.strip() if category_elem else "food"
                                
                                # Extract price (div.price-amount)
                                price_elem = card.find('div', class_='price-amount')
                                price = None
                                if price_elem:
                                    # Look for price-first-part and price-second-part
                                    first_part = price_elem.find(class_='price-first-part')
                                    second_part = price_elem.find(class_='price-second-part')
                                    
                                    if first_part and second_part:
                                        # Combine parts: "12" + "500" → 12.500 TND
                                        try:
                                            first = first_part.text.strip().replace(',', '.')
                                            second = second_part.text.strip()
                                            price = float(f"{first}.{second}")
                                        except ValueError:
                                            pass
                                    else:
                                        # Fallback: parse entire price text
                                        price_text = price_elem.text.strip()
                                        price_match = re.search(r'(\d+)[.,\s]*(\d+)?', price_text)
                                        if price_match:
                                            dinars = int(price_match.group(1))
                                            millimes = int(price_match.group(2)) if price_match.group(2) else 0
                                            price = dinars + (millimes / 1000)
                                
                                # Extract image URL (img.lazy-product-image[data-src])
                                img_elem = card.find('img', class_='lazy-product-image')
                                img_url = None
                                if img_elem:
                                    # Lazy-loaded images use data-src
                                    img_url = img_elem.get('data-src') or img_elem.get('src')
                                
                                # Download image
                                product_image = None
                                if img_url:
                                    if not img_url.startswith('http'):
                                        img_url = f"{base_url}{img_url}"
                                    
                                    try:
                                        img_response = requests.get(img_url, timeout=10)
                                        if img_response.status_code == 200:
                                            product_image = Image.open(BytesIO(img_response.content))
                                    except Exception as e:
                                        print(f"      ⚠️ Failed to download image: {e}")
                                
                                if name and price and product_image:
                                    product_data = {
                                        "name": name,
                                        "price": price,
                                        "market": "mg",
                                        "description": name,
                                        "category": category,
                                        "image": product_image,
                                        "scraped_at": datetime.now().isoformat()
                                    }
                                    
                                    if product_url:
                                        product_data["url"] = product_url
                                    
                                    products.append(product_data)
                            
                            except Exception as e:
                                continue
                        
                        # Find next page link (nav.pagination a[rel="next"])
                        pagination = soup.find('nav', class_='pagination')
                        next_link = None
                        if pagination:
                            next_elem = pagination.find('a', rel='next')
                            if next_elem:
                                next_link = next_elem.get('href')
                        
                        # Update current_url for next iteration
                        current_url = next_link
                        
                        # Small delay between pages
                        await asyncio.sleep(1)
        
        except Exception as e:
            print(f"  ❌ Error scraping MG: {e}")
        
        return products
    
    async def scrape_geant_tunisia(self) -> List[Dict[str, Any]]:
        """
        Scrape Geant Drive Tunisia (PrestaShop with pagination).
        URL: https://www.geantdrive.tn/tunis-city/332-promotions
        """
        products = []
        base_url = "https://www.geantdrive.tn"
        
        # Promotions URL
        url = "https://www.geantdrive.tn/tunis-city/332-promotions"
        
        try:
            if not self.is_allowed_by_robots(url):
                print(f"  ⚠️ Blocked by robots.txt: {url}")
                return products
            
            print(f"  Crawling {url}...")
            
            async with AsyncWebCrawler(config=browser_config) as crawler:
                # Pagination: follow up to 3 pages
                current_url = url
                page_count = 0
                max_pages = 3
                
                while current_url and page_count < max_pages:
                    page_count += 1
                    print(f"    Page {page_count}...")
                    
                    result = await crawler.arun(
                        url=current_url,
                        config=CrawlerRunConfig(
                            cache_mode=CacheMode.BYPASS,
                            session_id=f"geant_scrape_page_{page_count}",
                            wait_for="css:article.product-miniature",
                            page_timeout=30000,
                        )
                    )
                    
                    if not result.success or not result.html:
                        print(f"    ❌ Failed to fetch page {page_count}")
                        break
                    
                    soup = BeautifulSoup(result.html, 'html.parser')
                    
                    # Geant uses div.item-product > article.product-miniature
                    product_containers = soup.find_all('div', class_='item-product')
                    
                    print(f"    Found {len(product_containers)} products on page {page_count}")
                    
                    for container in product_containers:
                        try:
                            # Find the article inside
                            article = container.find('article', class_='product-miniature')
                            if not article:
                                continue
                            
                            # Extract product ID (data-id-product attribute)
                            product_id = article.get('data-id-product')
                            
                            # Extract product name (h2.product-title a)
                            name_elem = article.find('h2', class_='product-title')
                            name = None
                            product_url = None
                            if name_elem:
                                name_link = name_elem.find('a')
                                if name_link:
                                    name = name_link.text.strip()
                                    product_url = name_link.get('href')
                            
                            # Extract brand (p.manufacturer_product)
                            brand_elem = article.find('p', class_='manufacturer_product')
                            brand = brand_elem.text.strip() if brand_elem else ""
                            
                            # Extract short description (div.product_short)
                            desc_elem = article.find('div', class_='product_short')
                            short_desc = desc_elem.text.strip() if desc_elem else ""
                            
                            # Extract price (span.price)
                            price_elem = article.find('span', class_='price')
                            price = None
                            if price_elem:
                                price_text = price_elem.text.strip()
                                # Parse price with comma decimal: "12,500 DT" → 12.500
                                price_match = re.search(r'(\d+)[.,](\d+)', price_text)
                                if price_match:
                                    dinars = int(price_match.group(1))
                                    millimes = int(price_match.group(2))
                                    price = dinars + (millimes / 1000)
                            
                            # Extract old price (span.regular-price) - optional
                            old_price_elem = article.find('span', class_='regular-price')
                            old_price = None
                            if old_price_elem:
                                old_price_text = old_price_elem.text.strip()
                                price_match = re.search(r'(\d+)[.,](\d+)', old_price_text)
                                if price_match:
                                    dinars = int(price_match.group(1))
                                    millimes = int(price_match.group(2))
                                    old_price = dinars + (millimes / 1000)
                            
                            # Extract promo flag (ul.product-flags li.product-flag.discount)
                            promo_flag = None
                            flags_elem = article.find('ul', class_='product-flags')
                            if flags_elem:
                                discount_flag = flags_elem.find('li', class_='discount')
                                if discount_flag:
                                    promo_flag = discount_flag.text.strip()
                            
                            # Extract image URL (img.img-responsive[src])
                            img_elem = article.find('img', class_='img-responsive')
                            img_url = None
                            if img_elem:
                                img_url = img_elem.get('src')
                            
                            # Download image
                            product_image = None
                            if img_url:
                                if not img_url.startswith('http'):
                                    img_url = f"{base_url}{img_url}"
                                
                                try:
                                    img_response = requests.get(img_url, timeout=10)
                                    if img_response.status_code == 200:
                                        product_image = Image.open(BytesIO(img_response.content))
                                except Exception as e:
                                    print(f"      ⚠️ Failed to download image: {e}")
                            
                            # Build full product name with brand
                            full_name = name
                            if brand:
                                full_name = f"{brand} {name}"
                            
                            if name and price and product_image:
                                product_data = {
                                    "name": full_name,
                                    "price": price,
                                    "market": "geant",
                                    "description": short_desc or full_name,
                                    "category": "food",
                                    "image": product_image,
                                    "scraped_at": datetime.now().isoformat()
                                }
                                
                                # Add optional fields
                                if product_id:
                                    product_data["product_id"] = product_id
                                if product_url:
                                    product_data["url"] = product_url
                                if old_price:
                                    product_data["old_price"] = old_price
                                if promo_flag:
                                    product_data["promo"] = promo_flag
                                
                                products.append(product_data)
                        
                        except Exception as e:
                            continue
                    
                    # Find next page link (.pagination a.next)
                    pagination = soup.find('div', class_='pagination')
                    if not pagination:
                        pagination = soup.find('nav', class_='pagination')
                    
                    next_link = None
                    if pagination:
                        next_elem = pagination.find('a', class_='next')
                        if next_elem:
                            next_link = next_elem.get('href')
                    
                    # Update current_url for next iteration
                    current_url = next_link
                    
                    # Small delay between pages
                    await asyncio.sleep(1)
        
        except Exception as e:
            print(f"  ❌ Error scraping Geant: {e}")
        
        return products
    
    async def scrape_carrefour_tunisia(self) -> List[Dict[str, Any]]:
        """
        Scrape Carrefour Tunisia online store.
        Example: https://www.carrefour.tn/
        """
        products = []
        url = "https://www.carrefour.tn/maftn/fr/promotions"  # Update with actual URL
        
        try:
            if not self.is_allowed_by_robots(url):
                print(f"  ⚠️ Blocked by robots.txt: {url}")
                return products
            
            print(f"  Crawling {url}...")
            
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(
                    url=url,
                    config=CrawlerRunConfig(
                        cache_mode=CacheMode.BYPASS,
                        session_id="carrefour_scrape"
                    )
                )
                
                if not result.success or not result.html:
                    print(f"  ❌ Failed to fetch page")
                    return products
                
                soup = BeautifulSoup(result.html, 'html.parser')
                
                # Carrefour-specific selectors (adjust based on actual site)
                product_cards = soup.find_all('div', class_='product-item')
                
                if not product_cards:
                    product_cards = soup.find_all('article', class_='product')
                
                print(f"  Found {len(product_cards)} product cards")
                
                for card in product_cards[:50]:
                    try:
                        name_elem = card.find(['a', 'h3'], class_=re.compile('product.*name'))
                        name = name_elem.text.strip() if name_elem else None
                        
                        price_elem = card.find('span', class_=re.compile('price'))
                        price_text = price_elem.text.strip() if price_elem else None
                        
                        price = None
                        if price_text:
                            price_match = re.search(r'(\d+)[.,\s]*(\d+)?', price_text)
                            if price_match:
                                dinars = int(price_match.group(1))
                                millimes = int(price_match.group(2)) if price_match.group(2) else 0
                                price = dinars + (millimes / 1000)
                        
                        img_elem = card.find('img')
                        img_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else None
                        
                        product_image = None
                        if img_url:
                            if not img_url.startswith('http'):
                                img_url = f"https://www.carrefour.tn{img_url}"
                            
                            try:
                                img_response = requests.get(img_url, timeout=10)
                                if img_response.status_code == 200:
                                    product_image = Image.open(BytesIO(img_response.content))
                            except:
                                pass
                        
                        if name and price and product_image:
                            products.append({
                                "name": name,
                                "price": price,
                                "market": "carrefour",
                                "description": name,
                                "category": "food",
                                "image": product_image,
                                "scraped_at": datetime.now().isoformat()
                            })
                    
                    except Exception as e:
                        continue
        
        except Exception as e:
            print(f"  ❌ Error scraping Carrefour: {e}")
        
        return products
    
    async def scrape_monoprix_tunisia(self) -> List[Dict[str, Any]]:
        """
        Scrape Monoprix Tunisia.
        Example: https://courses.monoprix.tn/
        """
        products = []
        url = "https://courses.monoprix.tn/promotions"  # Update with actual URL
        
        try:
            if not self.is_allowed_by_robots(url):
                print(f"  ⚠️ Blocked by robots.txt: {url}")
                return products
            
            print(f"  Crawling {url}...")
            
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(
                    url=url,
                    config=CrawlerRunConfig(
                        cache_mode=CacheMode.BYPASS,
                        session_id="monoprix_scrape"
                    )
                )
                
                if not result.success or not result.html:
                    print(f"  ❌ Failed to fetch page")
                    return products
                
                soup = BeautifulSoup(result.html, 'html.parser')
                
                # Monoprix-specific selectors
                product_cards = soup.find_all('article', class_='product')
                
                if not product_cards:
                    product_cards = soup.find_all('div', class_='product-card')
                
                print(f"  Found {len(product_cards)} product cards")
                
                for card in product_cards[:50]:
                    try:
                        name_elem = card.find(['h2', 'h3'], class_=re.compile('product.*title|name'))
                        name = name_elem.text.strip() if name_elem else None
                        
                        price_elem = card.find('span', class_=re.compile('price'))
                        price_text = price_elem.text.strip() if price_elem else None
                        
                        price = None
                        if price_text:
                            price_match = re.search(r'(\d+)[.,\s]*(\d+)?', price_text)
                            if price_match:
                                dinars = int(price_match.group(1))
                                millimes = int(price_match.group(2)) if price_match.group(2) else 0
                                price = dinars + (millimes / 1000)
                        
                        img_elem = card.find('img')
                        img_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else None
                        
                        product_image = None
                        if img_url:
                            if not img_url.startswith('http'):
                                img_url = f"https://courses.monoprix.tn{img_url}"
                            
                            try:
                                img_response = requests.get(img_url, timeout=10)
                                if img_response.status_code == 200:
                                    product_image = Image.open(BytesIO(img_response.content))
                            except:
                                pass
                        
                        if name and price and product_image:
                            products.append({
                                "name": name,
                                "price": price,
                                "market": "monoprix",
                                "description": name,
                                "category": "food",
                                "image": product_image,
                                "scraped_at": datetime.now().isoformat()
                            })
                    
                    except Exception as e:
                        continue
        
        except Exception as e:
            print(f"  ❌ Error scraping Monoprix: {e}")
        
        return products
    
    async def scrape_all_markets(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scrape all configured supermarkets.
        Run this weekly to update product database.
        Saves products to SQLite database.
        """
        print("🕷️ Starting weekly supermarket scraping...")
        print("=" * 60)
        
        all_products = {}
        
        # Scrape Aziza
        print("\n📍 Scraping Aziza...")
        aziza_products = await self.scrape_aziza_online()
        all_products['aziza'] = aziza_products
        print(f"   ✓ Found {len(aziza_products)} products from Aziza")
        
        # Save to database
        if aziza_products:
            print(f"   💾 Saving to database...")
            saved = product_db.batch_insert_products(aziza_products)
            print(f"   ✓ Saved {saved} products to database")
        
        # Scrape MG
        print("\n📍 Scraping MG...")
        mg_products = await self.scrape_mg_tunisia()
        all_products['mg'] = mg_products
        print(f"   ✓ Found {len(mg_products)} products from MG")
        
        if mg_products:
            print(f"   💾 Saving to database...")
            saved = product_db.batch_insert_products(mg_products)
            print(f"   ✓ Saved {saved} products to database")
        
        # Scrape Geant
        print("\n📍 Scraping Geant...")
        geant_products = await self.scrape_geant_tunisia()
        all_products['geant'] = geant_products
        print(f"   ✓ Found {len(geant_products)} products from Geant")
        
        if geant_products:
            print(f"   💾 Saving to database...")
            saved = product_db.batch_insert_products(geant_products)
            print(f"   ✓ Saved {saved} products to database")
        
        # Scrape Carrefour
        print("\n📍 Scraping Carrefour...")
        carrefour_products = await self.scrape_carrefour_tunisia()
        all_products['carrefour'] = carrefour_products
        print(f"   ✓ Found {len(carrefour_products)} products from Carrefour")
        
        if carrefour_products:
            print(f"   💾 Saving to database...")
            saved = product_db.batch_insert_products(carrefour_products)
            print(f"   ✓ Saved {saved} products to database")
        
        # Scrape Monoprix
        print("\n📍 Scraping Monoprix...")
        monoprix_products = await self.scrape_monoprix_tunisia()
        all_products['monoprix'] = monoprix_products
        print(f"   ✓ Found {len(monoprix_products)} products from Monoprix")
        
        if monoprix_products:
            print(f"   💾 Saving to database...")
            saved = product_db.batch_insert_products(monoprix_products)
            print(f"   ✓ Saved {saved} products to database")
        
        self.last_scrape_time = datetime.now()
        self.scraped_data = all_products
        
        total_products = sum(len(prods) for prods in all_products.values())
        
        # Show database statistics
        print("\n" + "=" * 60)
        print("📊 DATABASE STATISTICS")
        print("=" * 60)
        stats = product_db.get_statistics()
        print(f"Total products in database: {stats['total_products']}")
        print(f"\nProducts by market:")
        for market, count in stats['by_market'].items():
            avg_price = stats['avg_prices'].get(market, 0)
            print(f"  {market}: {count} products (avg price: {avg_price} TND)")
        print(f"\nProducts with promotions: {stats['products_with_promos']}")
        
        print(f"\n✅ Scraping complete! Scraped {total_products} products this run")
        print("=" * 60)
        
        return all_products

# Singleton instance
supermarket_scraper = SupermarketScraper()


# Async helper function
async def run_weekly_scrape():
    """Run the weekly scraping job"""
    return await supermarket_scraper.scrape_all_markets()
