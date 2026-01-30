"""
MAZRAA Market Web Scraper using Crawl4AI
Extracts product images, prices, and names from MAZRAA Market website.
Supports both offline HTML and live web scraping with Crawl4AI.
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
from urllib.parse import urljoin
from pathlib import Path
import json
import csv

# Browser configuration for Crawl4AI
BROWSER_CONFIG = BrowserConfig(
    browser_type="chromium",
    headless=True,
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    extra_args=[
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-blink-features=AutomationControlled",
    ],
)


class MazraaMarketCrawl4AI:
    """
    MAZRAA Market scraper using Crawl4AI.
    
    Supports:
    - Live web scraping from MAZRAA Market website
    - Pagination handling
    - Category filtering
    - Product image downloading
    - Multiple output formats (JSON, CSV, HTML)
    """
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)  # Create parent directories too
        self.products = []
        self.scrape_timestamp = None
        self.base_url = "http://mazraamarket.tn"
    
    async def scrape_mazraa_live(
        self,
        category_url: str = "http://mazraamarket.tn/faces/storeParCategorie.xhtml",
        max_pages: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Scrape MAZRAA Market live using Crawl4AI.
        Handles pagination and multiple categories.
        
        Args:
            category_url: URL of the category to scrape
            max_pages: Maximum number of pages to scrape per category
            
        Returns:
            List of product dictionaries
        """
        products = []
        self.scrape_timestamp = datetime.now()
        
        try:
            async with AsyncWebCrawler(config=BROWSER_CONFIG) as crawler:
                # Pagination: follow up to max_pages
                current_url = category_url
                page_count = 0
                
                while current_url and page_count < max_pages:
                    page_count += 1
                    print(f"  📄 Page {page_count}: {current_url}")
                    
                    try:
                        # Use Crawl4AI to fetch and render the page
                        result = await crawler.arun(
                            url=current_url,
                            config=CrawlerRunConfig(
                                cache_mode=CacheMode.BYPASS,  # Don't use cache
                                session_id=f"mazraa_scrape_page_{page_count}",
                                # Remove wait_for to avoid timeout, use delay instead
                                page_timeout=60000,  # 60 second timeout
                                delay_before_return_html=5.0,  # Wait 5 seconds for page to load
                                js_code=[
                                    # Wait for page to fully load
                                    "await new Promise(r => setTimeout(r, 3000));",
                                ],
                            ),
                        )
                        
                        if not result.success or not result.html:
                            print(f"    ❌ Failed to fetch page {page_count}")
                            break
                        
                        # Parse with BeautifulSoup
                        soup = BeautifulSoup(result.html, "html.parser")
                        
                        # Extract products
                        page_products = self._extract_products_from_html(soup, page_number=page_count)
                        products.extend(page_products)
                        print(f"    ✓ Found {len(page_products)} products on page {page_count}")
                        
                        # Find next page URL
                        current_url = self._get_next_page_url(soup)
                        
                        # Respectful delay between pages
                        if current_url:
                            await asyncio.sleep(2)
                    
                    except Exception as e:
                        print(f"    ❌ Error on page {page_count}: {e}")
                        break
        
        except Exception as e:
            print(f"  ❌ Error scraping MAZRAA: {e}")
        
        return products
    
    async def scrape_multiple_categories(
        self, 
        category_urls: List[str], 
        max_pages_per_category: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scrape multiple categories from MAZRAA Market.
        
        Args:
            category_urls: List of category URLs to scrape
            max_pages_per_category: Max pages per category
            
        Returns:
            Dictionary with results per category
        """
        results = {}
        
        for i, url in enumerate(category_urls, 1):
            print(f"\n📍 Scraping category {i}/{len(category_urls)}")
            products = await self.scrape_mazraa_live(url, max_pages_per_category)
            
            category_name = url.split("=")[-1] if "=" in url else f"category_{i}"
            results[category_name] = products
            print(f"   ✓ Found {len(products)} products")
            
            # Delay between categories
            if i < len(category_urls):
                await asyncio.sleep(3)
        
        return results
    
    def _extract_products_from_html(
        self, 
        soup: BeautifulSoup, 
        page_number: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Extract products from parsed HTML.
        
        Args:
            soup: BeautifulSoup parsed HTML
            page_number: Page number for tracking
            
        Returns:
            List of product dictionaries
        """
        products = []
        
        # Find all product containers - they're inside ui-datagrid-content
        datagrid_content = soup.find("div", class_="ui-datagrid-content")
        if not datagrid_content:
            print("      ⚠️ No datagrid content found")
            return products
        
        # Find all product divs
        product_divs = datagrid_content.find_all("div", class_="product")
        
        print(f"      Found {len(product_divs)} product divs")
        
        for idx, product_div in enumerate(product_divs, 1):
            try:
                # Extract product name from h6 with class product-name
                name_elem = product_div.find("h6", class_="product-name")
                if not name_elem:
                    continue
                product_name = name_elem.get_text(strip=True)
                
                # Extract price from h4 with class product-price
                price_elem = product_div.find("h4", class_="product-price")
                if not price_elem:
                    continue
                price_text = price_elem.get_text(strip=True)
                # Extract just the number (e.g., "3.150 TND" -> "3.150")
                price = price_text.split()[0]
                
                # Extract image
                img_elem = product_div.find("img")
                if not img_elem:
                    continue
                image_url = img_elem.get("src", "")
                
                # Make URL absolute
                if image_url and not image_url.startswith("http"):
                    image_url = urljoin(self.base_url, image_url)
                
                # Try to download image
                product_image = None
                if image_url:
                    try:
                        img_response = requests.get(image_url, timeout=10)
                        if img_response.status_code == 200:
                            product_image = Image.open(BytesIO(img_response.content))
                    except Exception as e:
                        print(f"      ⚠️ Failed to download image for {product_name}: {e}")
                
                product_data = {
                    "product_name": product_name,
                    "price": price,
                    "currency": "TND",
                    "image_url": image_url,
                    "image": product_image,
                    "page": page_number,
                    "market": "el_mazraa",
                    "scraped_at": self.scrape_timestamp.isoformat()
                    if self.scrape_timestamp
                    else datetime.now().isoformat(),
                }
                
                products.append(product_data)
                print(f"      ✓ Extracted: {product_name} - {price} TND")
            
            except Exception as e:
                print(f"      ⚠️ Error extracting product {idx}: {e}")
                continue
        
        return products
    
    def _get_next_page_url(self, soup: BeautifulSoup) -> str:
        """
        Extract next page URL from pagination.
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            Next page URL or None
        """
        try:
            # Find pagination
            paginator = soup.find("div", class_="ui-paginator")
            if not paginator:
                return None
            
            # Find next button
            next_link = paginator.find("a", class_="ui-paginator-next")
            if not next_link:
                return None
            
            href = next_link.get("href")
            if href and not href.startswith("http"):
                href = urljoin(self.base_url, href)
            
            return href
        
        except Exception:
            return None
    
    async def download_all_images(self, products: List[Dict[str, Any]]) -> None:
        """
        Download all product images and save to disk.
        
        Args:
            products: List of product dictionaries
        """
        images_dir = self.output_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)  # Create parent directories too
        
        print(f"\n📸 Downloading {len(products)} product images...")
        
        for idx, product in enumerate(products, 1):
            try:
                if "image" not in product or not product["image"]:
                    continue
                
                # Create filename
                product_name = product["product_name"][:30].replace(" ", "_")
                filename = f"{idx:04d}_{product_name}.jpg"
                filepath = images_dir / filename
                
                # Save image
                product["image"].save(filepath, "JPEG", quality=85)
                
                if idx % 10 == 0:
                    print(f"  ✓ Downloaded {idx} images...")
            
            except Exception as e:
                print(f"  ⚠️ Error downloading image {idx}: {e}")
        
        print(f"  ✓ Downloaded {len(products)} images to {images_dir}")
    
    def save_json(
        self, 
        products: List[Dict[str, Any]], 
        filename: str = "mazraa_products.json"
    ) -> bool:
        """Save products to JSON."""
        try:
            # Remove PIL Image objects for JSON serialization
            json_products = []
            for p in products:
                json_p = {k: v for k, v in p.items() if k != "image"}
                json_products.append(json_p)
            
            filepath = self.output_dir / filename
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(json_products, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Saved JSON: {filepath} ({len(products)} items)")
            return True
        
        except Exception as e:
            print(f"❌ Error saving JSON: {e}")
            return False
    
    def save_csv(
        self, 
        products: List[Dict[str, Any]], 
        filename: str = "mazraa_products.csv"
    ) -> bool:
        """Save products to CSV."""
        try:
            if not products:
                print("⚠️ No products to save")
                return False
            
            filepath = self.output_dir / filename
            keys = ["product_name", "price", "currency", "image_url", "market", "page", "scraped_at"]
            
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                for product in products:
                    row = {k: product.get(k, "") for k in keys}
                    writer.writerow(row)
            
            print(f"✓ Saved CSV: {filepath} ({len(products)} items)")
            return True
        
        except Exception as e:
            print(f"❌ Error saving CSV: {e}")
            return False
    
    def print_summary(self, products: List[Dict[str, Any]]) -> None:
        """Print scraping summary."""
        print("\n" + "=" * 70)
        print("📊 MAZRAA MARKET SCRAPING SUMMARY")
        print("=" * 70)
        print(f"✓ Total Products: {len(products)}")
        
        if products:
            prices = []
            for p in products:
                try:
                    price = float(p["price"].replace(",", "."))
                    prices.append(price)
                except:
                    pass
            
            if prices:
                print(f"💰 Price Range: {min(prices):.3f} - {max(prices):.3f} TND")
                print(f"📈 Average Price: {sum(prices)/len(prices):.3f} TND")
        
        if self.scrape_timestamp:
            print(f"⏰ Timestamp: {self.scrape_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("=" * 70 + "\n")


async def test_mazraa_scraper():
    """Test the Mazraa Market scraper."""
    print("\n🕷️ MAZRAA Market Scraper Test with Crawl4AI")
    print("=" * 70)
    
    scraper = MazraaMarketCrawl4AI(output_dir="output/mazraa")  # Fixed path
    
    # Scrape live from MAZRAA Market
    print("\n📍 Scraping MAZRAA Market (live)...")
    products = await scraper.scrape_mazraa_live(max_pages=2)
    
    if not products:
        print("❌ No products found!")
        return
    
    # Print summary
    scraper.print_summary(products)
    
    # Save outputs
    print("💾 Saving outputs...")
    scraper.save_json(products)
    scraper.save_csv(products)
    
    # Download images (optional)
    print("\n📸 Downloading images...")
    await scraper.download_all_images(products)
    
    print(f"\n✅ Done! Check the 'output/mazraa' directory for results")
    
    return products


if __name__ == "__main__":
    asyncio.run(test_mazraa_scraper())
