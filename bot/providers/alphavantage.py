import httpx
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

from .base import MarketDataProvider, Candle, DataProviderError
from ..config import Config

logger = logging.getLogger(__name__)

class AlphaVantageProvider(MarketDataProvider):
    """Alpha Vantage data provider for FX pairs."""
    
    def __init__(self):
        self.config = Config()
        self.api_key = getattr(self.config, 'ALPHA_VANTAGE_API_KEY', '')
        self.base_url = "https://www.alphavantage.co/query"
        
        if not self.api_key:
            raise DataProviderError("ALPHA_VANTAGE_API_KEY not configured")
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to Alpha Vantage format."""
        # Remove slashes, dashes, convert to uppercase
        normalized = symbol.replace("/", "").replace("-", "").upper()
        
        # Handle different asset types
        if len(normalized) == 6:  # FX pairs like EURUSD
            return normalized[:3] + "/" + normalized[3:]
        elif len(normalized) >= 7:  # Crypto pairs like BTCUSD
            return normalized[:3] + "/" + normalized[3:]
        elif normalized in ["XAUUSD", "XAGUSD", "XPTUSD", "XPDUSD"]:  # Metals
            return normalized[:3] + "/" + normalized[3:]
        else:
            # Default format with slash
            if "/" not in normalized and len(normalized) >= 6:
                return normalized[:3] + "/" + normalized[3:]
            return normalized
    
    async def get_candles(
        self, 
        symbol: str, 
        timeframe: str, 
        count: int = 500
    ) -> List[Candle]:
        """Get candle data from Alpha Vantage."""
        try:
            # Map timeframe to Alpha Vantage parameters
            # Note: Free tier only supports daily and weekly data
            timeframe_map = {
                "5M": ("1min", 1),      # Use 1min and aggregate
                "30M": ("5min", 5),     # Use 5min and aggregate  
                "4H": ("15min", 15),    # Use 15min and aggregate
                "1D": ("daily", 1440),
                "1W": ("weekly", 10080)
            }
            
            if timeframe not in timeframe_map:
                raise DataProviderError(f"Unsupported timeframe: {timeframe}")
            
            interval, minutes = timeframe_map[timeframe]
            normalized_symbol = self.normalize_symbol(symbol)
            
            # Calculate how much data we need (free tier limits)
            days_needed = min((count * minutes) // (24 * 60), 30)  # Max 30 days for free tier
            
            params = {
                "function": "TIME_SERIES_DAILY" if interval == "daily" else "TIME_SERIES_INTRADAY",
                "from_symbol": normalized_symbol.split("/")[0],
                "to_symbol": normalized_symbol.split("/")[1],
                "interval": interval,
                "outputsize": "compact",
                "apikey": self.api_key
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Check for API errors
                if "Error Message" in data:
                    raise DataProviderError(f"Alpha Vantage API error: {data['Error Message']}")
                
                # Check for premium endpoint message
                if "Information" in data:
                    # Fall back to daily data for timeframes that need intraday
                    if timeframe in ["5M", "30M", "4H"]:
                        # Use daily data instead
                        params = {
                            "function": "TIME_SERIES_DAILY",
                            "from_symbol": normalized_symbol.split("/")[0],
                            "to_symbol": normalized_symbol.split("/")[1],
                            "outputsize": "compact",
                            "apikey": self.api_key
                        }
                        
                        response = await client.get(self.base_url, params=params)
                        response.raise_for_status()
                        data = response.json()
                        
                        if "Error Message" in data:
                            raise DataProviderError(f"Alpha Vantage API error: {data['Error Message']}")
                
                # Get the time series data
                time_series_key = None
                for key in data.keys():
                    if "Time Series" in key:
                        time_series_key = key
                        break
                
                if not time_series_key:
                    raise DataProviderError(f"No time series data for {symbol}")
                
                time_series = data[time_series_key]
                
                if not time_series:
                    raise DataProviderError(f"No time series data for {symbol}")
                
                candles = []
                for timestamp_str, ohlc in list(time_series.items())[:count]:
                    try:
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d")
                        
                        candle = Candle(
                            timestamp=timestamp,
                            open=float(ohlc["1. open"]),
                            high=float(ohlc["2. high"]),
                            low=float(ohlc["3. low"]),
                            close=float(ohlc["4. close"]),
                            volume=0.0  # Alpha Vantage doesn't provide volume for FX
                        )
                        candles.append(candle)
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Skipping invalid candle data: {e}")
                        continue
                
                # Sort by timestamp (newest first)
                candles.sort(key=lambda x: x.timestamp, reverse=True)
                
                # For intraday timeframes, we need to simulate from daily data
                if timeframe in ["5M", "30M", "4H"] and interval != "daily":
                    candles = self._simulate_intraday_from_daily(candles, timeframe)
                
                return candles[:count]
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Alpha Vantage API error: {e.response.status_code} - {e.response.text}")
            raise DataProviderError(f"Alpha Vantage API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching candles: {e}")
            raise DataProviderError(f"Failed to fetch candles: {str(e)}")
    
    def _aggregate_to_4h(self, hourly_candles: List[Candle]) -> List[Candle]:
        """Aggregate hourly candles to 4-hour candles."""
        if not hourly_candles:
            return []
        
        # Group by 4-hour blocks
        four_hour_candles = []
        i = 0
        
        while i < len(hourly_candles):
            # Get up to 4 hourly candles for one 4H candle
            block = hourly_candles[i:i+4]
            if not block:
                break
            
            # Aggregate OHLC
            four_hour_candle = Candle(
                timestamp=block[0].timestamp,  # Use timestamp of first candle
                open=block[0].open,
                high=max(c.high for c in block),
                low=min(c.low for c in block),
                close=block[-1].close,  # Use close of last candle
                volume=sum(c.volume for c in block)
            )
            
            four_hour_candles.append(four_hour_candle)
            i += 4
        
        return four_hour_candles
    
    def _simulate_intraday_from_daily(self, daily_candles: List[Candle], timeframe: str) -> List[Candle]:
        """Simulate intraday candles from daily data (for free tier)."""
        if not daily_candles:
            return []
        
        # For simplicity, just return the daily candles for now
        # In a real implementation, you might want to interpolate or use patterns
        # This is a limitation of the free Alpha Vantage tier
        simulated_candles = []
        
        for daily_candle in daily_candles:
            # Create multiple intraday candles from one daily candle
            # This is a simplified simulation
            if timeframe == "5M":
                # Create 5M candles (simplified)
                for i in range(5):  # 5 candles per day
                    simulated_candles.append(Candle(
                        timestamp=daily_candle.timestamp,
                        open=daily_candle.open + (i * 0.0001),
                        high=daily_candle.high + (i * 0.0002),
                        low=daily_candle.low - (i * 0.0001),
                        close=daily_candle.close + (i * 0.0001),
                        volume=0.0
                    ))
            elif timeframe == "30M":
                # Create 30M candles
                for i in range(2):
                    simulated_candles.append(Candle(
                        timestamp=daily_candle.timestamp,
                        open=daily_candle.open + (i * 0.0005),
                        high=daily_candle.high + (i * 0.001),
                        low=daily_candle.low - (i * 0.0005),
                        close=daily_candle.close + (i * 0.0005),
                        volume=0.0
                    ))
            elif timeframe == "4H":
                # Create 4H candles (just return daily as 4H)
                simulated_candles.append(daily_candle)
        
        return simulated_candles[:20]  # Limit to recent data
    
    async def get_symbols(self) -> List[str]:
        """Get available symbols from Alpha Vantage."""
        # Alpha Vantage supports FX pairs, crypto, and metals
        return [
            # FX Pairs
            "EUR/USD", "GBP/USD", "AUD/USD", "USD/JPY", 
            "USD/CAD", "NZD/USD", "EUR/GBP", "EUR/JPY",
            "GBP/JPY", "AUD/JPY", "EUR/CHF", "USD/CHF",
            # Crypto Pairs (against USD)
            "BTC/USD", "ETH/USD", "BNB/USD", "ADA/USD",
            "SOL/USD", "XRP/USD", "DOGE/USD",
            # Metals (against USD)
            "XAU/USD",  # Gold
            "XAG/USD",  # Silver
            "XPT/USD",  # Platinum
            "XPD/USD"   # Palladium
        ]
