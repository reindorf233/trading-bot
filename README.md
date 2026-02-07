# 🌍 Public Trading Bot - Free Analysis with Deriv

A sophisticated **public trading analysis bot** with **Deriv API** integration, providing comprehensive market analysis across FX, cryptocurrencies, and metals using a 3-timeframe technical framework.

## 🎯 Features

- **📊 Multi-Asset Analysis**: 17 FX pairs + 7 cryptocurrencies + 4 metals
- **⏰ 3-Timeframe Framework**: 4H (bias), 30M (POI), 5M (confirmation)
- **🔍 Technical Analysis**: BOS/MSS, Order Blocks, Fair Value Gaps, Liquidity Sweeps
- **🤖 AI Verification**: Optional LLM-based rule confirmation
- **📱 Public Telegram Bot**: Anyone can use it for FREE
- **⚡ Real-time Data**: Powered by Deriv API (completely free, no API key)
- **🚀 Production Ready**: Docker containerized for Railway deployment

## 🌍 **Try the Bot Now!**

**Bot Link**: [Click here to start using @rulerfxbot](https://t.me/rulerfxbot)

## 📊 Analysis Framework

### Timeframes
- **4H**: Market bias and direction (BOS/MSS)
- **30M**: Point of Interest detection and liquidity sweep narrative
- **5M**: Entry trigger confirmation

### 4-Step Signal Rules
1. **Direction**: Clear bias from 4H BOS/MSS
2. **POI**: Valid zone aligned with bias (OB/FVG minimum)
3. **Liquidity**: Sweep narrative supporting bias
4. **Confirmation**: Entry trigger aligned with POI

### AI-Powered Verification
- **Strategy Confirmation**: OpenAI GPT validates signal logic
- **Risk Assessment**: AI evaluates missing conditions
- **Confidence Scoring**: AI provides probability estimates
- **Rule Compliance**: Ensures all technical rules met

## 🚀 **Technology Stack**

### Data Provider: Deriv API
- **🆓 Completely Free**: No subscription required
- **⚡ Real-time Data**: Live market prices
- **🔄 No Rate Limits**: Unlimited requests
- **🌍 Global Access**: Available worldwide
- **📈 Multiple Assets**: FX, crypto, metals

### Supported Assets

#### Forex Pairs
- **Major**: EURUSD, GBPUSD, USDJPY, USDCHF
- **Commodity**: AUDUSD, NZDUSD, USDCAD
- **Cross**: EURGBP, EURJPY, GBPJPY, EURAUD

#### Cryptocurrencies
- **Top Coins**: BTCUSD, ETHUSD, LTCUSD, BCHUSD
- **Altcoins**: ADAUSD, SOLUSD, XRPUSD, DOGEUSD

#### Metals
- **Precious**: XAUUSD (Gold), XAGUSD (Silver)

### Technical Indicators
- **Market Structure**: BOS/MSS analysis
- **Order Blocks**: Smart money concepts
- **Fair Value Gaps**: Imbalance detection
- **Liquidity Sweeps**: Stop hunt identification
- **Swing Analysis**: High/low pattern recognition

## 🤖 **Bot Features**

### Interactive Interface
- **🎨 Modern Menus**: Beautiful inline keyboards
- **📱 Mobile Optimized**: Perfect for Telegram
- **🔗 Easy Sharing**: One-click bot sharing
- **⚡ Quick Analysis**: One-tap symbol analysis

### Analysis Capabilities
- **📊 Real-time Signals**: Live market analysis
- **🤖 AI Confirmation**: Strategy validation
- **📈 Multi-timeframe**: 4H/30M/5M analysis
- **🎯 Risk Management**: Entry/exit levels

### User Experience
- **🆓 Completely Free**: No charges or restrictions
- **🌍 Public Access**: Anyone can use the bot
- **📊 Professional Results**: High-quality analysis
- **🔔 Instant Updates**: Real-time notifications

## 📱 **How to Use**

### Quick Start
1. **Open Telegram**: Search for `@rulerfxbot`
2. **Start Bot**: Send `/start` command
3. **Choose Asset**: Select from interactive menu
4. **Get Analysis**: Receive professional trading signals

### Available Commands
- `/start` - Show main menu
- `/analyze [SYMBOL]` - Analyze specific symbol
- `/help` - Show help information
- `/status` - View last analysis

### Interactive Menu
```bash
📈 Forex Pairs    🪙 Crypto
🥇 Metals        ⚡ Quick Analysis  
📊 My Status     ⚙️ Settings
🔗 Share Bot     ❓ Help
```

## 🚀 **Deployment**

### Railway Deployment
```bash
# Environment Variables
DATA_PROVIDER=deriv
DERIV_APP_ID=1089
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ALLOWED_USER_ID=your_user_id
OPENAI_API_KEY=your_openai_key
```

### Quick Deploy
1. **Push to GitHub**: `git push origin main`
2. **Connect Railway**: Link your GitHub repository
3. **Set Environment**: Add required variables
4. **Deploy**: Railway builds and deploys automatically

## 🛠️ **Local Development**

### Setup
```bash
# Clone repository
git clone https://github.com/reindorf233/trading-bot.git
cd trading-bot

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your tokens

# Run bot
python run_bot.py
```

### Requirements
- **Python 3.11+**
- **Telegram Bot Token**
- **OpenAI API Key** (optional for AI verification)
- **Deriv API** (free, no key required)

## 📊 **Analysis Results**

### Signal Format
```bash
🟢 EURUSD Analysis
🕐 2026-02-07 14:36 UTC
📊 Timeframes: 4H | 30M | 5M

🎯 SIGNAL: ✅ BUY (Confidence: 85%)

📈 MARKET BIAS:
Direction: BULLISH
4H Trend: BOS
4H Event: BOS

🎯 POINT OF INTEREST:
Type: Order Block
Zone: 1.0850-1.0870

💧 LIQUIDITY:
Sweep: Yes

⚡ CONFIRMATION:
Pattern: Bullish Engulfing

🤖 AI ANALYSIS:
Strategy: Valid bullish setup
Confidence: High
Risk: Manage below 1.0820
```

## 🔒 **Security & Privacy**

### Data Protection
- **🔒 No Personal Data**: No user data collection
- **🛡️ Secure API**: HTTPS encrypted connections
- **🔐 Private Bot**: Only authorized access
- **📊 Anonymous**: No tracking or analytics

### API Security
- **� Secure Tokens**: Encrypted storage
- **� HTTPS Only**: Secure connections only
- **� Rate Limiting**: Built-in protection
- **🛡️ Input Validation**: Sanitized inputs

## ⚠️ **Disclaimer**

**Educational Purpose Only**
- This bot provides analysis for educational purposes
- Not financial advice or investment recommendations
- Trade at your own risk
- Past performance does not guarantee future results

## � **Why Choose This Bot?**

### For Traders
- **🆓 Completely Free**: No subscription fees
- **⚡ Real-time Data**: Live market prices
- **🤖 AI Enhanced**: Strategy validation
- **📱 Easy to Use**: Simple interface

### For Developers
- **🚀 Open Source**: Free to modify and deploy
- **📚 Well Documented**: Clear code structure
- **🔧 Easy Setup**: One-click deployment
- **🌍 Scalable**: Handles multiple users

### For Communities
- **📊 Professional Analysis**: High-quality signals
- **🔗 Easy Sharing**: Viral growth potential
- **🌍 Global Access**: Available worldwide
- **💫 Modern Interface**: Beautiful user experience

## 📞 **Support**
## ⚙️ Configuration Options

```python
# Analysis parameters
SWING_LOOKBACK = 3              # Swing detection lookback
FVG_TOLERANCE = 0.0001         # Fair Value Gap tolerance
LIQUIDITY_TOLERANCE = 0.0005   # Liquidity pool tolerance
POI_PROXIMITY_CANDLES = 10     # POI proximity (30M)
CONFIRMATION_PROXIMITY_CANDLES = 20  # Confirmation proximity (5M)

# Risk management
DEFAULT_RISK_R = 2.0           # Default R-multiple for targets
```

## 🔧 Advanced Features

### AI Verification (Optional)

Enable AI-based rule verification by setting:
```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview
```

The AI verifier:
- Reviews structured analysis data
- Can adjust confidence but cannot override hard rule failures
- Provides additional reasoning and risk assessment

### Data Provider Extensibility

The bot supports multiple data providers through a common interface:
- **OANDA**: Default FX data provider
- **TradingView**: Optional (stub implementation)
- **Binance**: Crypto support (stub implementation)

## 🚨 Important Notes

- **Private Bot**: Only authorized user can interact
- **Analysis Only**: No auto-trading functionality
- **Educational Purpose**: Not financial advice
- **Practice Mode**: Use OANDA practice environment initially

## 🐛 Troubleshooting

### Common Issues

1. **"Unauthorized access" error**
   - Check `TELEGRAM_ALLOWED_USER_ID` in .env
   - Verify your user ID with @userinfobot

2. **"Insufficient data" error**
   - Check OANDA API credentials
   - Verify symbol format (try EUR_USD)

3. **Bot doesn't start**
   - Verify all required environment variables
   - Check bot token with @BotFather

### Logs

Check `bot.log` for detailed error information:
```bash
tail -f bot.log
```

## 📝 License

This project is for educational and personal use only.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

---

**⚠️ DISCLAIMER**: This bot provides technical analysis for educational purposes only. It is not financial advice. Trading carries substantial risk of loss. Always do your own research and trade at your own risk.
