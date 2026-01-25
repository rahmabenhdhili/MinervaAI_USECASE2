"""
Load existing SQLite data into Qdrant for similarity search.
Use this to update Qdrant without re-scraping.
"""
import sys
from pathlib import Path
import io

sys.path.append(str(Path(__file__).parent))

from app.services.qdrant_service import qdrant_service
from app.services.hybrid_embedding_service import hybrid_embedding_service
from app.services.embedding_service import embedding_service
from app.core.config import settings
from app.models.schemas import Product
from data_pipeline.product_database import product_db

def load_to_qdrant():
    """Load SQLite products into Qdrant"""
    print("\n🔄 LOADING SQLITE DATA TO QDRANT")
    print("=" * 60)
    
    # Step 1: Check database
    print("\n1. Checking SQLite database...")
    db_stats = product_db.get_statistics()
    print(f"   Total products: {db_stats['total_products']}")
    
    if db_stats['total_products'] == 0:
        print("\n   ⚠️ Database is empty! Run test_database.py first")
        return
    
    # Step 2: Load products from database
    print("\n2. Loading products from database...")
    db_products = product_db.get_all_products(limit=5000)
    print(f"   ✓ Loaded {len(db_products)} products")
    
    # Step 3: Convert to Product schema
    print("\n3. Converting to Product schema...")
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
    
    print(f"   ✓ Prepared {len(products)} products")
    
    # Step 4: Recreate Qdrant collection
    print("\n4. Recreating Qdrant collection...")
    try:
        qdrant_service.client.delete_collection(settings.COLLECTION_SUPERMARKET)
        print("   ✓ Deleted old collection")
    except:
        print("   ℹ️ No old collection to delete")
    
    qdrant_service.create_collection(settings.COLLECTION_SUPERMARKET, use_clip=True)
    print("   ✓ Created new collection")
    
    # Step 5: Generate hybrid embeddings (60% image + 30% text + 10% packaging)
    print("\n5. Generating hybrid embeddings...")
    print("   Combining: 60% image + 30% text + 10% packaging")
    embeddings = []
    
    for i, (product, image) in enumerate(zip(products, product_images)):
        if image is not None:
            # Use actual product image from database
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            # Create hybrid embedding
            embedding = hybrid_embedding_service.create_product_embedding(
                image_bytes=img_bytes,
                product_name=product.name,
                brand=product.brand,
                category=product.category
            )
        else:
            # Fallback to text embedding
            text = f"{product.brand or ''} {product.name} {product.category or ''}".strip()
            embedding = embedding_service.embed_text(text)
            # Pad to 768 dimensions
            if len(embedding) < 768:
                embedding = embedding + [0.0] * (768 - len(embedding))
            else:
                embedding = embedding[:768]
        
        embeddings.append(embedding)
        
        if (i + 1) % 10 == 0:
            print(f"   Processed {i + 1}/{len(products)} products...")
    
    print(f"   ✓ Generated {len(embeddings)} hybrid embeddings")
    
    # Step 6: Insert into Qdrant
    print("\n6. Inserting into Qdrant...")
    qdrant_service.batch_insert_products(
        collection_name=settings.COLLECTION_SUPERMARKET,
        products=products,
        embeddings=embeddings
    )
    print(f"   ✓ Inserted {len(products)} products")
    
    # Step 7: Verify
    print("\n7. Verifying Qdrant collection...")
    info = qdrant_service.get_collection_info(settings.COLLECTION_SUPERMARKET)
    print(f"   Collection info: {info}")
    
    print("\n" + "=" * 60)
    print("✅ QDRANT UPDATE COMPLETE")
    print("=" * 60)
    print(f"\n✓ {len(products)} products now searchable by image")
    print("✓ CLIP embeddings generated from product images")
    print("✓ Ready for Shopping Mode similarity search")
    print("\nYou can now:")
    print("  1. Start the API: uvicorn app.main:app --reload")
    print("  2. Upload product images in Shopping Mode")
    print("  3. Get instant similarity matches!")

if __name__ == "__main__":
    load_to_qdrant()
