# 🚀 Hugging Face Deployment Checklist

## Pre-Deployment

- [ ] All files tested locally with `streamlit run app.py`
- [ ] API keys working (GROQ_API_KEY for AI chat)
- [ ] No hardcoded secrets in code
- [ ] `.gitignore` / `.dockerignore` configured

## Files to Deploy

### Essential Files (Required)
- [ ] `app.py` - Main Streamlit application
- [ ] `requirements.txt` - Python dependencies
- [ ] `README.md` - With HF Spaces metadata header
- [ ] `utils/` directory - All utility modules
  - [ ] `utils/market.py`
  - [ ] `utils/llm.py`

### Docker SDK (Optional - for production)
- [ ] `Dockerfile` - Container configuration
- [ ] `.dockerignore` - Exclude unnecessary files

### Not Needed (Excluded)
- ❌ `.env` file (use HF Secrets instead)
- ❌ `__pycache__/` directories
- ❌ `.vscode/` or IDE files

## Hugging Face Space Setup

### 1. Create Space
- [ ] Go to https://huggingface.co/new-space
- [ ] Choose name (e.g., `ai-market-chat`)
- [ ] Select SDK:
  - [ ] **Docker** (Production, uses Dockerfile)
  - [ ] **Streamlit** (Simpler, no Dockerfile)
- [ ] Set visibility (Public/Private)

### 2. README.md Header

**For Docker SDK:**
```yaml
---
title: AI Market Chat Companion
emoji: 📊
sdk: docker
app_port: 7860
---
```

**For Streamlit SDK:**
```yaml
---
title: AI Market Chat Companion
emoji: 📊
sdk: streamlit
sdk_version: 1.28.0
app_file: app.py
---
```

### 3. Configure Secrets
- [ ] Go to Space Settings → Repository Secrets
- [ ] Add `GROQ_API_KEY` (required for AI)
- [ ] Add `FMP_API_KEY` (optional, fallback to Yahoo)

### 4. Deploy
```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE
cd YOUR_SPACE

# Copy files
cp /path/to/market-chat-web/app.py .
cp /path/to/market-chat-web/requirements.txt .
cp /path/to/market-chat-web/README.md .
cp -r /path/to/market-chat-web/utils .

# Docker SDK only:
cp /path/to/market-chat-web/Dockerfile .
cp /path/to/market-chat-web/.dockerignore .

# Commit and push
git add .
git commit -m "Deploy AI Market Chat"
git push
```

## Post-Deployment Testing

- [ ] Wait for build to complete (check Logs tab)
- [ ] App loads without errors
- [ ] Enter ticker symbol (e.g., AAPL)
- [ ] Data displays correctly
- [ ] Charts render properly
- [ ] AI chat works (requires GROQ_API_KEY)
- [ ] Fear & Greed Index shows
- [ ] No console errors

## Common Issues

| Issue | Solution |
|-------|----------|
| Build fails | Check logs, verify all files present |
| API errors | Add secrets in Repository Secrets |
| Port errors (Docker) | Ensure Dockerfile uses port 7860 |
| Dependencies fail | Update `requirements.txt` versions |
| App won't start | Check README.md header format |

## SDK Choice Guide

**Use Streamlit SDK if:**
- ✅ You want fastest deployment
- ✅ Standard Streamlit app
- ✅ No custom system dependencies

**Use Docker SDK if:**
- ✅ You need custom system packages
- ✅ You want full environment control
- ✅ Production deployment with specific versions

## Success Criteria

✅ App is publicly accessible at `https://huggingface.co/spaces/USERNAME/SPACE_NAME`

✅ All features work as expected

✅ No API keys exposed in code

✅ Build completes in under 5 minutes

---

**Need help?** Check the main project README.md for detailed instructions.
