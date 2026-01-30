"""
Quick script to load ALL markets to Qdrant
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from load_db_to_qdrant import load_to_qdrant

if __name__ == "__main__":
    print("🚀 Loading ALL products from ALL markets to Qdrant")
    print("   This will recreate the collection with all products")
    print()
    
    response = input("Continue? (y/n): ")
    if response.lower() == 'y':
        load_to_qdrant()
    else:
        print("Cancelled")
