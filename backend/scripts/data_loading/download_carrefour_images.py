"""
Download images for existing Carrefour products that don't have images
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from data_pipeline.product_database import product_db
from data_pipeline.carrefour_scraper import CarrefourScraper
import time

def download_missing_images():
    """Download images for Carrefour products that don't have them"""
    
    print("\n" + "="*70)
    print("DOWNLOADING CARREFOUR IMAGES")
    print("="*70)
    
    # Get all Carrefour products
    products = product_db.get_products_by_market('Carrefour', limit=5000)
    
    if not products:
        print("\n[ERROR] No Carrefour products found!")
        return
    
    # Filter products without images but with image URLs
    products_needing_images = [
        p for p in products 
        if not p.get('image_blob') and p.get('image_url')
    ]
    
    print(f"\n[INFO] Total Carrefour products: {len(products)}")
    print(f"[INFO] Products needing images: {len(products_needing_images)}")
    
    if not products_needing_images:
        print("\n[OK] All products already have images!")
        return
    
    # Create scraper instance for image download
    scraper = CarrefourScraper()
    
    # Download images
    downloaded = 0
    failed = 0
    
    print(f"\n[DOWNLOADING] Processing {len(products_needing_images)} products...")
    
    for i, product in enumerate(products_needing_images, 1):
        try:
            # Download image
            image_blob = scraper.download_image_as_blob(product['image_url'])
            
            if image_blob:
                # Update product in database
                product_db.conn.execute(
                    "UPDATE products SET image_blob = ? WHERE id = ?",
                    (image_blob, product['id'])
                )
                product_db.conn.commit()
                downloaded += 1
                
                if i % 10 == 0:
                    print(f"  [{i}/{len(products_needing_images)}] Downloaded {downloaded} images...")
            else:
                failed += 1
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.1)
            
        except Exception as e:
            print(f"  [ERROR] Failed to download image for {product['name']}: {e}")
            failed += 1
    
    print(f"\n[OK] Download complete!")
    print(f"  Successfully downloaded: {downloaded}")
    print(f"  Failed: {failed}")
    print(f"  Success rate: {downloaded/(downloaded+failed)*100:.1f}%")
    
    # Verify
    products_after = product_db.get_products_by_market('Carrefour', limit=5000)
    with_images = sum(1 for p in products_after if p.get('image_blob'))
    
    print(f"\n[STATS] Products with images: {with_images}/{len(products_after)} ({with_images/len(products_after)*100:.1f}%)")
    
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    print("\n1. Verify data quality:")
    print("   python verify_carrefour_data.py")
    print("\n2. If quality is good, load to Qdrant:")
    print("   python load_carrefour_to_qdrant.py")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    download_missing_images()
