# 🤖 Trading Bot - Railway Deployment

A sophisticated FX trading analysis bot with **Financial Modeling Prep (FMP)** integration, deployable on Railway.

## 🎯 Features

- **📊 Multi-Asset Analysis**: FX pairs, cryptocurrencies, and metals
- **⏰ 3-Timeframe Framework**: 4H (bias), 30M (POI), 5M (confirmation)
- **🔍 Technical Analysis**: BOS/MSS, Order Blocks, Fair Value Gaps, Liquidity Sweeps
- **🤖 AI Verification**: Optional LLM-based rule confirmation
- **📱 Private Telegram Bot**: Single-user authorization for privacy
- **⚡ Real-time Data**: Powered by Financial Modeling Prep (free tier)

## 🚀 Quick Railway Deploy

### 1. Clone & Deploy
```bash
git clone https://github.com/yourusername/trading-bot.git
cd trading-bot
railway up
```

### 2. Set Environment Variables
In Railway dashboard, configure:
```env
DATA_PROVIDER=fmp
FMP_API_KEY=demo
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ALLOWED_USER_ID=your_user_id
DEFAULT_SYMBOL=EUR/USD
```

### 3. Start Trading
Your bot will be live and ready for commands:
- `/analyze EURUSD` - Forex analysis
- `/analyze BTCUSD` - Bitcoin analysis  
- `/analyze XAUUSD` - Gold analysis
- `/start` - Initialize bot

## 📈 Supported Assets

### FX Pairs (17)
EURUSD, GBPUSD, AUDUSD, USDJPY, USDCAD, NZDUSD, EURGBP, EURJPY, GBPJPY, AUDJPY, EURCHF, USDCHF

### Cryptocurrencies (7)
BTCUSD, ETHUSD, BNBUSD, ADAUSD, SOLUSD, XRPUSD, DOGEUSD

### Metals (4)
XAUUSD (Gold), XAGUSD (Silver), XPTUSD (Platinum), XPDUSD (Palladium)

## 🔧 Configuration

- **Data Provider**: Financial Modeling Prep (free, no API limits)
- **Timeframes**: 5M, 30M, 4H, 1D, 1W
- **Risk Management**: Configurable R-multiple (default: 2.0)
- **Private Access**: Telegram user authorization

## 📊 Analysis Framework

### 4-Step Signal Generation
1. **Direction**: 4H bias (BOS/MSS confirmation)
2. **POI**: 30M zone detection (OB/FVG minimum)
3. **Liquidity**: Required sweep into/near POI
4. **Confirmation**: 5M trigger aligned with bias

### Market Structure
- **Break of Structure (BOS)**: Trend continuation signals
- **Market Structure Shift (MSS)**: Trend reversal signals
- **Order Blocks**: Institutional buying/selling zones
- **Fair Value Gaps**: Imbalance opportunities
- **Liquidity Sweeps**: Stop hunt patterns

## 🛠️ Tech Stack

- **Backend**: Python 3.11
- **Bot Framework**: python-telegram-bot
- **Data API**: Financial Modeling Prep
- **Database**: SQLite (persistent storage)
- **Scheduler**: APScheduler (automated analysis)
- **Deployment**: Railway + Docker

## 📱 Telegram Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Initialize bot | `/start` |
| `/analyze [SYMBOL]` | Analyze asset | `/analyze BTCUSD` |
| `/set SYMBOL` | Set default | `/set EURUSD` |
| `/status` | Last analysis | `/status` |
| `/watch SYMBOL MIN` | Schedule analysis | `/watch EURUSD 30` |
| `/stopwatch` | Stop scheduling | `/stopwatch` |
| `/help` | Show help | `/help` |

## 🔒 Security

- **Private Bot**: Only authorized user can interact
- **Environment Variables**: Sensitive data in Railway, not code
- **No Auto-trading**: Analysis only, no execution
- **API Security**: FMP HTTPS endpoints

## 📈 Performance

- **Free Tier**: No rate limits on FMP
- **Fast Analysis**: Sub-second response times
- **Reliable Data**: Professional-grade market data
- **24/7 Operation**: Railway auto-scaling

## 🚀 Deploy Now

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=trading-bot)

**Your professional trading bot is ready for Railway deployment!**

---

*⚠️ Educational purposes only. Not financial advice. Trade at your own risk.*
