"""
Triplet Generator for Metric Learning
Generates (anchor, positive, negative) triplets from product database
"""
import sqlite3
import random
from pathlib import Path
from typing import List, Tuple, Dict
from PIL import Image
import io

class TripletGenerator:
    """
    Generate triplets for metric learning:
    - Anchor: Product image
    - Positive: Same product or same brand+category
    - Negative: Different category or different brand
    """
    
    def __init__(self, db_path: str = "scraped_products.db"):
        self.db_path = Path(__file__).parent.parent / db_path
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
    
    def generate_triplets(self, num_triplets: int = 1000) -> List[Tuple]:
        """
        Generate triplets for training.
        
        Strategy:
        1. Anchor: Random product with image
        2. Positive: Same category + same brand (or similar name)
        3. Negative: Different category OR different brand
        
        Args:
            num_triplets: Number of triplets to generate
            
        Returns:
            List of (anchor_img, positive_img, negative_img, metadata)
        """
        print(f"\n🔄 Generating {num_triplets} triplets...")
        
        # Get all products with images
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, product_id, name, brand, category, image_blob
            FROM products
            WHERE image_blob IS NOT NULL
        """)
        products = [dict(row) for row in cursor.fetchall()]
        
        print(f"  ✓ Loaded {len(products)} products with images")
        
        # Group by category and brand
        by_category_brand = {}
        for prod in products:
            key = (prod['category'], prod['brand'])
            if key not in by_category_brand:
                by_category_brand[key] = []
            by_category_brand[key].append(prod)
        
        triplets = []
        failed = 0
        
        for i in range(num_triplets):
            try:
                # 1. Select anchor
                anchor = random.choice(products)
                anchor_key = (anchor['category'], anchor['brand'])
                
                # 2. Select positive (same category + brand)
                positives = [p for p in by_category_brand.get(anchor_key, []) 
                            if p['id'] != anchor['id']]
                
                if not positives:
                    # Fallback: same category, any brand
                    positives = [p for p in products 
                                if p['category'] == anchor['category'] 
                                and p['id'] != anchor['id']]
                
                if not positives:
                    failed += 1
                    continue
                
                positive = random.choice(positives)
                
                # 3. Select negative (different category OR different brand)
                negatives = [p for p in products 
                            if p['category'] != anchor['category'] 
                            or p['brand'] != anchor['brand']]
                
                if not negatives:
                    failed += 1
                    continue
                
                negative = random.choice(negatives)
                
                # Convert BLOBs to PIL Images
                anchor_img = Image.open(io.BytesIO(anchor['image_blob']))
                positive_img = Image.open(io.BytesIO(positive['image_blob']))
                negative_img = Image.open(io.BytesIO(negative['image_blob']))
                
                triplets.append({
                    'anchor': anchor_img,
                    'positive': positive_img,
                    'negative': negative_img,
                    'anchor_name': anchor['name'],
                    'positive_name': positive['name'],
                    'negative_name': negative['name'],
                    'anchor_category': anchor['category'],
                    'positive_category': positive['category'],
                    'negative_category': negative['category']
                })
                
                if (i + 1) % 100 == 0:
                    print(f"  Generated {i + 1}/{num_triplets} triplets...")
            
            except Exception as e:
                failed += 1
                continue
        
        print(f"  ✓ Generated {len(triplets)} valid triplets")
        if failed > 0:
            print(f"  ⚠️ Failed to generate {failed} triplets")
        
        return triplets
    
    def get_statistics(self):
        """Get dataset statistics"""
        cursor = self.conn.cursor()
        
        # Total products
        cursor.execute("SELECT COUNT(*) FROM products WHERE image_blob IS NOT NULL")
        total = cursor.fetchone()[0]
        
        # By category
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM products
            WHERE image_blob IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
        """)
        by_category = dict(cursor.fetchall())
        
        # By brand
        cursor.execute("""
            SELECT brand, COUNT(*) as count
            FROM products
            WHERE image_blob IS NOT NULL AND brand IS NOT NULL
            GROUP BY brand
            ORDER BY count DESC
            LIMIT 10
        """)
        top_brands = dict(cursor.fetchall())
        
        return {
            'total': total,
            'by_category': by_category,
            'top_brands': top_brands
        }
    
    def close(self):
        """Close database connection"""
        self.conn.close()
