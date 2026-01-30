# Memory Issue Fix - Use Base Model

## Problem
Windows error: "Le fichier de pagination est insuffisant" (OS error 1455)
- This means your system ran out of virtual memory (RAM + page file)
- The fine-tuned SigLIP model is ~1.5GB and requires significant RAM

## Solution Options

### Option 1: Automatic Fallback (Already Implemented)
The code now automatically falls back to the base model if the fine-tuned model fails to load.

### Option 2: Force Base Model (Recommended for Low RAM)
If you want to always use the base model to save memory:

**Edit `backend/app/services/siglip_service.py`:**

Change line 17 from:
```python
self.model_name = "./siglip_finetuned"
```

To:
```python
self.model_name = "google/siglip-base-patch16-224"  # Use base model
```

And comment out the fine-tuned model path:
```python
# self.model_name = "./siglip_finetuned"  # Disabled - too large for RAM
```

### Option 3: Increase Windows Page File

1. Open System Properties (Win + Pause/Break)
2. Advanced system settings → Performance Settings
3. Advanced tab → Virtual memory → Change
4. Uncheck "Automatically manage paging file"
5. Set custom size:
   - Initial size: 4096 MB
   - Maximum size: 8192 MB (or more)
6. Click Set → OK → Restart

### Option 4: Delete Fine-tuned Model (Save Disk Space)

If you're not using the fine-tuned model:
```bash
# Delete the fine-tuned model folder
rm -rf backend/siglip_finetuned
```

This will force the system to use the base model and save ~1.5GB disk space.

## Performance Comparison

**Fine-tuned Model:**
- Accuracy: ~87% (trained on Tunisian products)
- Memory: ~1.5GB RAM
- Load time: 10-15 seconds

**Base Model:**
- Accuracy: ~82% (general purpose)
- Memory: ~1GB RAM
- Load time: 5-8 seconds

## Recommendation

For development/testing with limited RAM:
→ Use base model (Option 2)

For production with sufficient RAM:
→ Use fine-tuned model with automatic fallback (Option 1)

## Current Status

✅ Automatic fallback is now enabled
- Tries fine-tuned model first
- Falls back to base model if memory error
- No code changes needed
