"""
Interactive database browser
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from data_pipeline.product_database import product_db
from PIL import Image

def main():
    """Interactive database browser"""
    print("\n📊 SQLITE DATABASE BROWSER")
    print("=" * 60)
    
    while True:
        print("\nOptions:")
        print("  1. View statistics")
        print("  2. List all products")
        print("  3. Search by market")
        print("  4. Search by name")
        print("  5. View product details")
        print("  6. Export product image")
        print("  7. View products with promos")
        print("  8. Exit")
        
        choice = input("\nEnter choice (1-8): ").strip()
        
        if choice == "1":
            # Statistics
            stats = product_db.get_statistics()
            print("\n📊 Database Statistics:")
            print(f"  Total products: {stats['total_products']}")
            print(f"  Products with promos: {stats['products_with_promos']}")
            print(f"\n  By market:")
            for market, count in stats['by_market'].items():
                avg = stats['avg_prices'].get(market, 0)
                print(f"    {market:15s}: {count:4d} products (avg: {avg:6.2f} TND)")
        
        elif choice == "2":
            # List all
            limit = input("  How many products? (default 10): ").strip() or "10"
            products = product_db.get_all_products(limit=int(limit))
            
            print(f"\n📦 Products (showing {len(products)}):")
            for p in products:
                print(f"\n  {p['name']}")
                print(f"    ID: {p['product_id']}")
                print(f"    Price: {p['price']} TND")
                print(f"    Market: {p['market']}")
                if p['brand']:
                    print(f"    Brand: {p['brand']}")
                if p['promo']:
                    print(f"    Promo: {p['promo']}")
        
        elif choice == "3":
            # Search by market
            market = input("  Enter market name (aziza/mg/geant/etc): ").strip()
            limit = input("  How many products? (default 10): ").strip() or "10"
            
            products = product_db.get_products_by_market(market, limit=int(limit))
            
            if products:
                print(f"\n📦 {len(products)} products from {market}:")
                for p in products:
                    print(f"  • {p['name']} - {p['price']} TND")
            else:
                print(f"\n  No products found in {market}")
        
        elif choice == "4":
            # Search by name
            search = input("  Enter search term: ").strip()
            
            import sqlite3
            conn = sqlite3.connect(str(product_db.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM products 
                WHERE name LIKE ? 
                LIMIT 20
            """, (f"%{search}%",))
            
            products = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            if products:
                print(f"\n🔍 Found {len(products)} products:")
                for p in products:
                    print(f"  • {p['name']} - {p['price']} TND ({p['market']})")
            else:
                print(f"\n  No products found matching '{search}'")
        
        elif choice == "5":
            # View details
            product_id = input("  Enter product ID: ").strip()
            product = product_db.get_product_by_id(product_id)
            
            if product:
                print(f"\n📦 Product Details:")
                print(f"  ID: {product['product_id']}")
                print(f"  Name: {product['name']}")
                print(f"  Description: {product['description']}")
                print(f"  Brand: {product['brand']}")
                print(f"  Quantity: {product['quantity']}")
                print(f"  Price: {product['price']} {product['currency']}")
                if product['old_price']:
                    print(f"  Old Price: {product['old_price']} {product['currency']}")
                print(f"  Market: {product['market']}")
                print(f"  Category: {product['category']}")
                if product['promo']:
                    print(f"  Promo: {product['promo']}")
                print(f"  Image URL: {product['image_url']}")
                print(f"  Has Image: {product['image_blob'] is not None}")
                print(f"  Scraped: {product['scraped_at']}")
                print(f"  Updated: {product['updated_at']}")
            else:
                print(f"\n  Product not found: {product_id}")
        
        elif choice == "6":
            # Export image
            product_id = input("  Enter product ID: ").strip()
            output = input("  Output filename (e.g., product.jpg): ").strip()
            
            image = product_db.get_product_image(product_id)
            
            if image:
                image.save(output)
                print(f"\n  ✓ Image saved to {output}")
                print(f"    Size: {image.size}")
            else:
                print(f"\n  No image found for {product_id}")
        
        elif choice == "7":
            # Products with promos
            import sqlite3
            conn = sqlite3.connect(str(product_db.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM products 
                WHERE promo IS NOT NULL 
                ORDER BY market, price
            """)
            
            products = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            if products:
                print(f"\n🎉 {len(products)} products with promotions:")
                for p in products:
                    print(f"\n  {p['name']}")
                    print(f"    Price: {p['price']} TND", end="")
                    if p['old_price']:
                        print(f" (was {p['old_price']} TND)")
                    else:
                        print()
                    print(f"    Promo: {p['promo']}")
                    print(f"    Market: {p['market']}")
            else:
                print("\n  No products with promotions found")
        
        elif choice == "8":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("\n  Invalid choice. Please enter 1-8.")

if __name__ == "__main__":
    main()
