#!/bin/bash

# Quick Deploy Script for Hugging Face Space
# Updates the deployed app with latest changes

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Deploying to Hugging Face Space...${NC}\n"

# Configuration
HF_REPO="/home/joey/projects/capstone/deployment/huggingface/dsai-2-ai-market-chat"
SOURCE_DIR="/home/joey/projects/capstone/deployment/ds2-capstone-telegram-ai-alerts/market-chat-web"

# Check if HF repo exists
if [ ! -d "$HF_REPO" ]; then
    echo -e "${RED}❌ Hugging Face repo not found at: $HF_REPO${NC}"
    echo "Please clone your space first:"
    echo "  git clone https://huggingface.co/spaces/YOUR_USERNAME/dsai-2-ai-market-chat"
    exit 1
fi

# Navigate to HF repo
cd "$HF_REPO" || exit 1
echo -e "${GREEN}📂 Working in: $HF_REPO${NC}\n"

# Pull latest from HF (in case of conflicts)
echo -e "${BLUE}📥 Pulling latest from Hugging Face...${NC}"
git pull

# Copy updated files
echo -e "${BLUE}📋 Copying updated files...${NC}"

cp "$SOURCE_DIR/app.py" . && echo "  ✅ app.py"
cp "$SOURCE_DIR/requirements.txt" . && echo "  ✅ requirements.txt"
cp "$SOURCE_DIR/config.py" . && echo "  ✅ config.py"

# Copy utils folder
if [ -d "$SOURCE_DIR/utils" ]; then
    rm -rf utils
    cp -r "$SOURCE_DIR/utils" . && echo "  ✅ utils/"
fi

# Copy app folder (needed for FMP hybrid APIs)
APP_SOURCE="/home/joey/projects/capstone/deployment/ds2-capstone-telegram-ai-alerts/app"
if [ -d "$APP_SOURCE" ]; then
    rm -rf app
    mkdir -p app
    
    # Copy only needed modules (not bot code)
    cp "$APP_SOURCE/__init__.py" app/ 2>/dev/null || touch app/__init__.py
    cp "$APP_SOURCE/config.py" app/ && echo "  ✅ app/config.py"
    
    # Copy services folder (FMP hybrid, data providers)
    if [ -d "$APP_SOURCE/services" ]; then
        cp -r "$APP_SOURCE/services" app/ && echo "  ✅ app/services/"
    fi
    
    # Copy data folder (stock list, state)
    if [ -d "$APP_SOURCE/data" ]; then
        cp -r "$APP_SOURCE/data" app/ && echo "  ✅ app/data/"
    fi
fi

# Copy Docker files if they exist
if [ -f "$SOURCE_DIR/Dockerfile" ]; then
    cp "$SOURCE_DIR/Dockerfile" . && echo "  ✅ Dockerfile"
fi

if [ -f "$SOURCE_DIR/.dockerignore" ]; then
    cp "$SOURCE_DIR/.dockerignore" . && echo "  ✅ .dockerignore"
fi

echo ""

# Check for changes
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${GREEN}✅ No changes detected - already up to date!${NC}"
    exit 0
fi

# Show what changed
echo -e "${BLUE}📊 Changes detected:${NC}"
git status --short

echo ""
read -p "Deploy these changes? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Get commit message
    read -p "Commit message (or press Enter for default): " commit_msg
    if [ -z "$commit_msg" ]; then
        commit_msg="Update app with latest changes"
    fi
    
    # Commit and push
    echo -e "${BLUE}📤 Deploying to Hugging Face...${NC}"
    git add .
    git commit -m "$commit_msg"
    git push
    
    echo ""
    echo -e "${GREEN}✅ Deployment complete!${NC}"
    echo -e "${BLUE}🌐 Your app will rebuild in a few minutes${NC}"
    echo -e "${BLUE}📍 Check: https://huggingface.co/spaces/YOUR_USERNAME/dsai-2-ai-market-chat${NC}"
else
    echo -e "${RED}❌ Deployment cancelled${NC}"
    git reset --hard HEAD
fi
