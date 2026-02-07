# 🤖 Professional Trading Bot - Multi-Asset Analysis

A sophisticated trading analysis bot with **Financial Modeling Prep (FMP)** integration, providing comprehensive market analysis across FX, cryptocurrencies, and metals using a 3-timeframe technical framework.

## 🎯 Features

- **📊 Multi-Asset Analysis**: 17 FX pairs + 7 cryptocurrencies + 4 metals
- **⏰ 3-Timeframe Framework**: 4H (bias), 30M (POI), 5M (confirmation)
- **🔍 Technical Analysis**: BOS/MSS, Order Blocks, Fair Value Gaps, Liquidity Sweeps
- **🤖 AI Verification**: Optional LLM-based rule confirmation
- **📱 Public Telegram Bot**: Anyone can use the trading analysis
- **⚡ Real-time Data**: Powered by Financial Modeling Prep (free tier)
- **🚀 Production Ready**: Docker containerized for Railway deployment

## 📊 Analysis Framework

### Timeframes
- **4H**: Market bias and direction (BOS/MSS)
- **30M**: Point of Interest detection and liquidity sweep narrative
- **5M**: Entry trigger confirmation

### 4-Step Signal Rules
1. **Direction**: Clear bias from 4H BOS/MSS
2. **POI**: Valid zone aligned with bias (OB/FVG minimum)
3. **Liquidity**: Sweep into/near POI required
4. **Confirmation**: 5M trigger aligned with bias

Only when ALL steps pass does the bot generate ✅ BUY or ✅ SELL signals.

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd trading-bot

# Install dependencies
pip install -r requirements.txt
```

### 2. Get Alpha Vantage API Key (Recommended)

Alpha Vantage offers a **free tier** with 500 requests/day:

1. Go to [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Sign up for a free account
3. Get your API key from the dashboard
4. No credit card required for free tier

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
```

Required environment variables:
```env
# Data Provider (choose one)
DATA_PROVIDER=alphavantage

# Alpha Vantage (recommended - free tier available)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_ALLOWED_USER_ID=your_telegram_user_id_here

# Trading Configuration
DEFAULT_SYMBOL=EUR/USD
DEFAULT_RISK_R=2.0
```

### 4. Get Telegram Bot Token

1. Talk to [@BotFather](https://t.me/BotFather) on Telegram
2. Create a new bot with `/newbot`
3. Copy the bot token

### 5. Get Your Telegram User ID

1. Talk to [@userinfobot](https://t.me/userinfobot) on Telegram
2. Copy your user ID

### 6. Run Bot

```bash
cd bot
python main.py
```

## 📱 Bot Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Start using the bot | `/start` |
| `/analyze [SYMBOL]` | Analyze a symbol | `/analyze EURUSD` |
| `/set SYMBOL` | Set default symbol | `/set GBPUSD` |
| `/status` | Show last analysis | `/status` |
| `/watch SYMBOL MINUTES` | Schedule analysis | `/watch EURUSD 30` |
| `/stopwatch` | Stop scheduled analysis | `/stopwatch` |
| `/help` | Show help message | `/help` |

## � Data Providers

### Alpha Vantage (Recommended)
- **Free tier available** with 500 requests/day
- No credit card required
- Easy signup process
- Supports major FX pairs

### FX Pairs
- EURUSD (EUR/USD, EUR_USD)
- GBPUSD (GBP/USD, GBP_USD)
- AUDUSD (AUD/USD, AUD_USD)
- USDJPY (USD/JPY, USD_JPY)
- USDCAD (USD/CAD, USD_CAD)
- NZDUSD (NZD/USD, NZD_USD)

### Crypto Pairs (against USD)
- BTCUSD (Bitcoin/USD)
- ETHUSD (Ethereum/USD)
- BNBUSD (Binance Coin/USD)
- ADAUSD (Cardano/USD)
- SOLUSD (Solana/USD)
- XRPUSD (Ripple/USD)
- DOGEUSD (Dogecoin/USD)

### Metals (against USD)
- XAUUSD (Gold/USD)
- XAGUSD (Silver/USD)
- XPTUSD (Platinum/USD)
- XPDUSD (Palladium/USD)

### Symbol Format
All formats are automatically normalized:
- `EURUSD`, `EUR/USD`, `EUR_USD` → `EUR/USD`
- `BTCUSD` → `BTC/USD`
- `XAUUSD` → `XAU/USD` (Gold)

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_fvg.py

# Run with coverage
pytest --cov=bot tests/
```

## 📊 Example Output

### ✅ BUY Signal
```
🟢 EURUSD Analysis
🕐 2024-01-07 15:30 UTC
📊 Timeframes: 4H | 30M | 5M

🎯 SIGNAL: ✅ BUY (Confidence: 85%)

📈 MARKET BIAS:
Direction: LONG
4H Trend: uptrend
4H Event: BOS_UP
Swing High: 1.09550

🎯 POINT OF INTEREST:
Type: OB
Zone: 1.08920-1.08980
Strength: 0.85

💧 LIQUIDITY:
Sweep: Yes
Pool Type: EQUAL_LOWS
Sweep Price: 1.08910

⚡ CONFIRMATION:
Pattern: BREAK_ENTRY
Confidence: 0.80

💼 TRADE PLAN:
Entry Zone: 1.08920-1.08980
Invalidation: 1.08920
Target 1: 1.09550
Target 2: 1.09980

🤖 AI ANALYSIS:
Direction: Strong bullish BOS confirmed
POI: Quality order block in uptrend
Liquidity: Clear sweep of equal lows
Confirmation: Break and retest pattern

⚠️ DISCLAIMER:
This analysis is for educational purposes only.
Not financial advice. Trade at your own risk.
```

### ⚠️ NO-TRADE Signal
```
⚠️ EURUSD Analysis
🕐 2024-01-07 15:30 UTC
📊 Timeframes: 4H | 30M | 5M

🎯 SIGNAL: ⚠️ NO TRADE (Confidence: 40%)

📈 MARKET BIAS:
Direction: NEUTRAL
4H Trend: sideways
4H Event: NONE

🎯 POINT OF INTEREST:
Type: None

💧 LIQUIDITY:
Sweep: No

⚡ CONFIRMATION:
Pattern: None

🤖 AI ANALYSIS:
Direction: No clear bias established
POI: No valid POI detected
Liquidity: No liquidity sweep detected
Confirmation: No confirmation pattern
Missing: No clear 4H bias, No valid POI detected, No liquidity sweep detected, No confirmation pattern
```

## 🏗️ Project Structure

```
bot/
├── main.py                 # Main bot entry point
├── config.py              # Configuration management
├── storage.py             # SQLite database storage
├── providers/             # Data providers
│   ├── base.py           # Base provider interface
│   ├── oanda.py          # OANDA REST API
│   ├── tradingview.py    # TradingView (stub)
│   └── binance.py        # Binance (stub)
├── analysis/              # Analysis components
│   ├── swings.py         # Swing point detection
│   ├── structure.py      # BOS/MSS analysis
│   ├── poi.py            # POI detection
│   ├── liquidity.py      # Liquidity analysis
│   ├── confirmation.py   # Pattern confirmation
│   ├── signal_engine.py  # Main analysis engine
│   └── ai_verifier.py    # AI rule verification
├── telegram/              # Telegram interface
│   ├── auth.py           # User authorization
│   ├── handlers.py       # Command handlers
│   └── formatters.py     # Message formatting
└── tests/                 # Unit tests
    ├── test_fvg.py
    ├── test_swings.py
    ├── test_bos_mss.py
    └── test_patterns.py
```

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
