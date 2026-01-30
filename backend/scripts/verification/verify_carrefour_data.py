"""
Verify Carrefour scraped data before loading to Qdrant
Shows statistics and sample products to ensure data quality
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from data_pipeline.product_database import product_db
from collections import Counter

def verify_carrefour_data():
    """Verify Carrefour products in SQLite database"""
    
    print("\n" + "="*70)
    print("CARREFOUR DATA VERIFICATION")
    print("="*70)
    
    # Get all Carrefour products
    products = product_db.get_products_by_market('Carrefour', limit=5000)
    
    if not products:
        print("\n[ERROR] No Carrefour products found in database!")
        print("Run: python scrape_carrefour_multi.py first")
        return
    
    print(f"\n[OK] Found {len(products)} Carrefour products")
    
    # Statistics
    print("\n" + "-"*70)
    print("STATISTICS")
    print("-"*70)
    
    # Price statistics
    prices = [p['price'] for p in products if p['price']]
    if prices:
        print(f"\nPrice Range:")
        print(f"  Min: {min(prices):.2f} TND")
        print(f"  Max: {max(prices):.2f} TND")
        print(f"  Average: {sum(prices)/len(prices):.2f} TND")
    
    # Products with images
    with_images = sum(1 for p in products if p.get('image_blob'))
    print(f"\nImages:")
    print(f"  Products with images: {with_images}/{len(products)} ({with_images/len(products)*100:.1f}%)")
    
    # Name quality check
    print(f"\nName Quality:")
    names_with_dash = sum(1 for p in products if ' - ' in p['name'])
    print(f"  Products with full name (brand + description): {names_with_dash}/{len(products)} ({names_with_dash/len(products)*100:.1f}%)")
    
    short_names = [p for p in products if len(p['name']) < 10]
    if short_names:
        print(f"  [WARNING] {len(short_names)} products with very short names (< 10 chars)")
    
    # Check for duplicates
    name_counts = Counter(p['name'] for p in products)
    duplicates = {name: count for name, count in name_counts.items() if count > 1}
    if duplicates:
        print(f"\n[WARNING] Found {len(duplicates)} duplicate product names:")
        for name, count in list(duplicates.items())[:5]:
            print(f"  - {name}: {count} times")
    
    # Sample products
    print("\n" + "-"*70)
    print("SAMPLE PRODUCTS (First 10)")
    print("-"*70)
    
    for i, product in enumerate(products[:10], 1):
        has_image = "✓" if product.get('image_blob') else "✗"
        print(f"\n{i}. {product['name']}")
        print(f"   Price: {product['price']:.2f} TND")
        print(f"   Image: {has_image}")
        if product.get('product_url'):
            print(f"   URL: {product['product_url'][:60]}...")
    
    # Products by price range
    print("\n" + "-"*70)
    print("PRICE DISTRIBUTION")
    print("-"*70)
    
    ranges = [
        (0, 5, "0-5 TND"),
        (5, 10, "5-10 TND"),
        (10, 20, "10-20 TND"),
        (20, 50, "20-50 TND"),
        (50, float('inf'), "50+ TND")
    ]
    
    for min_p, max_p, label in ranges:
        count = sum(1 for p in products if min_p <= p['price'] < max_p)
        percentage = count / len(products) * 100
        bar = "█" * int(percentage / 2)
        print(f"  {label:12} {count:4} products {bar} {percentage:.1f}%")
    
    # Data quality score
    print("\n" + "-"*70)
    print("DATA QUALITY SCORE")
    print("-"*70)
    
    score = 0
    max_score = 5
    
    # Check 1: All products have prices
    if all(p['price'] > 0 for p in products):
        score += 1
        print("  [OK] All products have valid prices")
    else:
        print("  [WARNING] Some products missing prices")
    
    # Check 2: Most products have images
    if with_images / len(products) > 0.8:
        score += 1
        print("  [OK] Most products have images (>80%)")
    else:
        print("  [WARNING] Many products missing images")
    
    # Check 3: Most products have full names
    if names_with_dash / len(products) > 0.7:
        score += 1
        print("  [OK] Most products have full names (>70%)")
    else:
        print("  [WARNING] Many products have incomplete names")
    
    # Check 4: No excessive duplicates
    if len(duplicates) < len(products) * 0.1:
        score += 1
        print("  [OK] Low duplicate rate (<10%)")
    else:
        print("  [WARNING] High duplicate rate")
    
    # Check 5: Reasonable price range
    if prices and min(prices) > 0 and max(prices) < 1000:
        score += 1
        print("  [OK] Prices in reasonable range")
    else:
        print("  [WARNING] Some prices seem unusual")
    
    print(f"\n  Overall Score: {score}/{max_score} ({score/max_score*100:.0f}%)")
    
    if score >= 4:
        print("\n  [OK] Data quality is GOOD - Safe to load to Qdrant")
    elif score >= 3:
        print("\n  [WARNING] Data quality is ACCEPTABLE - Review warnings above")
    else:
        print("\n  [ERROR] Data quality is POOR - Fix issues before loading")
    
    # Recommendation
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    
    if score >= 3:
        print("\n1. Data looks good! Load to Qdrant:")
        print("   python load_carrefour_to_qdrant.py")
        print("\n2. Verify in Qdrant:")
        print("   python count_qdrant_products.py")
    else:
        print("\n1. Fix data quality issues")
        print("2. Re-scrape if needed:")
        print("   python scrape_carrefour_multi.py")
        print("3. Run this verification again")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    verify_carrefour_data()
