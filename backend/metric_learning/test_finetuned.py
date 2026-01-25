"""
Test et compare le modèle fine-tuné vs le modèle de base
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from transformers import AutoProcessor, AutoModel
import torch
from PIL import Image
import io
import sqlite3
import numpy as np

def load_model(model_path):
    """Load model and processor"""
    model = AutoModel.from_pretrained(model_path)
    processor = AutoProcessor.from_pretrained(model_path)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    model.eval()
    return model, processor, device

def embed_image(model, processor, device, image_bytes):
    """Generate embedding for image"""
    image = Image.open(io.BytesIO(image_bytes))
    inputs = processor(images=image, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model.get_image_features(**inputs)
        embedding = outputs / outputs.norm(dim=-1, keepdim=True)
    
    return embedding.cpu().numpy()[0]

def cosine_similarity(a, b):
    """Compute cosine similarity"""
    return np.dot(a, b)

def test_models():
    """Compare base model vs fine-tuned model"""
    print("\n" + "=" * 80)
    print("🧪 TESTING: BASE MODEL VS FINE-TUNED MODEL")
    print("=" * 80)
    
    # Load models
    print("\n📦 Loading models...")
    base_model, base_processor, device = load_model("google/siglip-base-patch16-224")
    print("  ✓ Base model loaded")
    
    finetuned_path = Path(__file__).parent.parent / "siglip_finetuned"
    if not finetuned_path.exists():
        print(f"\n❌ Fine-tuned model not found at: {finetuned_path}")
        print("   Run: python metric_learning/finetune_siglip.py first")
        return
    
    finetuned_model, finetuned_processor, _ = load_model(str(finetuned_path))
    print("  ✓ Fine-tuned model loaded")
    
    # Load test products from database
    print("\n📊 Loading test products...")
    db_path = Path(__file__).parent.parent / "scraped_products.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get products by category
    cursor.execute("""
        SELECT name, brand, category, image_blob
        FROM products
        WHERE image_blob IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 10
    """)
    
    test_products = cursor.fetchall()
    print(f"  ✓ Loaded {len(test_products)} test products")
    
    # Test similarity within same category
    print("\n" + "=" * 80)
    print("📈 SIMILARITY SCORES COMPARISON")
    print("=" * 80)
    
    for i in range(min(5, len(test_products) - 1)):
        anchor_name, anchor_brand, anchor_cat, anchor_img = test_products[i]
        
        print(f"\n🎯 Anchor: {anchor_name} ({anchor_cat})")
        
        # Find similar product (same category)
        similar = None
        different = None
        
        for j in range(i + 1, len(test_products)):
            name, brand, cat, img = test_products[j]
            if cat == anchor_cat and similar is None:
                similar = (name, brand, cat, img)
            elif cat != anchor_cat and different is None:
                different = (name, brand, cat, img)
            
            if similar and different:
                break
        
        if not similar or not different:
            continue
        
        # Compute embeddings
        anchor_emb_base = embed_image(base_model, base_processor, device, anchor_img)
        anchor_emb_ft = embed_image(finetuned_model, finetuned_processor, device, anchor_img)
        
        similar_emb_base = embed_image(base_model, base_processor, device, similar[3])
        similar_emb_ft = embed_image(finetuned_model, finetuned_processor, device, similar[3])
        
        different_emb_base = embed_image(base_model, base_processor, device, different[3])
        different_emb_ft = embed_image(finetuned_model, finetuned_processor, device, different[3])
        
        # Compute similarities
        sim_similar_base = cosine_similarity(anchor_emb_base, similar_emb_base)
        sim_similar_ft = cosine_similarity(anchor_emb_ft, similar_emb_ft)
        
        sim_different_base = cosine_similarity(anchor_emb_base, different_emb_base)
        sim_different_ft = cosine_similarity(anchor_emb_ft, different_emb_ft)
        
        # Display results
        print(f"\n  Similar ({similar[2]}): {similar[0][:50]}")
        print(f"    Base model:      {sim_similar_base:.3f}")
        print(f"    Fine-tuned:      {sim_similar_ft:.3f}")
        improvement_similar = (sim_similar_ft - sim_similar_base) * 100
        print(f"    Improvement:     {improvement_similar:+.1f}%")
        
        print(f"\n  Different ({different[2]}): {different[0][:50]}")
        print(f"    Base model:      {sim_different_base:.3f}")
        print(f"    Fine-tuned:      {sim_different_ft:.3f}")
        improvement_different = (sim_different_base - sim_different_ft) * 100
        print(f"    Separation:      {improvement_different:+.1f}%")
        
        # Margin
        margin_base = sim_similar_base - sim_different_base
        margin_ft = sim_similar_ft - sim_different_ft
        print(f"\n  Margin (similar - different):")
        print(f"    Base model:      {margin_base:.3f}")
        print(f"    Fine-tuned:      {margin_ft:.3f}")
        print(f"    Improvement:     {(margin_ft - margin_base)*100:+.1f}%")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)
    print("\n💡 Interpretation:")
    print("  - Similar products should have HIGHER similarity after fine-tuning")
    print("  - Different products should have LOWER similarity after fine-tuning")
    print("  - Larger margin = better separation = better accuracy")
    print("=" * 80)

if __name__ == "__main__":
    test_models()
