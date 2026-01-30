"""
Product database management CLI tool.
Use this to view, manage, and maintain the scraped products database.
"""
import sys
from pathlib import Path
import argparse

sys.path.append(str(Path(__file__).parent))

from data_pipeline.product_database import product_db
from PIL import Image

def show_stats():
    """Show database statistics"""
    print("\n📊 DATABASE STATISTICS")
    print("=" * 60)
    
    stats = product_db.get_statistics()
    print(f"Total products: {stats['total_products']}")
    print(f"Products with promotions: {stats['products_with_promos']}")
    
    print(f"\nProducts by market:")
    for market, count in sorted(stats['by_market'].items()):
        avg_price = stats['avg_prices'].get(market, 0)
        print(f"  {market:15s}: {count:4d} products (avg: {avg_price:6.2f} TND)")
    
    print("=" * 60)

def list_products(market=None, limit=10):
    """List products from database"""
    print(f"\n📦 PRODUCTS (limit: {limit})")
    print("=" * 60)
    
    if market:
        products = product_db.get_products_by_market(market, limit=limit)
        print(f"Market: {market}")
    else:
        products = product_db.get_all_products(limit=limit)
        print("All markets")
    
    print(f"Showing {len(products)} products:\n")
    
    for prod in products:
        print(f"{prod['name']}")
        print(f"  Market: {prod['market']}")
        print(f"  Price: {prod['price']} TND")
        if prod['brand']:
            print(f"  Brand: {prod['brand']}")
        if prod['promo']:
            print(f"  Promo: {prod['promo']}")
        print(f"  Has image: {prod['image_blob'] is not None}")
        print()

def clear_market(market):
    """Clear all products from a specific market"""
    print(f"\n⚠️  Clearing all products from {market}...")
    confirm = input("Are you sure? (yes/no): ")
    
    if confirm.lower() == 'yes':
        product_db.clear_market(market)
        print(f"✓ Cleared {market}")
    else:
        print("Cancelled")

def clear_all():
    """Clear entire database"""
    print("\n⚠️  WARNING: This will delete ALL products from the database!")
    confirm = input("Are you sure? Type 'DELETE ALL' to confirm: ")
    
    if confirm == 'DELETE ALL':
        product_db.clear_all()
        print("✓ Database cleared")
    else:
        print("Cancelled")

def export_image(product_id, output_path):
    """Export a product image to file"""
    image = product_db.get_product_image(product_id)
    
    if image:
        image.save(output_path)
        print(f"✓ Exported image to {output_path}")
    else:
        print(f"❌ No image found for product {product_id}")

def main():
    parser = argparse.ArgumentParser(description="Manage scraped products database")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Stats command
    subparsers.add_parser('stats', help='Show database statistics')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List products')
    list_parser.add_argument('--market', help='Filter by market')
    list_parser.add_argument('--limit', type=int, default=10, help='Number of products to show')
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear products')
    clear_parser.add_argument('--market', help='Market to clear (or --all for everything)')
    clear_parser.add_argument('--all', action='store_true', help='Clear entire database')
    
    # Export image command
    export_parser = subparsers.add_parser('export-image', help='Export product image')
    export_parser.add_argument('product_id', help='Product ID')
    export_parser.add_argument('output', help='Output file path')
    
    args = parser.parse_args()
    
    if args.command == 'stats':
        show_stats()
    
    elif args.command == 'list':
        list_products(market=args.market, limit=args.limit)
    
    elif args.command == 'clear':
        if args.all:
            clear_all()
        elif args.market:
            clear_market(args.market)
        else:
            print("Error: Specify --market or --all")
    
    elif args.command == 'export-image':
        export_image(args.product_id, args.output)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
