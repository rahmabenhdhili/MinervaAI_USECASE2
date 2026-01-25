"""
SQLite database for storing scraped product data.
Stores product info and images as BLOBs.
"""
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image
import io
from datetime import datetime

class ProductDatabase:
    """SQLite database for scraped products"""
    
    def __init__(self, db_path: str = "scraped_products.db"):
        """Initialize database connection"""
        self.db_path = Path(__file__).parent.parent / db_path
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """Create database tables if they don't exist"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        
        cursor = self.conn.cursor()
        
        # Create products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                brand TEXT,
                quantity TEXT,
                price REAL NOT NULL,
                old_price REAL,
                currency TEXT DEFAULT 'TND',
                market TEXT NOT NULL,
                category TEXT DEFAULT 'food',
                product_url TEXT,
                image_url TEXT,
                image_blob BLOB,
                promo TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on market and product_id for fast lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_market 
            ON products(market)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_product_id 
            ON products(product_id)
        """)
        
        self.conn.commit()
        print(f"✓ Database initialized: {self.db_path}")
    
    def insert_product(self, product_data: Dict[str, Any]) -> int:
        """
        Insert or update a product in the database.
        Returns the product ID.
        """
        cursor = self.conn.cursor()
        
        # Convert PIL Image to BLOB if present
        image_blob = None
        if "image" in product_data and product_data["image"] is not None:
            img = product_data["image"]
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            image_blob = img_byte_arr.getvalue()
        
        # Generate unique product_id
        product_id = product_data.get("product_id") or f"{product_data['market']}_{hash(product_data['name'])}"
        
        try:
            cursor.execute("""
                INSERT INTO products (
                    product_id, name, description, brand, quantity,
                    price, old_price, currency, market, category,
                    product_url, image_url, image_blob, promo, scraped_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(product_id) DO UPDATE SET
                    name = excluded.name,
                    price = excluded.price,
                    old_price = excluded.old_price,
                    image_blob = excluded.image_blob,
                    promo = excluded.promo,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                product_id,
                product_data["name"],
                product_data.get("description", product_data["name"]),
                product_data.get("brand"),
                product_data.get("quantity"),
                product_data["price"],
                product_data.get("old_price"),
                product_data.get("currency", "TND"),
                product_data["market"],
                product_data.get("category", "food"),
                product_data.get("url"),
                product_data.get("image_url"),
                image_blob,
                product_data.get("promo"),
                product_data.get("scraped_at", datetime.now().isoformat())
            ))
            
            self.conn.commit()
            return cursor.lastrowid
        
        except Exception as e:
            print(f"Error inserting product: {e}")
            self.conn.rollback()
            return -1
    
    def batch_insert_products(self, products: List[Dict[str, Any]]) -> int:
        """Insert multiple products. Returns count of inserted products."""
        count = 0
        for product in products:
            if self.insert_product(product) > 0:
                count += 1
        return count
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get a product by its product_id"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def get_products_by_market(self, market: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all products from a specific market"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM products 
            WHERE market = ? 
            ORDER BY updated_at DESC 
            LIMIT ?
        """, (market, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_all_products(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all products from database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM products 
            ORDER BY market, name 
            LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_product_image(self, product_id: str) -> Optional[Image.Image]:
        """Get product image as PIL Image"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT image_blob FROM products WHERE product_id = ?", (product_id,))
        row = cursor.fetchone()
        
        if row and row['image_blob']:
            return Image.open(io.BytesIO(row['image_blob']))
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        cursor = self.conn.cursor()
        
        # Total products
        cursor.execute("SELECT COUNT(*) as total FROM products")
        total = cursor.fetchone()['total']
        
        # Products per market
        cursor.execute("""
            SELECT market, COUNT(*) as count 
            FROM products 
            GROUP BY market
        """)
        by_market = {row['market']: row['count'] for row in cursor.fetchall()}
        
        # Average price per market
        cursor.execute("""
            SELECT market, AVG(price) as avg_price 
            FROM products 
            GROUP BY market
        """)
        avg_prices = {row['market']: round(row['avg_price'], 2) for row in cursor.fetchall()}
        
        # Products with promos
        cursor.execute("SELECT COUNT(*) as count FROM products WHERE promo IS NOT NULL")
        promo_count = cursor.fetchone()['count']
        
        return {
            "total_products": total,
            "by_market": by_market,
            "avg_prices": avg_prices,
            "products_with_promos": promo_count
        }
    
    def clear_market(self, market: str):
        """Delete all products from a specific market"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM products WHERE market = ?", (market,))
        self.conn.commit()
        print(f"✓ Cleared {cursor.rowcount} products from {market}")
    
    def clear_all(self):
        """Delete all products from database"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM products")
        self.conn.commit()
        print(f"✓ Cleared all products from database")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# Singleton instance
product_db = ProductDatabase()
