"""
Load Aziza products with IMAGES to Qdrant
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from data_pipeline.product_database import product_db
from app.services.qdrant_service import qdrant_service
from app.services.siglip_service import siglip_service
from app.core.config import settings
from app.models.schemas import Product
from qdrant_client.models import Filter, FieldCondition
from PIL import Image
import io

def main():
    print("\n[LOADING] Loading Aziza Products with IMAGES to Qdrant")
    print("=" * 70)
    
    # Step 1: Delete old Aziza embeddings
    print("\n[STEP 1] Deleting old Aziza embeddings from Qdrant...")
    try:
        qdrant_service.client.delete(
            collection_name=settings.COLLECTION_SUPERMARKET,
            points_selector=Filter(
                must=[FieldCondition(key='market', match={'value': 'aziza'})]
            )
        )
        print("   [OK] Deleted old Aziza embeddings")
    except Exception as e:
        print(f"   [WARNING] Error: {e}")
    
    # Step 2: Get Aziza products from SQLite
    print("\n[STEP 2] Loading Aziza products from SQLite...")
    aziza_products = product_db.get_products_by_market('aziza', limit=500)
    print(f"   Found {len(aziza_products)} Aziza products")
    
    # Filter only products with images
    products_with_images = [p for p in aziza_products if p.get('image_blob')]  # Changed from image_data to image_blob
    print(f"   Products with images: {len(products_with_images)}")
    
    if not products_with_images:
        print("\n   [ERROR] No products with images found!")
        return
    
    # Step 3: Load to Qdrant with IMAGE embeddings
    print("\n[STEP 3] Loading to Qdrant with IMAGE embeddings...")
    
    batch_size = 10
    total_loaded = 0
    failed = 0
    
    for i in range(0, len(products_with_images), batch_size):
        batch = products_with_images[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(products_with_images) + batch_size - 1) // batch_size
        
        print(f"\n   [BATCH] Batch {batch_num}/{total_batches} ({len(batch)} products)...")
        
        products_to_insert = []
        embeddings_to_insert = []
        
        for product_dict in batch:
            try:
                # Create Product object
                product = Product(
                    id=str(product_dict["id"]),
                    name=product_dict["name"],
                    description=product_dict.get("description", ""),
                    category=product_dict.get("category", "unknown"),
                    price=product_dict["price"],
                    market=product_dict["market"],
                    image_path=product_dict.get("image_path"),
                    specs=product_dict.get("specs", {}),
                    brand=product_dict.get("brand")
                )
                
                # Generate IMAGE embedding
                # image_blob is already bytes, pass it directly
                embedding = siglip_service.embed_image(product_dict["image_blob"])
                
                products_to_insert.append(product)
                embeddings_to_insert.append(embedding)
                
                print(f"      [OK] {product.name[:50]}")
            
            except Exception as e:
                print(f"      [ERROR] Error: {str(e)[:50]}")
                failed += 1
        
        # Insert batch
        if products_to_insert:
            try:
                qdrant_service.batch_insert_products(
                    collection_name=settings.COLLECTION_SUPERMARKET,
                    products=products_to_insert,
                    embeddings=embeddings_to_insert
                )
                total_loaded += len(products_to_insert)
                print(f"      [OK] Inserted {len(products_to_insert)} products")
            except Exception as e:
                print(f"      [ERROR] Batch insert failed: {e}")
                failed += len(products_to_insert)
    
    print(f"\n   [OK] Load complete!")
    print(f"      Total loaded: {total_loaded}")
    print(f"      Failed: {failed}")
    
    # Step 4: Verify
    print("\n[STEP 4] Verifying...")
    query_embedding = siglip_service.embed_text("biscuit")
    results = qdrant_service.search_products(
        collection_name=settings.COLLECTION_SUPERMARKET,
        query_vector=query_embedding,
        market="aziza",
        limit=5
    )
    
    print(f"   Search test: Found {len(results)} Aziza products")
    if results:
        print(f"   Sample:")
        for i, result in enumerate(results[:3], 1):
            product = result["payload"]
            print(f"      {i}. {product['name'][:50]} - {product['price']} TND")
    
    # Count all markets
    print("\n[STATS] Final Statistics:")
    for market in ["aziza", "Carrefour", "Mazraa Market"]:
        market_results = qdrant_service.search_products(
            collection_name=settings.COLLECTION_SUPERMARKET,
            query_vector=query_embedding,
            market=market,
            limit=2000
        )
        print(f"   {market}: {len(market_results)} products")
    
    print("\n" + "=" * 70)
    print("[OK] AZIZA LOADING COMPLETE!")
    print("=" * 70)
    print("\n[SUCCESS] Aziza now has IMAGE embeddings for accurate visual search!")
    print("   Restart your API server and test in the frontend.")
    print("=" * 70)

if __name__ == "__main__":
    main()
