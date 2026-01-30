"""
Identify and optionally remove unnecessary files from the codebase
"""
import os
from pathlib import Path

# Files to remove (debug, test, and duplicate scripts)
FILES_TO_REMOVE = [
    # Debug scripts
    "debug_mazraa_html.py",
    "debug_aziza_db.py",
    "debug_carrefour_structure.py",
    "diagnose_qdrant.py",
    "diagnose_search.py",
    
    # Old test scripts
    "test_pdf_scraping.py",
    "test_mazraa_selenium.py",
    "test_mazraa_scraper.py",
    "test_carrefour_scraper.py",
    "test_pytesseract_ocr.py",
    "test_agentic_rag.py",
    "test_market_filter.py",
    
    # Duplicate/old loading scripts
    "load_images_to_qdrant.py",
    "load_db_to_qdrant.py",
    "load_db_to_qdrant_batched.py",
    "load_recent_to_qdrant.py",
    "load_aziza_text_embeddings.py",
    "simple_load_to_qdrant.py",
    "reingest_clean_data.py",
    
    # Old scraping scripts
    "scrape_aziza.py",
    "quick_rescrape_aziza.py",
    "rescrape_aziza_complete.py",
    "reload_aziza.py",
    
    # Duplicate utility scripts
    "check_images.py",
    "check_aziza_images.py",
    "check_aziza_sqlite.py",
    "check_my_cluster.py",
    "check_second_cluster.py",
    "check_qdrant_collection.py",
    "browse_database.py",
    "clear_cache.py",
    "final_verification.py",
    "merge_collections.py",
    
    # HTML test files
    "carrefour.html",
    
    # Old markdown docs (keep main guides)
    "MAZRAA_SCRAPING_SOLUTION.md",
    "MAZRAA_SCRAPING_COMPLETE.md",
    "HOW_TO_RESCRAPE_AZIZA.md",
    "RESCRAPE_AZIZA_GUIDE.md",
    "AZIZA_PROBLEM_SOLVED_FINAL.md",
    "AZIZA_REAL_PROBLEM.md",
    "FIX_AZIZA_ISSUE.md",
    "CLEANUP_SUMMARY.md",
    "SOLUTION_SUMMARY.md",
    "CARREFOUR_SCRAPING_SUMMARY.md",
]

# Keep these important files
KEEP_FILES = [
    # Core scrapers
    "scrape_carrefour_multi.py",
    "scrape_carrefour_config.py",
    
    # Loading scripts (current versions)
    "load_carrefour_to_qdrant.py",
    "load_aziza_images_to_qdrant.py",
    "load_retail_markets.py",
    
    # Utility scripts (current versions)
    "verify_carrefour_data.py",
    "download_carrefour_images.py",
    "check_carrefour_images.py",
    "count_qdrant_products.py",
    "manage_products.py",
    "create_prototypes.py",
    
    # Important docs
    "QDRANT_LOADING_GUIDE.md",
    "EXPLAINABLE_AI_GUIDE.md",
    "EXPLAINABLE_AI_CHANGES.md",
    "USE_BASE_MODEL.md",
    "FIX_MEMORY_ERROR.md",
    "ARCHITECTURE_IMPLEMENTED.txt",
    "AGENTIC_WORKFLOW_DIAGRAM.txt",
    "CARREFOUR_SCRAPER_GUIDE.md",
]

def analyze_codebase():
    """Analyze and show what can be cleaned up"""
    
    backend_dir = Path(__file__).parent
    
    print("\n" + "="*70)
    print("CODEBASE CLEANUP ANALYSIS")
    print("="*70)
    
    # Check which files exist
    existing_files = []
    missing_files = []
    
    for filename in FILES_TO_REMOVE:
        filepath = backend_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size / 1024  # KB
            existing_files.append((filename, size))
        else:
            missing_files.append(filename)
    
    # Show results
    print(f"\n[FOUND] {len(existing_files)} unnecessary files:")
    print("-" * 70)
    
    total_size = 0
    categories = {
        "Debug scripts": [],
        "Test scripts": [],
        "Old loading scripts": [],
        "Old scraping scripts": [],
        "Duplicate utilities": [],
        "Documentation": [],
        "Other": []
    }
    
    for filename, size in existing_files:
        total_size += size
        
        if filename.startswith("debug_") or filename.startswith("diagnose_"):
            categories["Debug scripts"].append((filename, size))
        elif filename.startswith("test_"):
            categories["Test scripts"].append((filename, size))
        elif "load" in filename and filename not in KEEP_FILES:
            categories["Old loading scripts"].append((filename, size))
        elif "scrape" in filename and filename not in KEEP_FILES:
            categories["Old scraping scripts"].append((filename, size))
        elif filename.endswith(".md"):
            categories["Documentation"].append((filename, size))
        elif filename.startswith("check_") or filename.startswith("browse_"):
            categories["Duplicate utilities"].append((filename, size))
        else:
            categories["Other"].append((filename, size))
    
    for category, files in categories.items():
        if files:
            print(f"\n{category}:")
            for filename, size in files:
                print(f"  - {filename:50} ({size:6.1f} KB)")
    
    print(f"\n[TOTAL] {len(existing_files)} files, {total_size:.1f} KB")
    
    # Show what will be kept
    print("\n" + "="*70)
    print("IMPORTANT FILES (WILL BE KEPT)")
    print("="*70)
    
    kept_files = []
    for filename in KEEP_FILES:
        filepath = backend_dir / filename
        if filepath.exists():
            kept_files.append(filename)
    
    print(f"\n[KEEPING] {len(kept_files)} important files:")
    for filename in sorted(kept_files):
        print(f"  ✓ {filename}")
    
    return existing_files

def cleanup_codebase(dry_run=True):
    """Remove unnecessary files"""
    
    existing_files = analyze_codebase()
    
    if not existing_files:
        print("\n[OK] Codebase is already clean!")
        return
    
    print("\n" + "="*70)
    
    if dry_run:
        print("DRY RUN MODE - No files will be deleted")
        print("="*70)
        print("\nTo actually delete these files, run:")
        print("  python cleanup_codebase.py --delete")
    else:
        print("DELETING FILES")
        print("="*70)
        
        backend_dir = Path(__file__).parent
        deleted = 0
        failed = 0
        
        for filename, size in existing_files:
            filepath = backend_dir / filename
            try:
                filepath.unlink()
                print(f"  [DELETED] {filename}")
                deleted += 1
            except Exception as e:
                print(f"  [ERROR] {filename}: {e}")
                failed += 1
        
        print(f"\n[DONE] Deleted {deleted} files")
        if failed:
            print(f"[WARNING] Failed to delete {failed} files")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    import sys
    
    # Check if --delete flag is provided
    if "--delete" in sys.argv:
        print("\n⚠️  WARNING: This will permanently delete files!")
        response = input("Are you sure? Type 'yes' to confirm: ")
        if response.lower() == 'yes':
            cleanup_codebase(dry_run=False)
        else:
            print("\n[CANCELLED] No files were deleted")
    else:
        cleanup_codebase(dry_run=True)
