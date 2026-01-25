"""
Weekly scraping and ingestion script.
Run this once per week to update supermarket product database.

WORKFLOW:
1. Scrape all supermarket websites → Save to SQLite
2. Load products from SQLite database
3. Generate CLIP embeddings from stored images
4. Update Qdrant vector database
"""
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.qdrant_service import qdrant_service
from app.services.clip_service import clip_service
from app.services.embedding_service import embedding_service
from app.core.config import settings
from data_pipeline.web_scraper import run_weekly_scrape
from data_pipeline.product_database import product_db
from app.models.schemas import Product
import io

async def scrape_and_ingest_supermarkets():
    """
    Main weekly job:
    1. Scrape supermarket websites (saves to SQLite automatically)
    2. Load products from SQLite database
    3. Generate CLIP embeddings from product images
    4. Update Qdrant vector database
    """
    print("\n🚀 WEEKLY SCRAPE AND INGEST JOB")
    print("=" * 60)
    print("This job will:")
    print("  1. Scrape all supermarket websites")
    print("  2. Update SQLite database with fresh data")
    print("  3. Generate CLIP embeddings")
    print("  4. Update Qdrant for vector search")
    print("=" * 60)
    
    try:
        # STEP 1: Scrape all markets (automatically saves to SQLite)
        print("\n" + "=" * 60)
        print("STEP 1: SCRAPING SUPERMARKET WEBSITES")
        print("=" * 60)
        
        all_market_products = await run_weekly_scrape()
        
        scraped_count = sum(len(p) for p in all_market_products.values())
        print(f"\n✓ Scraping complete! Scraped {scraped_count} products")
        
        # STEP 2: Load products from SQLite database
        print("\n" + "=" * 60)
        print("STEP 2: LOADING PRODUCTS FROM DATABASE")
        print("=" * 60)
        
        db_products = product_db.get_all_products(limit=5000)
        print(f"✓ Loaded {len(db_products)} products from database")
        
        if not db_products:
            print("\n⚠️ No products in database. Using sample data as fallback...")
            from data_pipeline.supermarket_data_loader import supermarket_data_loader
            sample_products = supermarket_data_loader.get_sample_supermarket_products()
            
            # Convert to Product schema
            products = sample_products
            product_images = [None] * len(products)
        else:
            # Convert database records to Product schema
            products = []
            product_images = []
            
            for db_prod in db_products:
                product = Product(
                    id=db_prod['product_id'],
                    name=db_prod['name'],
                    description=db_prod['description'],
                    category=db_prod['category'],
                    price=db_prod['price'],
                    market=db_prod['market'],
                    image_path=db_prod.get('image_url'),
                    specs=None,
                    brand=db_prod.get('brand')
                )
                products.append(product)
                
                # Get image from database
                image = product_db.get_product_image(db_prod['product_id'])
                product_images.append(image)
            
            print(f"✓ Prepared {len(products)} products for Qdrant")
        
        # STEP 3: Update Qdrant collection
        print("\n" + "=" * 60)
        print("STEP 3: UPDATING QDRANT VECTOR DATABASE")
        print("=" * 60)
        
        # Recreate collection with fresh data
        print("Recreating collection...")
        try:
            qdrant_service.client.delete_collection(settings.COLLECTION_SUPERMARKET)
            print("  ✓ Deleted old collection")
        except:
            print("  ℹ️ No old collection to delete")
        
        qdrant_service.create_collection(settings.COLLECTION_SUPERMARKET, use_clip=True)
        print("  ✓ Created new collection")
        
        # STEP 4: Generate CLIP embeddings
        print("\nGenerating CLIP embeddings...")
        embeddings = []
        
        for i, (product, image) in enumerate(zip(products, product_images)):
            if image is not None:
                # Use actual product image from database
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()
                embedding = clip_service.embed_image(img_bytes)
            else:
                # Fallback to text embedding
                text = embedding_service.create_product_text(product.model_dump())
                embedding = clip_service.embed_text(text)
            
            embeddings.append(embedding)
            
            if (i + 1) % 50 == 0:
                print(f"  Processed {i + 1}/{len(products)} products...")
        
        print(f"  ✓ Generated {len(embeddings)} embeddings")
        
        # STEP 5: Insert into Qdrant
        print("\nInserting into Qdrant...")
        qdrant_service.batch_insert_products(
            collection_name=settings.COLLECTION_SUPERMARKET,
            products=products,
            embeddings=embeddings
        )
        
        print(f"  ✓ Inserted {len(products)} products into Qdrant")
        
        # Show final statistics
        print("\n" + "=" * 60)
        print("📊 FINAL STATISTICS")
        print("=" * 60)
        
        db_stats = product_db.get_statistics()
        print(f"\nSQLite Database:")
        print(f"  Total products: {db_stats['total_products']}")
        print(f"  Products with promos: {db_stats['products_with_promos']}")
        print(f"\n  By market:")
        for market, count in db_stats['by_market'].items():
            avg_price = db_stats['avg_prices'].get(market, 0)
            print(f"    {market}: {count} products (avg: {avg_price} TND)")
        
        qdrant_info = qdrant_service.get_collection_info(settings.COLLECTION_SUPERMARKET)
        print(f"\nQdrant Vector Database:")
        print(f"  {qdrant_info}")
        
        print("\n" + "=" * 60)
        print("✅ WEEKLY SCRAPE AND INGEST COMPLETE")
        print("=" * 60)
        print("\n📅 Schedule this script to run weekly:")
        print("  Windows: Task Scheduler")
        print("  Linux/Mac: cron job")
        print("\n💡 Products are now up-to-date with:")
        print("  ✓ Latest prices")
        print("  ✓ Current promotions")
        print("  ✓ Fresh product images")
        print("  ✓ Vector embeddings for search")
        
    except Exception as e:
        print(f"\n❌ Error during scrape and ingest: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Entry point"""
    asyncio.run(scrape_and_ingest_supermarkets())

if __name__ == "__main__":
    main()
