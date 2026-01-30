"""
Check if Carrefour product images are valid and match the products
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from data_pipeline.product_database import product_db
import requests
from PIL import Image
import io

def check_image_urls():
    """Check if image URLs are valid and accessible"""
    
    print("\n" + "="*70)
    print("CARREFOUR IMAGE URL VERIFICATION")
    print("="*70)
    
    # Get all Carrefour products
    products = product_db.get_products_by_market('Carrefour', limit=5000)
    
    if not products:
        print("\n[ERROR] No Carrefour products found!")
        return
    
    print(f"\n[INFO] Checking {len(products)} Carrefour products...")
    
    # Check image URLs
    with_url = [p for p in products if p.get('image_url')]
    without_url = [p for p in products if not p.get('image_url')]
    
    print(f"\n[STATS] Products with image URL: {len(with_url)}/{len(products)} ({len(with_url)/len(products)*100:.1f}%)")
    print(f"[STATS] Products without image URL: {len(without_url)}")
    
    if without_url:
        print(f"\n[WARNING] {len(without_url)} products don't have image URLs")
        print("Sample products without URLs:")
        for p in without_url[:3]:
            print(f"  - {p['name']}")
    
    # Test a sample of image URLs
    print(f"\n[TESTING] Testing 10 random image URLs...")
    
    import random
    sample = random.sample(with_url, min(10, len(with_url)))
    
    valid_images = 0
    invalid_images = 0
    
    for i, product in enumerate(sample, 1):
        try:
            # Try to download and verify image
            response = requests.get(product['image_url'], timeout=5)
            
            if response.status_code == 200:
                # Try to open as image
                img = Image.open(io.BytesIO(response.content))
                img.verify()
                
                # Check image size
                img = Image.open(io.BytesIO(response.content))
                width, height = img.size
                
                print(f"\n{i}. [OK] {product['name'][:50]}")
                print(f"   URL: {product['image_url'][:60]}...")
                print(f"   Size: {width}x{height}px")
                print(f"   Format: {img.format}")
                
                valid_images += 1
            else:
                print(f"\n{i}. [ERROR] {product['name'][:50]}")
                print(f"   Status: {response.status_code}")
                invalid_images += 1
                
        except Exception as e:
            print(f"\n{i}. [ERROR] {product['name'][:50]}")
            print(f"   Error: {str(e)[:60]}")
            invalid_images += 1
    
    # Summary
    print("\n" + "-"*70)
    print("TEST RESULTS")
    print("-"*70)
    print(f"Valid images: {valid_images}/10")
    print(f"Invalid images: {invalid_images}/10")
    print(f"Success rate: {valid_images/10*100:.0f}%")
    
    # Show some example URLs
    print("\n" + "-"*70)
    print("SAMPLE IMAGE URLS")
    print("-"*70)
    
    for i, product in enumerate(with_url[:5], 1):
        print(f"\n{i}. {product['name']}")
        print(f"   {product['image_url']}")
    
    # Recommendations
    print("\n" + "="*70)
    print("RECOMMENDATIONS")
    print("="*70)
    
    if valid_images >= 8:
        print("\n[OK] Image URLs look good!")
        print("\nNext steps:")
        print("1. Download images:")
        print("   python download_carrefour_images.py")
        print("\n2. Verify data quality:")
        print("   python verify_carrefour_data.py")
    elif valid_images >= 5:
        print("\n[WARNING] Some image URLs may be broken")
        print("Most images should download successfully")
        print("\nProceed with:")
        print("   python download_carrefour_images.py")
    else:
        print("\n[ERROR] Many image URLs are broken!")
        print("Consider re-scraping:")
        print("   python scrape_carrefour_multi.py")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    check_image_urls()
