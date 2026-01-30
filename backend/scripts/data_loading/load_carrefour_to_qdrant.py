"""
Quick script to load all Carrefour products to Qdrant
Use this after scraping Carrefour products
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from load_recent_to_qdrant import load_recent_to_qdrant
from data_pipeline.product_database import product_db


def main():
    print("\n🛒 LOADING CARREFOUR PRODUCTS TO QDRANT")
    print("=" * 60)
    
    # Get all Carrefour products
    print("\n1. Checking Carrefour products in database...")
    all_products = product_db.get_all_products(limit=10000)
    carrefour_products = [p for p in all_products if p['market'] == 'Carrefour']
    
    if not carrefour_products:
        print("   ⚠️ No Carrefour products found in database")
        print("   💡 Run: python scrape_carrefour_config.py first")
        return
    
    print(f"   ✓ Found {len(carrefour_products)} Carrefour products")
    
    # Group by category
    by_category = {}
    for prod in carrefour_products:
        cat = prod.get('category', 'unknown')
        by_category[cat] = by_category.get(cat, 0) + 1
    
    print("\n   Products by category:")
    for cat, count in sorted(by_category.items()):
        print(f"      {cat}: {count} products")
    
    # Ask for confirmation
    response = input(f"\n   Load {len(carrefour_products)} Carrefour products to Qdrant? (y/n): ")
    if response.lower() != 'y':
        print("   ❌ Cancelled")
        return
    
    # Load to Qdrant
    product_ids = [p['product_id'] for p in carrefour_products]
    load_recent_to_qdrant(product_ids=product_ids)


if __name__ == "__main__":
    main()
