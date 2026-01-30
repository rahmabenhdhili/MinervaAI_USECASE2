# Fix Memory Error (OS Error 1455)

## Error Message
```
OSError: Le fichier de pagination est insuffisant pour terminer cette opération. (os error 1455)
```

This means: **"The paging file is insufficient to complete this operation"**

## Quick Fix: Increase Windows Page File

### Step 1: Open System Properties
1. Press `Win + Pause/Break` (or right-click "This PC" → Properties)
2. Click "Advanced system settings" on the left
3. In the "Performance" section, click "Settings..."

### Step 2: Increase Virtual Memory
1. Go to the "Advanced" tab
2. Under "Virtual memory", click "Change..."
3. **Uncheck** "Automatically manage paging file size for all drives"
4. Select your C: drive
5. Choose "Custom size"
6. Set:
   - **Initial size (MB):** 8192 (8 GB)
   - **Maximum size (MB):** 16384 (16 GB)
7. Click "Set"
8. Click "OK" on all dialogs
9. **Restart your computer**

### Step 3: Restart Server
After reboot:
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Alternative: Use Base Model (No Restart Needed)

If you can't restart now, temporarily use the base model:

**Edit `backend/app/services/siglip_service.py` line 17:**

Change:
```python
self.model_name = "./siglip_finetuned"
```

To:
```python
self.model_name = "google/siglip-base-patch16-224"
```

Then restart the server (no system restart needed).

## Why This Happens

- Your fine-tuned model is ~1.5 GB
- Windows needs virtual memory (page file) to load it
- Default page file is too small
- Increasing it allows Windows to use disk space as extra RAM

## Recommended Settings

**For 8GB RAM:**
- Initial: 8192 MB
- Maximum: 16384 MB

**For 16GB RAM:**
- Initial: 16384 MB
- Maximum: 32768 MB

**For 32GB+ RAM:**
- Initial: 32768 MB
- Maximum: 65536 MB

## After Fix

Your server will start normally:
```
🎯 Loading FINE-TUNED SigLIP model from ./siglip_finetuned...
✓ Fine-tuned SigLIP model loaded on cpu
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Need Help?

If you still get errors after increasing page file:
1. Check available disk space (need at least 20GB free)
2. Close other applications to free RAM
3. Use base model as temporary solution
