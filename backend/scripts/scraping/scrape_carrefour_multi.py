"""
Multi-category Carrefour scraper with automatic pagination
Scrapes multiple product categories from Carrefour Tunisia
"""
import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from data_pipeline.carrefour_scraper import CarrefourScraper


# Categories to scrape
CATEGORIES = [
    {
        'name': 'Eaux',
        'url': 'https://www.carrefour.tn/boissons/eaux.html',
        'category': 'boissons'
    },
    {
        'name': 'Café',
        'url': 'https://www.carrefour.tn/epicerie-sucree/cafe.html',
        'category': 'epicerie_sucree'
    },
    {
        'name': 'Blé et Semoule',
        'url': 'https://www.carrefour.tn/epicerie-salee/ble-et-semoule.html',
        'category': 'epicerie_salee'
    },
    {
        'name': 'Thés et Infusions',
        'url': 'https://www.carrefour.tn/epicerie-sucree/thes-et-infusions.html',
        'category': 'epicerie_sucree'
    }
]


def scrape_category(category_info: dict, max_pages: int = 5):
    """Scrape a single category with pagination"""
    print(f"\n{'='*60}")
    print(f"📦 Scraping category: {category_info['name']}")
    print(f"{'='*60}")
    
    scraper = CarrefourScraper(base_url=category_info['url'])
    
    # Scrape multiple pages
    all_products = scraper.scrape_multiple_pages(start_page=1, end_page=max_pages)
    
    # Add category info to products
    for product in all_products:
        product['category'] = category_info['category']
        product['category_name'] = category_info['name']
    
    return all_products


def main():
    print("🚀 Carrefour Tunisia Multi-Category Scraper")
    print("="*60)
    print(f"📋 Categories to scrape: {len(CATEGORIES)}")
    for cat in CATEGORIES:
        print(f"   - {cat['name']}")
    print("="*60)
    
    all_products = []
    
    # Scrape each category
    for idx, category in enumerate(CATEGORIES, 1):
        print(f"\n[{idx}/{len(CATEGORIES)}] Processing: {category['name']}")
        
        try:
            products = scrape_category(category, max_pages=3)
            all_products.extend(products)
            
            print(f"✅ Scraped {len(products)} products from {category['name']}")
            
            # Delay between categories to be polite
            if idx < len(CATEGORIES):
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
    for cat_name, count in by_category.items():
        print(f"   {cat_name}: {count} products")
    
    if all_products:
        prices = [p['price'] for p in all_products if p.get('price')]
        if prices:
            print(f"\nPrice range: {min(prices):.2f} - {max(prices):.2f} TND")
            print(f"Average price: {sum(prices)/len(prices):.2f} TND")
    
    print("="*60)
    
    # Save to database
    if all_products:
        print(f"\n💾 Saving {len(all_products)} products to database...")
        
        # Use the scraper's database connection
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
                    except Exception as e:
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
