"""
Configurable Carrefour scraper - reads categories from JSON config
"""
import sys
import json
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from data_pipeline.carrefour_scraper import CarrefourScraper


def load_categories(config_file: str = "carrefour_categories.json"):
    """Load categories from JSON config file"""
    config_path = Path(__file__).parent / config_file
    
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return []
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Filter only enabled categories
    enabled_categories = [cat for cat in config['categories'] if cat.get('enabled', True)]
    
    return enabled_categories


def scrape_category(category_info: dict, max_pages: int = 5, auto_detect: bool = True):
    """Scrape a single category with pagination"""
    print(f"\n{'='*60}")
    print(f"📦 Scraping category: {category_info['name']}")
    print(f"{'='*60}")
    
    scraper = CarrefourScraper(base_url=category_info['url'])
    
    # Scrape with auto-detection or fixed pages
    if auto_detect:
        all_products = scraper.scrape_multiple_pages(start_page=1, end_page=max_pages, auto_detect=True)
    else:
        all_products = scraper.scrape_multiple_pages(start_page=1, end_page=max_pages)
    
    # Add category info to products
    for product in all_products:
        product['category'] = category_info['category']
        product['category_name'] = category_info['name']
    
    return all_products


def main():
    print("🚀 Carrefour Tunisia Configurable Scraper")
    print("="*60)
    
    # Load categories from config
    categories = load_categories()
    
    if not categories:
        print("❌ No enabled categories found in config file")
        return
    
    print(f"📋 Categories to scrape: {len(categories)}")
    for cat in categories:
        print(f"   - {cat['name']}")
    print("="*60)
    
    # Ask user for confirmation
    response = input(f"\n⚠️  This will scrape {len(categories)} categories. Continue? (y/n): ")
    if response.lower() != 'y':
        print("❌ Scraping cancelled")
        return
    
    all_products = []
    
    # Scrape each category
    for idx, category in enumerate(categories, 1):
        print(f"\n[{idx}/{len(categories)}] Processing: {category['name']}")
        
        try:
            products = scrape_category(category, max_pages=10, auto_detect=True)
            all_products.extend(products)
            
            print(f"✅ Scraped {len(products)} products from {category['name']}")
            
            # Delay between categories
            if idx < len(categories):
                print("⏳ Waiting 5 seconds before next category...")
                time.sleep(5)
        
        except Exception as e:
            print(f"❌ Error scraping {category['name']}: {str(e)}")
            continue
    
    # Print overall summary
    print("\n" + "="*60)
    print("📊 OVERALL SUMMARY")
    print("="*60)
    print(f"Total products scraped: {len(all_products)}")
    
    # Group by category
    by_category = {}
    for product in all_products:
        cat_name = product.get('category_name', 'Unknown')
        by_category[cat_name] = by_category.get(cat_name, 0) + 1
    
    print("\nProducts by category:")
    for cat_name, count in sorted(by_category.items()):
        print(f"   {cat_name}: {count} products")
    
    if all_products:
        prices = [p['price'] for p in all_products if p.get('price')]
        if prices:
            print(f"\nPrice range: {min(prices):.2f} - {max(prices):.2f} TND")
            print(f"Average price: {sum(prices)/len(prices):.2f} TND")
    
    print("="*60)
    
    # Save to database
    if all_products:
        response = input(f"\n💾 Save {len(all_products)} products to database? (y/n): ")
        if response.lower() != 'y':
            print("❌ Save cancelled")
            return
        
        print(f"\n💾 Saving {len(all_products)} products to database...")
        
        from data_pipeline.product_database import ProductDatabase
        import requests
        from PIL import Image
        import io
        
        db = ProductDatabase()
        saved_count = 0
        
        for product in all_products:
            if not product.get('name') or not product.get('price'):
                continue
            
            try:
                # Download image as BLOB
                image_blob = None
                if product.get('image_url'):
                    try:
                        response = requests.get(product['image_url'], timeout=10)
                        if response.status_code == 200:
                            img = Image.open(io.BytesIO(response.content))
                            img.verify()
                            image_blob = response.content
                    except Exception:
                        pass
                
                db.insert_product({
                    'name': product['name'],
                    'price': product['price'],
                    'market': 'Carrefour',
                    'image_url': product.get('image_url', ''),
                    'image_blob': image_blob,
                    'product_url': product.get('product_url', ''),
                    'description': product['name'],
                    'currency': 'TND',
                    'category': product.get('category', 'general')
                })
                saved_count += 1
                
                if saved_count % 20 == 0:
                    print(f"   ✓ Saved {saved_count}/{len(all_products)} products...")
            
            except Exception as e:
                continue
        
        print(f"✅ Successfully saved {saved_count} products to database!")
        
        print("\n💡 Next steps:")
        print("   1. Run: python browse_database.py")
        print("   2. Run: python load_db_to_qdrant.py")
        print("   3. Your Carrefour products will be searchable in the app!")
    else:
        print("⚠️  No products were scraped.")


if __name__ == "__main__":
    main()
