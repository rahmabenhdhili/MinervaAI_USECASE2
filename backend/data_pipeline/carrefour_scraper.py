"""
Carrefour Tunisia Web Scraper using Selenium
Extracts product images, names, and prices from dynamically loaded content
Integrates with ProductDatabase and Qdrant
"""
import time
import re
import io
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from PIL import Image
import requests

from data_pipeline.product_database import ProductDatabase


class CarrefourScraper:
    """Scraper for Carrefour Tunisia products using Selenium"""
    
    def __init__(self, base_url: str = "https://www.carrefour.tn/boissons/eaux.html"):
        self.base_url = base_url
        self.products = []
        self.output_dir = Path("output/carrefour")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self.db = ProductDatabase()
        
        # Setup Selenium
        self.driver = None
        
        # Setup Selenium
        self.driver = None
    
    def setup_driver(self):
        """Initialize Selenium WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        print("✅ Selenium WebDriver initialized")
    
    def close_driver(self):
        """Close Selenium WebDriver"""
        if self.driver:
            self.driver.quit()
            print("✅ WebDriver closed")
    
    def clean_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text"""
        if not price_text:
            return None
        
        # Remove currency symbols and extract numbers
        numbers = re.findall(r'\d+[.,]?\d*', price_text.replace(',', '.'))
        if numbers:
            try:
                return float(numbers[0])
            except ValueError:
                return None
        return None
    
    def download_image_as_blob(self, image_url: str) -> Optional[bytes]:
        """Download image and return as BLOB"""
        try:
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:
                # Verify it's a valid image
                img = Image.open(io.BytesIO(response.content))
                img.verify()
                return response.content
            return None
        except Exception as e:
            print(f"   ⚠️  Error downloading image: {e}")
            return None
    
    def get_total_pages(self) -> int:
        """Detect total number of pages available"""
        try:
            url = f"{self.base_url}?page=1"
            self.driver.get(url)
            time.sleep(3)
            
            # Look for pagination elements
            try:
                # Try to find the last page number in pagination
                pagination_elements = self.driver.find_elements(By.CSS_SELECTOR, "a.page-link, button.page-link, a[class*='page'], button[class*='page']")
                
                max_page = 1
                for elem in pagination_elements:
                    text = elem.text.strip()
                    if text.isdigit():
                        page_num = int(text)
                        if page_num > max_page:
                            max_page = page_num
                
                if max_page > 1:
                    print(f"📄 Detected {max_page} pages available")
                    return max_page
            except Exception as e:
                pass
            
            # Fallback: check if there's a "next" button
            try:
                next_button = self.driver.find_element(By.CSS_SELECTOR, "a[aria-label*='Next'], button[aria-label*='Next'], a[class*='next'], button[class*='next']")
                if next_button:
                    print("📄 Pagination detected, will scrape until no more products")
                    return 999  # Large number to continue until empty
            except:
                pass
            
            print("📄 No pagination detected, assuming single page")
            return 1
            
        except Exception as e:
            print(f"⚠️  Error detecting pagination: {e}")
            return 1
    
    def scrape_page(self, page_num: int = 1) -> List[Dict]:
        """Scrape a single page"""
        url = f"{self.base_url}?page={page_num}"
        print(f"\n📄 Scraping page {page_num}: {url}")
        
        try:
            self.driver.get(url)
            
            # Wait for products to load
            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.category-categoryItem-7pb")))
            
            # Scroll to load lazy images
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Find all product cards
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.category-categoryItem-7pb")
            
            products = []
            print(f"   Found {len(product_elements)} product cards")
            
            for idx, element in enumerate(product_elements):
                try:
                    # Extract product name - try to get both brand/name and description
                    product_name = None
                    product_description = None
                    
                    # Try to get the main product name (brand + product)
                    try:
                        name_elem = element.find_element(By.CSS_SELECTOR, "span.item-name-LPg")
                        product_name = name_elem.text.strip()
                    except NoSuchElementException:
                        pass
                    
                    # Try to get the description (packaging info)
                    try:
                        desc_elem = element.find_element(By.CSS_SELECTOR, "div.item-description-oxA")
                        product_description = desc_elem.text.strip()
                    except NoSuchElementException:
                        pass
                    
                    # Combine name and description if both exist
                    if product_name and product_description:
                        full_name = f"{product_name} - {product_description}"
                    elif product_name:
                        full_name = product_name
                    elif product_description:
                        full_name = product_description
                    else:
                        continue
                    
                    if not full_name or len(full_name) < 3:
                        continue
                    
                    # Extract price - look for integer and decimal parts
                    price = None
                    try:
                        integer_elem = element.find_element(By.CSS_SELECTOR, "span.item-miniInteger-NhR")
                        decimal_elem = element.find_element(By.CSS_SELECTOR, "span.item-miniDecimal-Cwx")
                        
                        integer_part = integer_elem.text.strip()
                        decimal_part = decimal_elem.text.strip()
                        
                        if integer_part and decimal_part:
                            price = float(f"{integer_part}.{decimal_part}")
                    except NoSuchElementException:
                        pass
                    
                    # Extract image
                    image_url = None
                    try:
                        img_elem = element.find_element(By.CSS_SELECTOR, "img.image-loaded-QS8")
                        image_url = img_elem.get_attribute('src')
                        
                        # Fix relative URLs
                        if image_url and not image_url.startswith('http'):
                            if image_url.startswith('//'):
                                image_url = 'https:' + image_url
                            elif image_url.startswith('/'):
                                image_url = 'https://www.carrefour.tn' + image_url
                    except NoSuchElementException:
                        pass
                    
                    # Extract product URL
                    product_url = None
                    try:
                        link_elem = element.find_element(By.CSS_SELECTOR, "a.item-nameContainer--mM")
                        product_url = link_elem.get_attribute('href')
                    except NoSuchElementException:
                        pass
                    
                    if full_name and price:
                        product = {
                            'name': full_name,
                            'price': price,
                            'image_url': image_url,
                            'product_url': product_url,
                            'market': 'Carrefour',
                            'scraped_at': datetime.now().isoformat()
                        }
                        products.append(product)
                        
                        if len(products) % 10 == 0:
                            print(f"   ✓ Extracted {len(products)} products...")
                
                except Exception as e:
                    continue
            
            print(f"✅ Successfully scraped {len(products)} products from page {page_num}")
            return products
        
        except TimeoutException:
            print(f"❌ Timeout waiting for products to load on page {page_num}")
            return []
        except Exception as e:
            print(f"❌ Error scraping page {page_num}: {str(e)}")
            return []
    
    def scrape_multiple_pages(self, start_page: int = 1, end_page: int = 3, auto_detect: bool = False):
        """Scrape multiple pages
        
        Args:
            start_page: Starting page number
            end_page: Ending page number (ignored if auto_detect=True)
            auto_detect: If True, automatically detect total pages and scrape all
        """
        self.setup_driver()
        
        try:
            all_products = []
            
            # Auto-detect total pages if requested
            if auto_detect:
                total_pages = self.get_total_pages()
                end_page = min(total_pages, 20)  # Limit to 20 pages max for safety
                print(f"🔍 Will scrape pages {start_page} to {end_page}")
            
            for page_num in range(start_page, end_page + 1):
                products = self.scrape_page(page_num)
                
                # If no products found, we've reached the end
                if not products:
                    print(f"⚠️  No products found on page {page_num}, stopping pagination")
                    break
                
                all_products.extend(products)
                
                # Be polite - add delay between pages
                if page_num < end_page:
                    time.sleep(3)
            
            self.products = all_products
            return all_products
        
        finally:
            self.close_driver()
    
    def save_to_database(self) -> int:
        """Save products to SQLite database"""
        if not self.products:
            print("⚠️  No products to save")
            return 0
        
        print(f"\n💾 Saving {len(self.products)} products to database...")
        saved_count = 0
        
        for product in self.products:
            if not product.get('name') or not product.get('price'):
                continue
            
            try:
                # Download image as BLOB
                image_blob = None
                if product.get('image_url'):
                    image_blob = self.download_image_as_blob(product['image_url'])
                
                self.db.insert_product({
                    'name': product['name'],
                    'price': product['price'],
                    'market': 'Carrefour',
                    'image_url': product.get('image_url', ''),
                    'image_blob': image_blob,
                    'product_url': product.get('product_url', ''),
                    'description': product['name'],
                    'currency': 'TND',
                    'category': 'beverages'
                })
                saved_count += 1
                
                if saved_count % 10 == 0:
                    print(f"   ✓ Saved {saved_count} products...")
            
            except Exception as e:
                print(f"   ⚠️  Error saving product: {e}")
                continue
        
        print(f"✅ Successfully saved {saved_count} products to database!")
        return saved_count
    
    def print_summary(self):
        """Print summary statistics"""
        if not self.products:
            print("No products scraped")
            return
        
        total = len(self.products)
        with_prices = sum(1 for p in self.products if p.get('price'))
        with_images = sum(1 for p in self.products if p.get('image_url'))
        
        print("\n" + "="*60)
        print("📊 SCRAPING SUMMARY")
        print("="*60)
        print(f"Total products: {total}")
        print(f"Products with prices: {with_prices} ({with_prices/total*100:.1f}%)")
        print(f"Products with images: {with_images} ({with_images/total*100:.1f}%)")
        
        if with_prices:
            prices = [p['price'] for p in self.products if p.get('price')]
            print(f"\nPrice range: {min(prices):.2f} - {max(prices):.2f} TND")
            print(f"Average price: {sum(prices)/len(prices):.2f} TND")
        
        print("="*60 + "\n")


def main():
    """Main execution function"""
    print("🚀 Carrefour Tunisia Scraper (Selenium)")
    print("="*60)
    
    # Initialize scraper
    scraper = CarrefourScraper(base_url="https://www.carrefour.tn/boissons/eaux.html")
    
    # Scrape pages 1-3
    print("\n🔍 Starting scraping process...")
    scraper.scrape_multiple_pages(start_page=1, end_page=3)
    
    # Print summary
    scraper.print_summary()
    
    # Save to database
    if scraper.products:
        saved_count = scraper.save_to_database()
        
        # Print sample products
        print("\n📦 Sample products:")
        for i, product in enumerate(scraper.products[:3], 1):
            print(f"\n{i}. {product['name']}")
            print(f"   Price: {product['price']} TND")
            if product.get('image_url'):
                print(f"   Image: {product['image_url'][:60]}...")
        
        print("\n💡 Next steps:")
        print("   1. Run: python browse_database.py")
        print("   2. Run: python load_db_to_qdrant.py")
        print("   3. Your products will be searchable in the app!")
    else:
        print("⚠️  No products were scraped. Check the selectors or website structure.")


if __name__ == "__main__":
    main()
