"""
Fine-tune SigLIP with Metric Learning (Triplet Loss)
Optimizes embeddings specifically for your product dataset
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from transformers import AutoProcessor, AutoModel
from pathlib import Path
import sys
from tqdm import tqdm
import numpy as np

sys.path.append(str(Path(__file__).parent.parent))
from metric_learning.triplet_generator import TripletGenerator

class TripletDataset(Dataset):
    """Dataset for triplet training"""
    
    def __init__(self, triplets, processor):
        self.triplets = triplets
        self.processor = processor
    
    def __len__(self):
        return len(self.triplets)
    
    def __getitem__(self, idx):
        triplet = self.triplets[idx]
        
        # Convert images to RGB if needed
        anchor_img = triplet['anchor'].convert('RGB')
        positive_img = triplet['positive'].convert('RGB')
        negative_img = triplet['negative'].convert('RGB')
        
        # Process images
        anchor = self.processor(images=anchor_img, return_tensors="pt")
        positive = self.processor(images=positive_img, return_tensors="pt")
        negative = self.processor(images=negative_img, return_tensors="pt")
        
        return {
            'anchor': {k: v.squeeze(0) for k, v in anchor.items()},
            'positive': {k: v.squeeze(0) for k, v in positive.items()},
            'negative': {k: v.squeeze(0) for k, v in negative.items()}
        }

class TripletLoss(nn.Module):
    """Triplet loss with margin"""
    
    def __init__(self, margin=0.2):
        super().__init__()
        self.margin = margin
    
    def forward(self, anchor, positive, negative):
        """
        Compute triplet loss:
        L = max(0, ||anchor - positive||² - ||anchor - negative||² + margin)
        """
        pos_dist = torch.sum((anchor - positive) ** 2, dim=1)
        neg_dist = torch.sum((anchor - negative) ** 2, dim=1)
        
        loss = torch.relu(pos_dist - neg_dist + self.margin)
        return loss.mean()

def finetune_siglip(
    num_triplets: int = 1000,
    epochs: int = 5,
    batch_size: int = 8,
    learning_rate: float = 1e-5,
    margin: float = 0.2,
    save_path: str = "siglip_finetuned"
):
    """
    Fine-tune SigLIP with triplet loss.
    
    Args:
        num_triplets: Number of training triplets
        epochs: Number of training epochs
        batch_size: Batch size
        learning_rate: Learning rate
        margin: Triplet loss margin
        save_path: Path to save fine-tuned model
    """
    print("\n" + "=" * 80)
    print("🎯 FINE-TUNING SIGLIP WITH METRIC LEARNING")
    print("=" * 80)
    
    # Device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n📱 Device: {device}")
    
    # Load model and processor
    print("\n📦 Loading SigLIP model...")
    model_name = "google/siglip-base-patch16-224"
    model = AutoModel.from_pretrained(model_name)
    processor = AutoProcessor.from_pretrained(model_name)
    model.to(device)
    print("  ✓ Model loaded")
    
    # Generate triplets
    print("\n🔄 Generating training triplets...")
    generator = TripletGenerator()
    
    # Show statistics
    stats = generator.get_statistics()
    print(f"\n📊 Dataset Statistics:")
    print(f"  Total products: {stats['total']}")
    print(f"  Categories: {len(stats['by_category'])}")
    for cat, count in list(stats['by_category'].items())[:5]:
        print(f"    - {cat}: {count}")
    
    triplets = generator.generate_triplets(num_triplets)
    generator.close()
    
    if len(triplets) < 100:
        print(f"\n⚠️ Warning: Only {len(triplets)} triplets generated.")
        print("   Need at least 100 for meaningful training.")
        print("   Consider scraping more products or lowering num_triplets.")
        return
    
    # Create dataset and dataloader
    print(f"\n📚 Creating dataset with {len(triplets)} triplets...")
    dataset = TripletDataset(triplets, processor)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    # Setup training
    criterion = TripletLoss(margin=margin)
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    print(f"\n🏋️ Training Configuration:")
    print(f"  Epochs: {epochs}")
    print(f"  Batch size: {batch_size}")
    print(f"  Learning rate: {learning_rate}")
    print(f"  Margin: {margin}")
    print(f"  Total batches: {len(dataloader)}")
    
    # Training loop
    print("\n" + "=" * 80)
    print("🚀 STARTING TRAINING")
    print("=" * 80)
    
    model.train()
    
    for epoch in range(epochs):
        epoch_loss = 0.0
        progress_bar = tqdm(dataloader, desc=f"Epoch {epoch+1}/{epochs}")
        
        for batch_idx, batch in enumerate(progress_bar):
            # Move to device
            anchor_inputs = {k: v.to(device) for k, v in batch['anchor'].items()}
            positive_inputs = {k: v.to(device) for k, v in batch['positive'].items()}
            negative_inputs = {k: v.to(device) for k, v in batch['negative'].items()}
            
            # Forward pass
            anchor_emb = model.get_image_features(**anchor_inputs)
            positive_emb = model.get_image_features(**positive_inputs)
            negative_emb = model.get_image_features(**negative_inputs)
            
            # Normalize embeddings
            anchor_emb = anchor_emb / anchor_emb.norm(dim=-1, keepdim=True)
            positive_emb = positive_emb / positive_emb.norm(dim=-1, keepdim=True)
            negative_emb = negative_emb / negative_emb.norm(dim=-1, keepdim=True)
            
            # Compute loss
            loss = criterion(anchor_emb, positive_emb, negative_emb)
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            # Update metrics
            epoch_loss += loss.item()
            progress_bar.set_postfix({'loss': f'{loss.item():.4f}'})
        
        avg_loss = epoch_loss / len(dataloader)
        print(f"\n  Epoch {epoch+1}/{epochs} - Average Loss: {avg_loss:.4f}")
    
    # Save fine-tuned model
    print("\n💾 Saving fine-tuned model...")
    save_dir = Path(__file__).parent.parent / save_path
    save_dir.mkdir(parents=True, exist_ok=True)
    
    model.save_pretrained(save_dir)
    processor.save_pretrained(save_dir)
    
    print(f"  ✓ Model saved to: {save_dir}")
    
    print("\n" + "=" * 80)
    print("✅ FINE-TUNING COMPLETE!")
    print("=" * 80)
    print("\n📝 Next steps:")
    print("  1. Update siglip_service.py to use fine-tuned model")
    print("  2. Re-generate embeddings: python load_db_to_qdrant.py")
    print("  3. Test improved accuracy!")
    print("=" * 80)

if __name__ == "__main__":
    # Configuration optimisée pour CPU
    config = {
        'num_triplets': 300,   # Réduit de 1000 → 300 (3x plus rapide)
        'epochs': 3,           # Réduit de 5 → 3 (1.6x plus rapide)
        'batch_size': 2,       # Réduit de 4 → 2 (2x plus rapide)
        'learning_rate': 2e-5, # Augmenté pour converger plus vite
        'margin': 0.2,
        'save_path': 'siglip_finetuned'
    }
    
    finetune_siglip(**config)
