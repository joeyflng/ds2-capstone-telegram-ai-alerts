# Hugging Face Spaces Deployment Guide

## Repository Information
- **Deployment Path**: `/home/joey/projects/capstone/deployment/huggingface/dsai-2-ai-market-chat`
- **Space URL**: https://huggingface.co/spaces/starryeyeowl/dsai-2-ai-market-chat

## Quick Deploy

Use the automated deployment script:

```bash
cd /home/joey/projects/capstone/deployment/ds2-capstone-telegram-ai-alerts/market-chat-web
./deploy_to_hf.sh
```

This script will:
1. Copy all updated files to the HF repo (including `app/` folder)
2. Show you what changed
3. Prompt for a commit message  
4. Push to Hugging Face
5. Trigger automatic Docker rebuild

## Critical Requirements

### 1. Dockerfile MUST Include app/ Folder

⚠️ **CRITICAL**: The Dockerfile must copy the `app/` folder:

```dockerfile
COPY app.py .
COPY utils/ ./utils/
COPY app/ ./app/        # ← WITHOUT THIS, WEB APP USES MOCK DATA!
```

Without this line, the web app falls back to mock data ($270 for AAPL instead of ~$266).

### 2. Path Detection

`utils/market.py` tries multiple paths and verifies services/ folder exists:
- `/app/app` (HF Docker - this works!)
- Logs show: `✅ Added app path: /app/app (services found)`

## Verification

Check Container logs for:
```
App folder exists: True
✅ Added app path: /app/app (services found)
✅ Hybrid FMP+Yahoo APIs loaded successfully
```

Test real data:
- AAPL: ~$266 (NOT $270 mock)
- Source: "fmp" (NOT "mock")
- 52W data from FMP yearHigh/yearLow

See full guide: https://github.com/joeyflng/ds2-capstone-telegram-ai-alerts/blob/main/market-chat-web/HUGGINGFACE_DEPLOY_OLD.md
