"""
Count products by market in Qdrant
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.services.qdrant_service import qdrant_service
from app.core.config import settings
from qdrant_client.models import Filter, FieldCondition

def count_by_market():
    print("📊 Counting Products by Market in Qdrant")
    print("=" * 60)
    
    # Get collection info
    try:
        collection_info = qdrant_service.client.get_collection(settings.COLLECTION_SUPERMARKET)
        total_points = collection_info.points_count
        print(f"\n✓ Total points in collection: {total_points}")
    except Exception as e:
        print(f"❌ Error getting collection info: {e}")
        return
    
    # Count by market
    markets = ["aziza", "Carrefour", "Mazraa Market"]
    
    print(f"\n📈 Breakdown by market:")
    for market in markets:
        try:
            # Use scroll to count (more reliable than search)
            result = qdrant_service.client.scroll(
                collection_name=settings.COLLECTION_SUPERMARKET,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="market",
                            match={"value": market}
                        )
                    ]
                ),
                limit=10000,  # Large limit to get all
                with_payload=False,
                with_vectors=False
            )
            
            count = len(result[0])
            print(f"   {market}: {count} products")
            
            # Show sample
            if count > 0:
                sample_result = qdrant_service.client.scroll(
                    collection_name=settings.COLLECTION_SUPERMARKET,
                    scroll_filter=Filter(
                        must=[
                            FieldCondition(
                                key="market",
                                match={"value": market}
                            )
                        ]
                    ),
                    limit=3,
                    with_payload=True,
                    with_vectors=False
                )
                
                print(f"      Sample products:")
                for point in sample_result[0]:
                    print(f"      - {point.payload['name'][:50]}")
        
        except Exception as e:
            print(f"   {market}: Error - {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    count_by_market()
