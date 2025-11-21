# 🤖 Telegram Bot Deployment Guide

Complete guide to deploy your AI-powered Telegram stock bot to various cloud platforms.

---

## 📋 Pre-Deployment Checklist

### **1. Required Environment Variables**
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
GROQ_API_KEY=your_groq_api_key_here
FMP_API_KEY=your_fmp_key_here  # Optional, falls back to Yahoo

# Alert Intervals (optimized for rate limiting)
ALERT_STOCK_INTERVAL=1800
ALERT_52_WEEK_HIGH_INTERVAL=2400
ALERT_BUY_DIP_INTERVAL=1800
ALERT_MA_CROSSOVER_INTERVAL=3600
ALERT_EARNINGS_INTERVAL=21600

# Stock symbols to monitor
DEFAULT_STOCKS=NVDA,TSLA
```

### **2. Important Files**
- ✅ `bot_interactive.py` - Main bot entry point
- ✅ `requirements.txt` - Python dependencies
- ✅ `Dockerfile` - Container configuration
- ✅ `.env` - Environment variables (DO NOT commit to Git!)
- ✅ `app/` - All bot modules

### **3. Resource Requirements**
- **Memory**: 512MB minimum, 1GB recommended
- **CPU**: 0.5 vCPU minimum
- **Storage**: 500MB
- **Network**: Outbound HTTPS (443) for APIs

### **4. Critical Deployment Considerations**

#### **Rate Limiting is CRITICAL** ⚠️
Your bot makes many API calls to Yahoo Finance, which has aggressive rate limiting:
- **Staggered Startup**: Takes 40 minutes for all alerts to begin
- **Per-Stock Delays**: 15 seconds between stock queries
- **Alert Spacing**: 30 seconds minimum between alert types
- **Yahoo API**: 12-second base delay, 30-second batch cooldown

**Don't reduce these delays** or you'll get 401/422 errors and potential IP bans!

#### **Long-Running Process**
- Bot runs continuously 24/7
- Uses threading for parallel alerts
- Needs platform that supports long-running processes (not serverless)

#### **Data Persistence**
- Alert logs stored in `app/data/logs/`
- State file: `app/data/state.json`
- Consider mounting a volume for persistent storage

#### **Error Handling**
- Bot auto-recovers from API failures
- Telegram errors won't crash the bot
- Check logs regularly for issues

---

## 🚂 Option 1: Railway.app (RECOMMENDED)

**Perfect for beginners and production use!**

### **Setup Steps:**

1. **Create Railway Account**
   - Go to https://railway.app
   - Sign up with GitHub (recommended for easy deployment)

2. **Create New Project**
   ```bash
   # Option A: Deploy from GitHub (recommended)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway auto-detects Dockerfile
   
   # Option B: Deploy from local
   - Install Railway CLI: npm install -g @railway/cli
   - Login: railway login
   - Initialize: railway init
   - Deploy: railway up
   ```

3. **Configure Environment Variables**
   - Go to your project settings
   - Click "Variables"
   - Add all required environment variables (see checklist above)
   - **IMPORTANT**: Add each one individually, don't paste .env file directly

4. **Configure Start Command**
   - Railway should auto-detect `bot_interactive.py`
   - If not, set start command: `python bot_interactive.py`
   - Or use Dockerfile (recommended): Railway will auto-detect

5. **Deploy**
   - Click "Deploy"
   - Watch logs for successful startup
   - Look for: "✅ Telegram Stock Alert Bot v2.0.0 - Modular started!"

6. **Verify Deployment**
   - Check Railway logs for errors
   - Send `/start` to your Telegram bot
   - Verify you get a welcome message
   - Wait 1 minute, you should see first alert (General Stock)

### **Railway Pros:**
- ✅ Auto-restart on crashes
- ✅ Easy GitHub integration
- ✅ Built-in monitoring and logs
- ✅ Free tier: 500 hours/month ($5 for unlimited)
- ✅ Automatic HTTPS
- ✅ Easy environment variable management

### **Railway Cost:**
- **Free**: 500 execution hours/month + $5 credit
- **Pro**: $20/month for higher limits
- Your bot will use ~720 hours/month (24/7), so ~$10-15/month after free credit

---

## 🎨 Option 2: Render.com

### **Setup Steps:**

1. **Create Render Account**
   - Go to https://render.com
   - Sign up with GitHub

2. **Create New Web Service**
   - Click "New +" → "Background Worker" (not Web Service!)
   - Connect your GitHub repository
   - Render auto-detects Python

3. **Configure Service**
   ```
   Name: telegram-stock-bot
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python bot_interactive.py
   ```

4. **Set Environment Variables**
   - In service settings, add all variables from checklist
   - Use "Environment" tab

5. **Deploy**
   - Click "Create Background Worker"
   - Monitor logs for successful startup

### **Render Pros:**
- ✅ Free tier available (750 hours/month)
- ✅ Simple interface
- ✅ Automatic deploys from Git
- ✅ Built-in metrics

### **Render Cons:**
- ⚠️ Free tier spins down after 15 minutes of inactivity
- ⚠️ Need paid plan ($7/month) for 24/7 operation

---

## 🐳 Option 3: Docker on Any VPS

**Best for full control and running multiple services**

### **1. Get a VPS**
Choose any provider:
- **DigitalOcean**: $6/month droplet (1GB RAM)
- **Linode**: $5/month nanode (1GB RAM)
- **AWS EC2**: t3.micro (~$8/month, free tier available)
- **Hetzner**: €4.51/month (cheapest option)

### **2. Server Setup**
```bash
# SSH into your server
ssh root@your_server_ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y
```

### **3. Deploy Bot**
```bash
# Clone your repository
git clone https://github.com/joeyflng/ds2-capstone-telegram-ai-alerts.git
cd ds2-capstone-telegram-ai-alerts

# Create .env file with your credentials
nano .env
# Paste your environment variables, save (Ctrl+X, Y, Enter)

# Build and run with Docker
docker build -t telegram-bot .
docker run -d \
  --name telegram-stock-bot \
  --restart unless-stopped \
  --env-file .env \
  telegram-bot

# Check logs
docker logs -f telegram-stock-bot
```

### **4. Auto-Restart on Server Reboot**
```bash
# Bot will auto-restart due to --restart unless-stopped flag
# To manually manage:
docker start telegram-stock-bot   # Start
docker stop telegram-stock-bot    # Stop
docker restart telegram-stock-bot # Restart
```

### **5. Keep Bot Updated**
```bash
# Pull latest code
cd ds2-capstone-telegram-ai-alerts
git pull

# Rebuild and restart
docker stop telegram-stock-bot
docker rm telegram-stock-bot
docker build -t telegram-bot .
docker run -d \
  --name telegram-stock-bot \
  --restart unless-stopped \
  --env-file .env \
  telegram-bot
```

### **VPS Pros:**
- ✅ Full control
- ✅ Can run multiple services
- ✅ Fixed monthly cost
- ✅ No platform limitations

### **VPS Cons:**
- ⚠️ Need to manage server security
- ⚠️ More setup time
- ⚠️ Need basic Linux knowledge

---

## 🏠 Option 4: Run on Your Own Computer/Raspberry Pi

**Free option for testing or personal use**

### **Requirements:**
- Computer/Raspberry Pi that can run 24/7
- Python 3.11+ installed
- Stable internet connection

### **Setup:**

1. **Clone Repository**
   ```bash
   git clone https://github.com/joeyflng/ds2-capstone-telegram-ai-alerts.git
   cd ds2-capstone-telegram-ai-alerts
   ```

2. **Install Dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   nano .env  # Add your API keys
   ```

4. **Run Bot**
   ```bash
   # Simple run
   python bot_interactive.py
   
   # Keep running in background (Linux/Mac)
   nohup python bot_interactive.py > bot.log 2>&1 &
   
   # Check logs
   tail -f bot.log
   ```

5. **Auto-Start on Boot (Linux)**
   ```bash
   # Create systemd service
   sudo nano /etc/systemd/system/telegram-bot.service
   ```
   
   Paste this content:
   ```ini
   [Unit]
   Description=Telegram Stock Bot
   After=network.target
   
   [Service]
   Type=simple
   User=your_username
   WorkingDirectory=/path/to/ds2-capstone-telegram-ai-alerts
   ExecStart=/path/to/venv/bin/python bot_interactive.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   Enable and start:
   ```bash
   sudo systemctl enable telegram-bot
   sudo systemctl start telegram-bot
   sudo systemctl status telegram-bot
   ```

### **Pros:**
- ✅ Free (only electricity cost)
- ✅ Complete control
- ✅ Great for learning

### **Cons:**
- ⚠️ Computer must run 24/7
- ⚠️ Internet downtime = bot downtime
- ⚠️ Home IP might get rate limited more aggressively

---

## 🔍 Post-Deployment Monitoring

### **1. Check Bot Startup**
Look for these messages in logs:
```
✅ Telegram Stock Alert Bot v2.0.0 - Modular started!
📊 Monitoring 2 stocks: NVDA, TSLA
⏰ Alerts staggered over 40 min to prevent rate limiting
🛡️ Enhanced rate protection: 15s between stocks, 30s between alert types
```

### **2. Verify Alert Schedule**
After startup, you should see:
```
📅 Staggered startup delays configured (spread over 40 min to avoid rate limits):
   ⏰ General Stock: starts in 1m, then every 30.0 min
   🎯 52-Week Highs: starts in 10m, then every 40.0 min
   💰 Buy Dips: starts in 20m, then every 30.0 min
   📈 MA Crossovers: starts in 30m, then every 60.0 min
   📊 Earnings: starts in 40m, then every 360.0 min
```

### **3. Monitor for Errors**
Common issues to watch:
- **401/422 Errors**: Rate limited by Yahoo (should be rare with new config)
- **Connection Timeouts**: Network issues
- **Memory Issues**: Bot using too much RAM (shouldn't happen)
- **Telegram API Errors**: Usually temporary, bot will retry

### **4. Test Bot Functionality**
Send these commands to verify:
```
/start          # Should get welcome message
NVDA            # Should get brief company summary
/quote TSLA     # Should get detailed quote
/add AAPL       # Should add to watchlist
/list           # Should show watchlist
```

### **5. Check Alert Delivery**
- **1 minute after startup**: General Stock alert
- **10 minutes**: 52-Week High alert
- **20 minutes**: Buy Dip alert
- **30 minutes**: MA Crossover alert
- **40 minutes**: Earnings alert

---

## 🛠️ Troubleshooting

### **Bot Won't Start**
```bash
# Check Python version
python --version  # Should be 3.11+

# Verify dependencies
pip install -r requirements.txt

# Check environment variables
python -c "import os; print(os.getenv('TELEGRAM_BOT_TOKEN'))"
```

### **Rate Limiting Issues (401/422 Errors)**
If you still see rate limiting:
1. **Increase delays further** in `.env`:
   ```bash
   ALERT_STOCK_INTERVAL=3600  # 1 hour instead of 30 min
   ```
2. **Check Yahoo Finance status**: https://downdetector.com/status/yahoo/
3. **Consider using only FMP**: Set higher FMP_DELAY_SECONDS

### **Telegram Messages Not Sending**
```bash
# Verify bot token
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"

# Verify chat ID
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates"
```

### **High Memory Usage**
```bash
# Check memory
docker stats telegram-stock-bot

# If too high, reduce chart generation or add memory limit
docker run -d --memory="512m" ...
```

### **Bot Crashes Frequently**
- Check logs for specific errors
- Verify all API keys are valid
- Ensure stable network connection
- Consider using a more reliable hosting platform

---

## 💰 Cost Comparison

| Platform | Free Tier | Paid Tier | Best For |
|----------|-----------|-----------|----------|
| **Railway** | 500 hrs/month + $5 credit | ~$10-15/month | Production, beginners |
| **Render** | 750 hrs/month (sleeps) | $7/month | Side projects |
| **Heroku** | No free tier | $7/month | Mature deployments |
| **DigitalOcean** | No free tier | $6/month | Full control |
| **AWS EC2** | 750 hrs/month (1 year) | ~$8/month | Enterprise |
| **Home/Pi** | Free (electricity) | ~$5/year electricity | Learning, testing |

---

## 🎯 Recommended Deployment Strategy

### **For Production (24/7 reliable operation):**
1. **Railway.app** - Best balance of ease and features
2. Deploy from GitHub for automatic updates
3. Use paid tier ($10-15/month) for reliability
4. Set up monitoring and alerts

### **For Development/Testing:**
1. Run locally on your computer
2. Test all features thoroughly
3. Monitor rate limiting behavior
4. Then deploy to Railway/Render

### **For Learning/Portfolio:**
1. Deploy to Railway free tier initially
2. Document the deployment process
3. Keep logs of performance
4. Can upgrade to paid if needed

---

## 🚀 Quick Deployment Commands

### **Railway (with CLI)**
```bash
npm install -g @railway/cli
railway login
railway init
railway add
railway up
```

### **Docker on VPS**
```bash
ssh root@your_server
git clone https://github.com/joeyflng/ds2-capstone-telegram-ai-alerts.git
cd ds2-capstone-telegram-ai-alerts
nano .env  # Add your keys
docker build -t telegram-bot .
docker run -d --name telegram-stock-bot --restart unless-stopped --env-file .env telegram-bot
```

### **Local Background Process**
```bash
cd ds2-capstone-telegram-ai-alerts
source venv/bin/activate
nohup python bot_interactive.py > bot.log 2>&1 &
tail -f bot.log
```

---

## 📞 Need Help?

- **Logs not showing**: Check your platform's log viewer
- **Bot not responding**: Verify TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
- **Rate limiting**: Don't reduce the delays - they're optimized!
- **Platform-specific issues**: Check platform documentation

**Remember**: The bot takes 40 minutes to fully start all alerts due to staggered timing. This is intentional to prevent rate limiting!

---

**🎉 Once deployed, your bot will monitor stocks 24/7 and send alerts directly to your Telegram!**
