# 🚀 Railway Deployment Guide

## 📋 Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Account**: For repository hosting
3. **Railway CLI**: Install Railway CLI

## 🔧 Setup Steps

### 1. Prepare Your Repository

```bash
# Initialize git if not already done
git init

# Add all files
git add .

# Commit changes
git commit -m "Initial commit: Trading bot with FMP integration"

# Create GitHub repository (replace with your repo URL)
git remote add origin https://github.com/yourusername/trading-bot.git

# Push to GitHub
git push -u origin main
```

### 2. Configure Railway Environment Variables

In Railway dashboard, set these environment variables:

```env
DATA_PROVIDER=fmp
FMP_API_KEY=demo
TELEGRAM_BOT_TOKEN=8017226274:AAG4VUBmlzqbwhAEYLHyqypwmvEgzUkI-s4
TELEGRAM_ALLOWED_USER_ID=6335623901
DEFAULT_SYMBOL=EUR/USD
DEFAULT_RISK_R=2.0
```

### 3. Deploy to Railway

#### Option A: Using Railway CLI
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Deploy from GitHub
railway up
```

#### Option B: Using Railway Dashboard
1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Connect your GitHub repository
4. Railway will auto-detect and deploy

## 🔍 Important Notes

### Environment Variables
- **Never commit `.env` file** to Git
- Always use Railway's environment variables
- Telegram bot token is sensitive - keep it secure

### Data Provider
- **FMP (Financial Modeling Prep)**: Free tier, no API key required
- **Alternative**: Switch to `alphavantage` or `oanda` if needed

### Bot Configuration
- **Default Symbol**: EUR/USD (can be changed)
- **Risk Management**: Default R:2.0 (adjustable)
- **User Authorization**: Only your Telegram user ID

## 🐛 Troubleshooting

### Common Issues

1. **Bot doesn't start**
   - Check all environment variables in Railway
   - Verify Telegram bot token is valid
   - Ensure user ID is correct

2. **API errors**
   - FMP demo key works for basic usage
   - For production, get free API key at [fmp.dev](https://fmp.dev)

3. **Deployment fails**
   - Check `requirements.txt` dependencies
   - Verify `Dockerfile` syntax
   - Review Railway logs

### Logs
```bash
# View Railway logs
railway logs

# View specific service logs
railway logs <service-name>
```

## 📱 Testing Your Bot

After deployment:

1. **Start your bot**: It will run automatically
2. **Send test commands** on Telegram:
   ```bash
   /start
   /analyze EURUSD
   /analyze BTCUSD
   /analyze XAUUSD
   /help
   ```

3. **Monitor**: Check Railway dashboard for logs and status

## 🔄 Updates

To update your bot:
```bash
# Make changes locally
git add .
git commit -m "Update: feature description"
git push origin main

# Railway will auto-redeploy on push
```

## 📊 Monitoring

- **Railway Dashboard**: Monitor usage, logs, metrics
- **Telegram Bot**: Test commands regularly
- **FMP API**: Monitor rate limits (generous free tier)

## 🎯 Production Tips

1. **Get FMP API Key**: For production use, register at [fmp.dev](https://fmp.dev)
2. **Security**: Never expose sensitive data
3. **Backups**: Railway handles persistence
4. **Scaling**: Railway auto-scales as needed

---

**🚀 Your trading bot is ready for Railway deployment!**

Deploy now and start analyzing FX, crypto, and metals markets!
