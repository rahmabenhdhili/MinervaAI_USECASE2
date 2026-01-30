"""
Load retail market products with images to Qdrant.
Memory-optimized version with batch processing.
Uses YOUR cluster directly.
"""
import sys
from pathlib import Path
import io
import gc

sys.path.append(str(Path(__file__).parent))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from app.models.schemas import Product
from data_pipeline.product_database import product_db

# YOUR cluster
QDRANT_URL = "https://12967839-b821-4039-ba74-1fb878555326.europe-west3-0.gcp.cloud.qdrant.io:6333"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.aF0apPZOZSmSPYXGgLuYmbEylssUeNgmABoYFieFb_A"
COLLECTION_NAME = "products_supermarket"

def load_retail_markets():
    """Load products with images to Qdrant - memory optimized"""
    print("\n🔄 LOADING RETAIL MARKET PRODUCTS TO QDRANT")
    print("=" * 60)
    print(f"Cluster: {QDRANT_URL}")
    print(f"Collection: {COLLECTION_NAME}")
    print("=" * 60)
    
    # Connect to YOUR cluster
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        timeout=60
    )
    
    # Step 1: Get products with images only
    print("\n1. Loading products with images from database...")
    cursor = product_db.conn.cursor()
    cursor.execute("""
        SELECT * FROM products 
        WHERE image_blob IS NOT NULL
        ORDER BY updated_at DESC
    """)
    db_products = [dict(row) for row in cursor.fetchall()]
    print(f"   ✓ Found {len(db_products)} products with images")
    
    if len(db_products) == 0:
        print("\n   ⚠️ No products with images! Run scraper first")
        return
    
    # Step 2: Recreate Qdrant collection
    print("\n2. Setting up Qdrant collection...")
    try:
        client.delete_collection(COLLECTION_NAME)
        print("   ✓ Deleted old collection")
    except:
        print("   ℹ️ No old collection to delete")
    
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=768, distance=Distance.COSINE)
    )
    print(f"   ✓ Created collection: {COLLECTION_NAME}")
    
    # Step 3: Process in small batches to avoid memory issues
    print("\n3. Processing products in batches...")
    batch_size = 50  # Small batches to avoid memory issues
    total_inserted = 0
    
    # Import SigLIP only when needed
    from app.services.siglip_service import siglip_service
    
    for batch_start in range(0, len(db_products), batch_size):
        batch_end = min(batch_start + batch_size, len(db_products))
        batch_products_data = db_products[batch_start:batch_end]
        
        print(f"\n   Processing batch {batch_start//batch_size + 1}/{(len(db_products)-1)//batch_size + 1}")
        print(f"   Products {batch_start+1}-{batch_end} of {len(db_products)}")
        
        products = []
        embeddings = []
        
        for db_prod in batch_products_data:
            try:
                # Convert to Product schema
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
                
                # Get image and create embedding
                image = product_db.get_product_image(db_prod['product_id'])
                if image:
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format='PNG')
                    img_bytes = img_byte_arr.getvalue()
                    
                    # Generate visual embedding
                    embedding = siglip_service.embed_image(img_bytes, preprocess=True)
                    
                    products.append(product)
                    embeddings.append(embedding)
                    
            except Exception as e:
                print(f"   ⚠️ Failed to process {db_prod['name']}: {e}")
                continue
        
        # Insert batch into Qdrant
        if products:
            qdrant_service.batch_insert_products(
                collection_name=settings.COLLECTION_SUPERMARKET,
                products=products,
                embeddings=embeddings
            )
            total_inserted += len(products)
            print(f"   ✓ Inserted {len(products)} products (Total: {total_inserted})")
        
        # Clear memory
        del products
        del embeddings
        gc.collect()
    
    # Step 4: Verify
    print("\n4. Verifying Qdrant collection...")
    info = qdrant_service.get_collection_info(settings.COLLECTION_SUPERMARKET)
    print(f"   Collection info: {info}")
    
    print("\n" + "=" * 60)
    print("✅ RETAIL MARKETS COLLECTION READY")
    print("=" * 60)
    print(f"\n✓ {total_inserted} products indexed in '{settings.COLLECTION_SUPERMARKET}'")
    print(f"✓ Cluster: {settings.QDRANT_URL}")
    print("✓ SigLIP visual embeddings generated")
    print("✓ Ready for Shopping Mode image search")
    print("\nNext steps:")
    print("  1. Start API: uvicorn app.main:app --reload")
    print("  2. Upload product images in Shopping Mode")
    print("  3. Get instant visual similarity matches!")

if __name__ == "__main__":
    load_retail_markets()
