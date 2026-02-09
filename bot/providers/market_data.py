"""
Real-time market data provider for accurate asset pricing
"""

import asyncio
import json
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging

# Try to import aiohttp, make it optional
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None

logger = logging.getLogger(__name__)


class MarketDataProvider:
    """Real-time market data provider for accurate asset pricing."""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes cache
        self.available = AIOHTTP_AVAILABLE
        
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price for symbol."""
        if not self.available:
            logger.warning("aiohttp not available - market data disabled")
            return None
        
        # Check cache first
        cache_key = f"price_{symbol}"
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if datetime.utcnow() - cached_data['timestamp'] < timedelta(seconds=self.cache_timeout):
                return cached_data['price']
        
        # Try multiple data sources
        price = await self._fetch_from_multiple_sources(symbol)
        
        if price:
            # Cache the result
            self.cache[cache_key] = {
                'price': price,
                'timestamp': datetime.utcnow()
            }
            return price
        
        return None
    
    async def get_price_range(self, symbol: str) -> Tuple[float, float]:
        """Get realistic price range for symbol based on current market data."""
        current_price = await self.get_current_price(symbol)
        
        if not current_price:
            # Fallback to hardcoded ranges if no live data
            return self._get_fallback_range(symbol)
        
        # Calculate range based on current price and asset type
        if self._is_crypto(symbol):
            # Crypto: ±20% range
            min_price = current_price * 0.8
            max_price = current_price * 1.2
        elif self._is_gold(symbol):
            # Gold: ±5% range (less volatile)
            min_price = current_price * 0.95
            max_price = current_price * 1.05
        elif self._is_metal(symbol):
            # Other metals: ±10% range
            min_price = current_price * 0.9
            max_price = current_price * 1.1
        elif self._is_index(symbol):
            # Indices: ±3% range
            min_price = current_price * 0.97
            max_price = current_price * 1.03
        else:
            # Forex: ±2% range
            min_price = current_price * 0.98
            max_price = current_price * 1.02
        
        return (min_price, max_price)
    
    async def _fetch_from_multiple_sources(self, symbol: str) -> Optional[float]:
        """Fetch price from multiple data sources."""
        sources = [
            self._fetch_from_yahoo_finance,
            self._fetch_from_coinmarketcap,
            self._fetch_from_coingecko,
            self._fetch_from_alpha_vantage
        ]
        
        for source in sources:
            try:
                price = await source(symbol)
                if price and price > 0:
                    return price
            except Exception as e:
                logger.warning(f"Source failed for {symbol}: {e}")
                continue
        
        return None
    
    async def _fetch_from_yahoo_finance(self, symbol: str) -> Optional[float]:
        """Fetch price from Yahoo Finance API."""
        try:
            # Map symbols to Yahoo Finance format
            yahoo_symbol = self._map_to_yahoo_symbol(symbol)
            
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'chart' in data and data['chart']['result']:
                            result = data['chart']['result'][0]
                            if 'meta' in result and 'regularMarketPrice' in result['meta']:
                                return float(result['meta']['regularMarketPrice'])
        except Exception as e:
            logger.debug(f"Yahoo Finance error for {symbol}: {e}")
        
        return None
    
    async def _fetch_from_coinmarketcap(self, symbol: str) -> Optional[float]:
        """Fetch price from CoinMarketCap (crypto only)."""
        if not self._is_crypto(symbol):
            return None
        
        try:
            # Map crypto symbols to CoinMarketCap format
            cmc_symbol = self._map_to_cmc_symbol(symbol)
            
            url = f"https://api.coinmarketcap.com/data-api/v3/cryptocurrency/detail?slug={cmc_symbol}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'data' in data and 'quotes' in data['data']:
                            quotes = data['data']['quotes']
                            if 'USD' in quotes:
                                return float(quotes['USD']['price'])
        except Exception as e:
            logger.debug(f"CoinMarketCap error for {symbol}: {e}")
        
        return None
    
    async def _fetch_from_coingecko(self, symbol: str) -> Optional[float]:
        """Fetch price from CoinGecko (crypto only)."""
        if not self._is_crypto(symbol):
            return None
        
        try:
            # Map crypto symbols to CoinGecko format
            gecko_symbol = self._map_to_gecko_symbol(symbol)
            
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={gecko_symbol}&vs_currencies=usd"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if gecko_symbol in data:
                            return float(data[gecko_symbol]['usd'])
        except Exception as e:
            logger.debug(f"CoinGecko error for {symbol}: {e}")
        
        return None
    
    async def _fetch_from_alpha_vantage(self, symbol: str) -> Optional[float]:
        """Fetch price from Alpha Vantage (stocks, forex, indices)."""
        try:
            # Map symbols to Alpha Vantage format
            av_symbol = self._map_to_alpha_symbol(symbol)
            
            # Note: This would require an API key in production
            # For demo purposes, we'll use a free endpoint
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={av_symbol}&apikey=demo"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'Global Quote' in data and '05. price' in data['Global Quote']:
                            return float(data['Global Quote']['05. price'])
        except Exception as e:
            logger.debug(f"Alpha Vantage error for {symbol}: {e}")
        
        return None
    
    def _map_to_yahoo_symbol(self, symbol: str) -> str:
        """Map symbol to Yahoo Finance format."""
        symbol_map = {
            # Crypto
            'BTCUSD': 'BTC-USD',
            'ETHUSD': 'ETH-USD',
            'LTCUSD': 'LTC-USD',
            'BCHUSD': 'BCH-USD',
            'XRPUSD': 'XRP-USD',
            'ADAUSD': 'ADA-USD',
            'DOTUSD': 'DOT-USD',
            'LINKUSD': 'LINK-USD',
            'UNIUSD': 'UNI-USD',
            'SOLUSD': 'SOL-USD',
            'AVAXUSD': 'AVAX-USD',
            'MATICUSD': 'MATIC-USD',
            'DOGEUSD': 'DOGE-USD',
            'BNBUSD': 'BNB-USD',
            
            # Metals
            'XAUUSD': 'GC=F',  # Gold futures
            'XAGUSD': 'SI=F',  # Silver futures
            'XPTUSD': 'PL=F',  # Platinum futures
            'XPDUSD': 'PA=F',  # Palladium futures
            
            # Indices
            'US30': '^DJI',
            'NASDAQ': '^IXIC',
            'SP500': '^GSPC',
            'DAX': '^GDAXI',
            'FTSE': '^FTSE',
            
            # Forex (Yahoo uses different format)
            'EURUSD': 'EURUSD=X',
            'GBPUSD': 'GBPUSD=X',
            'USDJPY': 'USDJPY=X',
            'USDCHF': 'USDCHF=X',
        }
        
        return symbol_map.get(symbol, symbol)
    
    def _map_to_cmc_symbol(self, symbol: str) -> str:
        """Map crypto symbol to CoinMarketCap slug."""
        cmc_map = {
            'BTCUSD': 'bitcoin',
            'ETHUSD': 'ethereum',
            'LTCUSD': 'litecoin',
            'BCHUSD': 'bitcoin-cash',
            'XRPUSD': 'ripple',
            'ADAUSD': 'cardano',
            'DOTUSD': 'polkadot-new',
            'LINKUSD': 'chainlink',
            'UNIUSD': 'uniswap',
            'SOLUSD': 'solana',
            'AVAXUSD': 'avalanche-2',
            'MATICUSD': 'polygon',
            'DOGEUSD': 'dogecoin',
            'BNBUSD': 'bnb',
        }
        
        return cmc_map.get(symbol, symbol.lower().replace('usd', ''))
    
    def _map_to_gecko_symbol(self, symbol: str) -> str:
        """Map crypto symbol to CoinGecko ID."""
        gecko_map = {
            'BTCUSD': 'bitcoin',
            'ETHUSD': 'ethereum',
            'LTCUSD': 'litecoin',
            'BCHUSD': 'bitcoin-cash',
            'XRPUSD': 'ripple',
            'ADAUSD': 'cardano',
            'DOTUSD': 'polkadot',
            'LINKUSD': 'chainlink',
            'UNIUSD': 'uniswap',
            'SOLUSD': 'solana',
            'AVAXUSD': 'avalanche-2',
            'MATICUSD': 'polygon',
            'DOGEUSD': 'dogecoin',
            'BNBUSD': 'binancecoin',
        }
        
        return gecko_map.get(symbol, symbol.lower().replace('usd', ''))
    
    def _map_to_alpha_symbol(self, symbol: str) -> str:
        """Map symbol to Alpha Vantage format."""
        # Remove USD suffix for Alpha Vantage
        if symbol.endswith('USD'):
            return symbol[:-3]
        return symbol
    
    def _is_crypto(self, symbol: str) -> bool:
        """Check if symbol is cryptocurrency."""
        crypto_prefixes = ['BTC', 'ETH', 'LTC', 'BCH', 'XRP', 'ADA', 'DOT', 'LINK', 'UNI', 'SOL', 'AVAX', 'MATIC', 'DOGE', 'BNB']
        return any(symbol.startswith(prefix) for prefix in crypto_prefixes)
    
    def _is_gold(self, symbol: str) -> bool:
        """Check if symbol is gold."""
        return symbol.startswith('XAU')
    
    def _is_metal(self, symbol: str) -> bool:
        """Check if symbol is a metal."""
        return symbol.startswith(('XA', 'XP'))
    
    def _is_index(self, symbol: str) -> bool:
        """Check if symbol is an index."""
        index_prefixes = ['US', 'NAS', 'SPX', 'DAX', 'FTSE']
        return any(symbol.startswith(prefix) for prefix in index_prefixes)
    
    def _get_fallback_range(self, symbol: str) -> Tuple[float, float]:
        """Fallback to hardcoded ranges if no live data available."""
        if self._is_crypto(symbol):
            if symbol.startswith('BTC'):
                return (60000, 100000)
            elif symbol.startswith('ETH'):
                return (3000, 5000)
            elif symbol.startswith('BNB'):
                return (300, 800)
            else:
                return (0.01, 5000)
        elif self._is_gold(symbol):
            return (4000, 5000)  # Updated current range
        elif self._is_metal(symbol):
            if symbol.startswith('XAG'):
                return (20, 35)
            elif symbol.startswith('XPT'):
                return (800, 1200)
            else:
                return (10, 2000)
        elif self._is_index(symbol):
            if 'US30' in symbol or 'DOW' in symbol:
                return (30000, 40000)
            elif 'NAS' in symbol:
                return (14000, 20000)
            elif 'SPX' in symbol or 'SP500' in symbol:
                return (4000, 6000)
            else:
                return (1000, 50000)
        else:
            return (0.5, 2.0)  # Forex
