"""
Mazraa Market Selenium Scraper
Scrapes products from http://mazraamarket.tn using Selenium to handle JSF/PrimeFaces AJAX
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException
import time
import sys
import os
import requests
from PIL import Image
from io import BytesIO

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_pipeline.product_database import ProductDatabase

# Configuration
URL = "http://mazraamarket.tn/faces/storeParCategorie.xhtml"
SUPERMARKET = "Mazraa Market"
HEADLESS = False  # Set to True to run without opening browser window

class MazraaSeleniumScraper:
    def __init__(self, headless=HEADLESS):
        self.setup_driver(headless)
        self.wait = WebDriverWait(self.driver, 15)
        self.db = ProductDatabase()
        self.products_scraped = 0
        
    def setup_driver(self, headless):
        """Initialize Chrome WebDriver with options"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
    def wait_for_loading_overlay(self):
        """Waits for the PrimeFaces loading modal to disappear"""
        try:
            # Wait for loading overlay to disappear
            self.wait.until(EC.invisibility_of_element_located((By.ID, "j_idt4")))
        except:
            pass
        
    def download_image(self, img_url):
        """Download image from URL using Selenium's session cookies"""
        try:
            # Handle relative URLs
            if img_url.startswith('/'):
                img_url = f"http://mazraamarket.tn{img_url}"
            
            # Get cookies from Selenium session
            cookies = self.driver.get_cookies()
            session = requests.Session()
            for cookie in cookies:
                session.cookies.set(cookie['name'], cookie['value'])
            
            # Add headers to mimic browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Referer': 'http://mazraamarket.tn/faces/storeParCategorie.xhtml'
            }
            
            response = session.get(img_url, timeout=10, headers=headers)
            if response.status_code == 200 and len(response.content) > 0:
                # Try to open as image regardless of content-type header
                # (PrimeFaces doesn't always set it correctly)
                try:
                    img = Image.open(BytesIO(response.content))
                    # Convert to RGB if necessary (some images are RGBA or P mode)
                    if img.mode in ('RGBA', 'P', 'LA'):
                        img = img.convert('RGB')
                    return img
                except:
                    pass
        except Exception as e:
            # Silently fail - too verbose otherwise
            pass
        return None
        
    def scrape_current_page(self, category_name):
        """Extracts product data from the currently visible grid"""
        try:
            products = self.driver.find_elements(By.CLASS_NAME, "ui-datagrid-column")
            print(f"\n--- Category: {category_name} ({len(products)} products found) ---")
            
            first_product = True  # Debug flag
            
            for product in products:
                try:
                    # Extract product details
                    name = product.find_element(By.CSS_SELECTOR, "h6.product-name").text.strip()
                    price_text = product.find_element(By.CSS_SELECTOR, "h4.product-price").text.strip()
                    
                    # Extract image URL
                    img_element = product.find_element(By.CSS_SELECTOR, "img[id*='Photo']")
                    img_url = img_element.get_attribute("src")
                    
                    # Debug: print first image URL
                    if first_product:
                        print(f"  [DEBUG] First image URL: {img_url}")
                        first_product = False
                    
                    # Parse price (remove currency symbols and convert to float)
                    price = self.parse_price(price_text)
                    
                    # Download image
                    image = self.download_image(img_url)
                    
                    if name and price > 0:
                        # Save to database with image BLOB
                        product_data = {
                            "name": name,
                            "price": price,
                            "market": SUPERMARKET,
                            "category": category_name,
                            "image_url": img_url,
                            "description": name,
                            "image": image  # PIL Image object
                        }
                        self.db.insert_product(product_data)
                        self.products_scraped += 1
                        img_status = "📷" if image else "🔗"
                        print(f"✓ {img_status} {name} | {price} TND")
                    
                except NoSuchElementException:
                    continue
                except Exception as e:
                    print(f"Error extracting product: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error scraping page: {e}")
            
    def parse_price(self, price_text):
        """Extract numeric price from text"""
        try:
            # Remove currency symbols and whitespace
            price_clean = price_text.replace('TND', '').replace('DT', '').replace(',', '.').strip()
            return float(price_clean)
        except:
            return 0.0
            
    def scrape_all_categories(self):
        """Main scraping logic - iterate through all categories"""
        try:
            print(f"Opening {URL}...")
            self.driver.get(URL)
            self.wait_for_loading_overlay()
            time.sleep(2)  # Let page fully load
            
            # Find all category links
            category_links = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, ".category-menu-list ul li a")
                )
            )
            
            # Store category names (DOM will refresh after clicks)
            category_names = [link.text.split('(')[0].strip() for link in category_links]
            print(f"Found {len(category_names)} categories: {', '.join(category_names)}")
            
            # Iterate through each category
            for i in range(len(category_names)):
                # Re-fetch links to avoid stale element references
                links = self.driver.find_elements(By.CSS_SELECTOR, ".category-menu-list ul li a")
                current_name = category_names[i]
                
                print(f"\n{'='*60}")
                print(f"Navigating to category: {current_name}")
                print(f"{'='*60}")
                
                try:
                    # Scroll to element and click
                    self.driver.execute_script("arguments[0].scrollIntoView();", links[i])
                    time.sleep(0.5)
                    links[i].click()
                    
                    # Wait for AJAX update
                    self.wait_for_loading_overlay()
                    time.sleep(2)  # Safety buffer for JS rendering
                    
                    # Scrape products from this category
                    self.scrape_current_page(current_name)
                    
                except (ElementClickInterceptedException, TimeoutException) as e:
                    print(f"Could not click category {current_name}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error during scraping: {e}")
            
        finally:
            print(f"\n{'='*60}")
            print(f"Scraping Complete!")
            print(f"Total products scraped: {self.products_scraped}")
            print(f"{'='*60}")
            self.cleanup()
            
    def cleanup(self):
        """Close browser and database connection"""
        if self.driver:
            self.driver.quit()
        if self.db:
            self.db.close()

def main():
    print("Starting Mazraa Market Selenium Scraper...")
    print("="*60)
    
    scraper = MazraaSeleniumScraper(headless=HEADLESS)
    scraper.scrape_all_categories()

if __name__ == "__main__":
    main()
