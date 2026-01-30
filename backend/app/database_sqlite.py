"""
SQLite database for user management and events tracking
Simple, reliable, and no external dependencies
"""
import sqlite3
import hashlib
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

class SQLiteUserDB:
    """SQLite database for user management and events"""
    
    def __init__(self, db_path: str = "users.db"):
        """Initialize SQLite database"""
        self.db_path = Path(__file__).parent.parent / db_path
        self.init_database()
    
    def init_database(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                user_type TEXT DEFAULT 'b2c',
                company_name TEXT,
                contact_person TEXT,
                phone TEXT,
                address TEXT,
                business_type TEXT,
                is_verified BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create events table for user tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                content TEXT,
                product_name TEXT,
                brand TEXT,
                category TEXT,
                supplier TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_type ON users(user_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
        
        conn.commit()
        conn.close()
        print(f"[OK] SQLite user database initialized: {self.db_path}")
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Check if email already exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (user_data["email"],))
            if cursor.fetchone():
                raise ValueError("Email already registered")
            
            # Generate unique ID
            user_id = str(uuid.uuid4())
            
            # Insert user
            cursor.execute("""
                INSERT INTO users (
                    id, email, password, user_type, company_name, 
                    contact_person, phone, address, business_type, is_verified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                user_data["email"],
                user_data["password"],
                user_data.get("user_type", "b2c"),
                user_data.get("company_name"),
                user_data.get("contact_person"),
                user_data.get("phone"),
                user_data.get("address"),
                user_data.get("business_type"),
                user_data.get("is_verified", False)
            ))
            
            conn.commit()
            
            # Return created user
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = dict(cursor.fetchone())
            return user
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_user_by_email(self, email: str, user_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if user_type:
                cursor.execute("SELECT * FROM users WHERE email = ? AND user_type = ?", (email, user_type))
            else:
                cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            
            user = cursor.fetchone()
            return dict(user) if user else None
            
        finally:
            conn.close()
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
            
        finally:
            conn.close()
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user data"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            # Build dynamic update query
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                if key != 'id':  # Don't allow ID updates
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
            
            if not set_clauses:
                return False
            
            # Add updated_at timestamp
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            values.append(user_id)
            
            query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ?"
            cursor.execute(query, values)
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
            
        finally:
            conn.close()
    
    # ==================== EVENTS METHODS ====================
    
    def track_event(self, event_data: Dict[str, Any]) -> str:
        """Track user event"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            event_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO events (
                    id, user_id, event_type, content, product_name, 
                    brand, category, supplier
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id,
                event_data["user_id"],
                event_data["event_type"],
                event_data.get("content"),
                event_data.get("product_name"),
                event_data.get("brand"),
                event_data.get("category"),
                event_data.get("supplier")
            ))
            
            conn.commit()
            return event_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_user_events(self, user_id: str, limit: int = 20, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get user events for personalization"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if event_type:
                cursor.execute("""
                    SELECT * FROM events 
                    WHERE user_id = ? AND event_type = ?
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (user_id, event_type, limit))
            else:
                cursor.execute("""
                    SELECT * FROM events 
                    WHERE user_id = ?
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (user_id, limit))
            
            events = cursor.fetchall()
            return [dict(event) for event in events]
            
        finally:
            conn.close()
    
    def get_user_preference_text(self, user_id: str, limit: int = 20) -> str:
        """Get user preference text for personalization"""
        events = self.get_user_events(user_id, limit)
        
        if not events:
            return ""
        
        # Build preference text from user events
        preferences = []
        for event in events:
            if event["event_type"] == "search" and event["content"]:
                preferences.append(f"searched for: {event['content']}")
            elif event["event_type"] == "click":
                parts = []
                if event["product_name"]:
                    parts.append(f"clicked on {event['product_name']}")
                if event["brand"]:
                    parts.append(f"brand: {event['brand']}")
                if event["category"]:
                    parts.append(f"category: {event['category']}")
                if parts:
                    preferences.append(", ".join(parts))
        
        return " | ".join(preferences[:10])  # Limit to avoid too long text
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            # Total users
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            # Users by type
            cursor.execute("SELECT user_type, COUNT(*) FROM users GROUP BY user_type")
            users_by_type = dict(cursor.fetchall())
            
            # Recent registrations (last 7 days)
            cursor.execute("""
                SELECT COUNT(*) FROM users 
                WHERE created_at >= datetime('now', '-7 days')
            """)
            recent_registrations = cursor.fetchone()[0]
            
            # Total events
            cursor.execute("SELECT COUNT(*) FROM events")
            total_events = cursor.fetchone()[0]
            
            # Events by type
            cursor.execute("SELECT event_type, COUNT(*) FROM events GROUP BY event_type")
            events_by_type = dict(cursor.fetchall())
            
            return {
                "total_users": total_users,
                "users_by_type": users_by_type,
                "recent_registrations": recent_registrations,
                "total_events": total_events,
                "events_by_type": events_by_type
            }
            
        finally:
            conn.close()

# Singleton instance
user_db = SQLiteUserDB()

# Compatibility functions for existing code
def get_users_collection():
    """Compatibility function - returns the user_db instance"""
    return user_db

def get_events_collection():
    """Compatibility function - returns the user_db instance"""
    return user_db