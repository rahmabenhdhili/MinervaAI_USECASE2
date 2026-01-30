"""
Inspect Qdrant data - show products by market with samples
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from app.services.qdrant_service import qdrant_service
from app.core.config import settings
from collections import defaultdict

def inspect_qdrant():
    """Show what data is in Qdrant for each market"""
    
    print("\n" + "="*70)
    print("QDRANT DATA INSPECTION")
    print("="*70)
    
    print(f"\nCollection: {settings.COLLECTION_SUPERMARKET}")
    
    # Scroll through all products
    print("\n[LOADING] Fetching all products from Qdrant...")
    
    all_products = []
    offset = None
    
    while True:
        result = qdrant_service.client.scroll(
            collection_name=settings.COLLECTION_SUPERMARKET,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )
        
        points, next_offset = result
        
        if not points:
            break
        
        all_products.extend(points)
        
        if next_offset is None:
            break
        
        offset = next_offset
        print(f"  Loaded {len(all_products)} products...")
    
    print(f"\n[OK] Total products in Qdrant: {len(all_products)}")
    
    # Group by market
    by_market = defaultdict(list)
    
    for point in all_products:
        market = point.payload.get('market', 'Unknown')
        by_market[market].append(point.payload)
    
    # Show statistics
    print("\n" + "-"*70)
    print("PRODUCTS BY MARKET")
    print("-"*70)
    
    for market in sorted(by_market.keys()):
        products = by_market[market]
        print(f"\n{market}: {len(products)} products")
        
        # Price statistics
        prices = [p.get('price', 0) for p in products if p.get('price')]
        if prices:
            print(f"  Price range: {min(prices):.2f} - {max(prices):.2f} TND")
            print(f"  Average price: {sum(prices)/len(prices):.2f} TND")
        
        # Sample products
        print(f"  Sample products:")
        for i, product in enumerate(products[:5], 1):
            name = product.get('name', 'Unknown')[:50]
            price = product.get('price', 0)
            print(f"    {i}. {name} - {price:.2f} TND")
    
    # Show categories
    print("\n" + "-"*70)
    print("PRODUCTS BY CATEGORY")
    print("-"*70)
    
    by_category = defaultdict(int)
    for point in all_products:
        category = point.payload.get('category', 'unknown')
        by_category[category] += 1
    
    for category in sorted(by_category.keys()):
        count = by_category[category]
        print(f"  {category}: {count} products")
    
    # Show brands
    print("\n" + "-"*70)
    print("TOP BRANDS")
    print("-"*70)
    
    by_brand = defaultdict(int)
    for point in all_products:
        brand = point.payload.get('brand')
        if brand:
            by_brand[brand] += 1
    
    # Top 10 brands
    top_brands = sorted(by_brand.items(), key=lambda x: x[1], reverse=True)[:10]
    for brand, count in top_brands:
        print(f"  {brand}: {count} products")
    
    # Search for specific product
    print("\n" + "="*70)
    print("SEARCH TEST")
    print("="*70)
    
    search_term = "café"
    print(f"\nSearching for '{search_term}'...")
    
    matching = []
    for point in all_products:
        name = point.payload.get('name', '').lower()
        if search_term.lower() in name:
            matching.append(point.payload)
    
    print(f"Found {len(matching)} products matching '{search_term}':")
    for i, product in enumerate(matching[:10], 1):
        print(f"  {i}. {product.get('name')} - {product.get('price'):.2f} TND ({product.get('market')})")
    
    # Export option
    print("\n" + "="*70)
    print("EXPORT OPTIONS")
    print("="*70)
    print("\nTo export all products to JSON:")
    print("  python inspect_qdrant_data.py --export products.json")
    print("\nTo search for a specific product:")
    print("  python inspect_qdrant_data.py --search 'product name'")
    print("\n" + "="*70 + "\n")

def export_to_json(filename):
    """Export all Qdrant data to JSON"""
    import json
    
    print(f"\n[EXPORTING] Fetching all products...")
    
    all_products = []
    offset = None
    
    while True:
        result = qdrant_service.client.scroll(
            collection_name=settings.COLLECTION_SUPERMARKET,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )
        
        points, next_offset = result
        
        if not points:
            break
        
        all_products.extend([p.payload for p in points])
        
        if next_offset is None:
            break
        
        offset = next_offset
    
    # Save to file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_products, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Exported {len(all_products)} products to {filename}")

def search_products(search_term):
    """Search for products by name"""
    
    print(f"\n[SEARCHING] Looking for '{search_term}'...")
    
    all_products = []
    offset = None
    
    while True:
        result = qdrant_service.client.scroll(
            collection_name=settings.COLLECTION_SUPERMARKET,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )
        
        points, next_offset = result
        
        if not points:
            break
        
        all_products.extend(points)
        
        if next_offset is None:
            break
        
        offset = next_offset
    
    # Search
    matching = []
    for point in all_products:
        name = point.payload.get('name', '').lower()
        if search_term.lower() in name:
            matching.append(point.payload)
    
    print(f"\n[FOUND] {len(matching)} products matching '{search_term}':\n")
    
    # Group by market
    by_market = defaultdict(list)
    for product in matching:
        market = product.get('market', 'Unknown')
        by_market[market].append(product)
    
    for market in sorted(by_market.keys()):
        products = by_market[market]
        print(f"\n{market} ({len(products)} products):")
        for i, product in enumerate(products, 1):
            print(f"  {i}. {product.get('name')} - {product.get('price'):.2f} TND")

if __name__ == "__main__":
    import sys
    
    if "--export" in sys.argv:
        idx = sys.argv.index("--export")
        filename = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "qdrant_export.json"
        export_to_json(filename)
    elif "--search" in sys.argv:
        idx = sys.argv.index("--search")
        search_term = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else ""
        if search_term:
            search_products(search_term)
        else:
            print("Please provide a search term: --search 'product name'")
    else:
        inspect_qdrant()
