"""
Full Carrefour scraper - scrapes multiple pages and saves to database
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from data_pipeline.carrefour_scraper import CarrefourScraper


def main():
    print("🚀 Carrefour Tunisia Full Scraper")
    print("="*60)
    
    # Initialize scraper
    scraper = CarrefourScraper(base_url="https://www.carrefour.tn/boissons/eaux.html")
    
    # Scrape pages 1-3 (you can adjust this)
    print("\n🔍 Scraping Carrefour products...")
    scraper.scrape_multiple_pages(start_page=1, end_page=3)
    
    # Print summary
    scraper.print_summary()
    
    # Save to database
    if scraper.products:
        saved_count = scraper.save_to_database()
        
        print("\n💡 Next steps:")
        print("   1. Run: python browse_database.py")
        print("   2. Run: python load_db_to_qdrant.py")
        print("   3. Your Carrefour products will be searchable in the app!")
    else:
        print("⚠️  No products were scraped.")


if __name__ == "__main__":
    main()
