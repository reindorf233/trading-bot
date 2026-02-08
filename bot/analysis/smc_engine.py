"""
Smart Money Concepts (SMC) Analysis Engine
CurrencyBot v2 - Advanced SMC forex analysis with structured 4-step strategy
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np

from ..providers.base import MarketDataProvider, Candle
from ..config import Config


class SMCAnalysis:
    """SMC analysis result structure."""
    
    def __init__(self):
        self.symbol: str = ""
        self.timestamp: datetime = datetime.utcnow()
        self.data_status: str = "Unknown"
        
        # Step 1: Direction (Market Bias)
        self.direction: str = "Neutral"
        self.bias_4h: str = "Neutral"
        self.trend_4h: str = "None"
        self.event_4h: str = "None"
        
        # Step 2: POI (Point of Interest)
        self.poi_type: str = "None"
        self.poi_zone: str = "N/A"
        self.poi_timeframe: str = "30M"
        
        # Step 3: Liquidity Sweep
        self.liquidity_sweep: str = "No"
        self.sweep_details: str = "No sweep detected"
        
        # Step 4: Confirmation
        self.confirmation_pattern: str = "None"
        self.confirmation_timeframe: str = "5M"
        
        # Signal Generation
        self.signal: str = "NO TRADE"
        self.confidence: int = 0
        self.entry_zone: str = "N/A"
        self.invalidation_level: str = "N/A"
        self.target1: str = "N/A"
        self.target2: str = "N/A"
        
        # AI Analysis
        self.ai_reasons: str = "Analysis pending"
        self.missing_conditions: List[str] = []
        self.risk_notes: str = "No risk assessment"


class SMCEngine:
    """Smart Money Concepts analysis engine."""
    
    def __init__(self, provider: MarketDataProvider, config: Config):
        self.provider = provider
        self.config = config
    
    def _detect_bos_choch(self, candles: List[Candle]) -> Tuple[str, str, str]:
        """Detect Break of Structure (BOS) or Market Structure Shift (MSS/CHoCH)."""
        if len(candles) < 20:
            return "Neutral", "None", "Insufficient data"
        
        # Get recent highs and lows
        highs = [c.high for c in candles[:20]]
        lows = [c.low for c in candles[:20]]
        
        # Find swing highs and lows
        swing_highs = []
        swing_lows = []
        
        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                swing_highs.append(highs[i])
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                swing_lows.append(lows[i])
        
        if not swing_highs or not swing_lows:
            return "Neutral", "None", "No clear structure"
        
        # Determine trend direction
        recent_high = max(swing_highs[-3:]) if len(swing_highs) >= 3 else max(swing_highs)
        recent_low = min(swing_lows[-3:]) if len(swing_lows) >= 3 else min(swing_lows)
        
        current_price = candles[0].close
        
        # Check for BOS (continuation)
        if current_price > recent_high:
            return "Bullish", "BOS", f"Price broke above recent high at {recent_high:.5f}"
        elif current_price < recent_low:
            return "Bearish", "BOS", f"Price broke below recent low at {recent_low:.5f}"
        
        # Check for MSS/CHoCH (reversal)
        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            if swing_highs[-1] < swing_highs[-2] and swing_lows[-1] > swing_lows[-2]:
                return "Bearish", "MSS", "Lower highs and higher lows detected"
            elif swing_lows[-1] < swing_lows[-2] and swing_highs[-1] > swing_highs[-2]:
                return "Bullish", "MSS", "Higher lows and lower highs detected"
        
        return "Neutral", "None", "No clear bias established"
    
    def _detect_fvg(self, candles: List[Candle]) -> Optional[Dict]:
        """Detect Fair Value Gaps (FVG)."""
        if len(candles) < 3:
            return None
        
        fvgs = []
        for i in range(len(candles) - 2):
            current = candles[i]
            next_candle = candles[i + 1]
            next_next = candles[i + 2]
            
            # Bullish FVG (gap up)
            if next_candle.low > current.high:
                fvg_size = next_candle.low - current.high
                fvgs.append({
                    'type': 'Bullish FVG',
                    'top': current.high,
                    'bottom': next_candle.low,
                    'size': fvg_size,
                    'time': next_candle.timestamp
                })
            
            # Bearish FVG (gap down)
            elif next_candle.high < current.low:
                fvg_size = current.low - next_candle.high
                fvgs.append({
                    'type': 'Bearish FVG',
                    'top': next_candle.high,
                    'bottom': current.low,
                    'size': fvg_size,
                    'time': next_candle.timestamp
                })
        
        if fvgs:
            # Return most recent significant FVG
            significant_fvgs = [fvg for fvg in fvgs if abs(fvg['size']) > 0.0001]
            if significant_fvgs:
                return max(significant_fvgs, key=lambda x: x['time'])
        
        return None
    
    def _detect_order_blocks(self, candles: List[Candle]) -> Optional[Dict]:
        """Detect Order Blocks (OB)."""
        if len(candles) < 5:
            return None
        
        order_blocks = []
        
        for i in range(len(candles) - 4):
            # Look for strong momentum candles
            current = candles[i]
            next_candle = candles[i + 1]
            
            # Bullish Order Block (strong down candle followed by strong up move)
            if (current.close < current.open and  # Bearish candle
                abs(current.close - current.open) > 0.001 and  # Strong move
                next_candle.close > next_candle.open):  # Reversal
                
                ob = {
                    'type': 'Bullish OB',
                    'high': current.high,
                    'low': current.low,
                    'time': current.timestamp
                }
                order_blocks.append(ob)
            
            # Bearish Order Block (strong up candle followed by strong down move)
            elif (current.close > current.open and  # Bullish candle
                  abs(current.close - current.open) > 0.001 and  # Strong move
                  next_candle.close < next_candle.open):  # Reversal
                
                ob = {
                    'type': 'Bearish OB',
                    'high': current.high,
                    'low': current.low,
                    'time': current.timestamp
                }
                order_blocks.append(ob)
        
        if order_blocks:
            # Return most recent order block
            return max(order_blocks, key=lambda x: x['time'])
        
        return None
    
    def _detect_liquidity_sweep(self, candles: List[Candle], poi: Dict) -> Tuple[str, str]:
        """Detect liquidity sweeps into POI."""
        if not poi or len(candles) < 10:
            return "No", "No POI to check for sweep"
        
        current_price = candles[0].close
        recent_highs = sorted([c.high for c in candles[:10]], reverse=True)[:3]
        recent_lows = sorted([c.low for c in candles[:10]])[:3]
        
        sweep_details = ""
        
        # Check for sweep above recent highs
        if poi['type'] in ['Bullish OB', 'Bullish FVG']:
            equal_highs = [h for h in recent_highs if abs(h - recent_highs[0]) < 0.0001]
            if equal_highs:
                # Check if price swept above then returned
                for candle in candles[:5]:
                    if candle.high > recent_highs[0] and candle.close < recent_highs[0]:
                        sweep_details = f"Yes – wicked above recent high at {recent_highs[0]:.5f} into {poi['type']}"
                        return "Yes", sweep_details
        
        # Check for sweep below recent lows
        elif poi['type'] in ['Bearish OB', 'Bearish FVG']:
            equal_lows = [l for l in recent_lows if abs(l - recent_lows[0]) < 0.0001]
            if equal_lows:
                # Check if price swept below then returned
                for candle in candles[:5]:
                    if candle.low < recent_lows[0] and candle.close > recent_lows[0]:
                        sweep_details = f"Yes – wicked below recent low at {recent_lows[0]:.5f} into {poi['type']}"
                        return "Yes", sweep_details
        
        return "No", "No clear liquidity sweep detected"
    
    def _detect_confirmation_patterns(self, candles: List[Candle], direction: str) -> Tuple[str, str]:
        """Detect confirmation patterns on lower timeframe."""
        if len(candles) < 3:
            return "None", "Insufficient data"
        
        current = candles[0]
        previous = candles[1]
        
        # Bullish confirmation patterns
        if direction == "Bullish":
            # Bullish Engulfing
            if (previous.close < previous.open and  # Previous bearish
                current.close > current.open and  # Current bullish
                current.close > previous.open and  # Engulfs previous
                current.open < previous.close):
                return "Bullish Engulfing", "Strong bullish reversal pattern"
            
            # Morning Star
            if (len(candles) >= 3 and
                previous.close < previous.open and  # Bearish middle candle
                candles[2].close > candles[2].open):  # Bullish third candle
                return "Morning Star", "Three-candle bullish reversal"
            
            # Strong Bullish Bar
            if (current.close > current.open and
                abs(current.close - current.open) > 0.001):
                return "Strong Bullish Bar", "Strong momentum candle"
        
        # Bearish confirmation patterns
        elif direction == "Bearish":
            # Bearish Engulfing
            if (previous.close > previous.open and  # Previous bullish
                current.close < current.open and  # Current bearish
                current.close < previous.open and  # Engulfs previous
                current.open > previous.close):
                return "Bearish Engulfing", "Strong bearish reversal pattern"
            
            # Evening Star
            if (len(candles) >= 3 and
                previous.close > previous.open and  # Bullish middle candle
                candles[2].close < candles[2].open):  # Bearish third candle
                return "Evening Star", "Three-candle bearish reversal"
            
            # Strong Bearish Bar
            if (current.close < current.open and
                abs(current.close - current.open) > 0.001):
                return "Strong Bearish Bar", "Strong momentum candle"
        
        return "None", "No clear confirmation pattern"
    
    def _calculate_confidence(self, analysis: SMCAnalysis) -> int:
        """Calculate confidence score based on confluences."""
        confidence = 0
        
        # Direction confidence (30% max)
        if analysis.direction != "Neutral":
            confidence += 30
            if analysis.event_4h in ["BOS", "MSS"]:
                confidence += 10
        
        # POI confidence (30% max)
        if analysis.poi_type != "None":
            confidence += 30
            if analysis.poi_type in ["Order Block", "FVG"]:
                confidence += 10
        
        # Liquidity sweep confidence (20% max)
        if analysis.liquidity_sweep == "Yes":
            confidence += 20
        
        # Confirmation confidence (20% max)
        if analysis.confirmation_pattern != "None":
            confidence += 20
            if "Engulfing" in analysis.confirmation_pattern or "Star" in analysis.confirmation_pattern:
                confidence += 10
        
        return min(confidence, 100)
    
    def _generate_signal(self, analysis: SMCAnalysis) -> Tuple[str, str, str, str, str]:
        """Generate trading signal based on analysis."""
        confidence = self._calculate_confidence(analysis)
        
        if confidence < 70:
            return "NO TRADE", "N/A", "N/A", "N/A", "Insufficient confluence for high-confidence setup"
        
        if analysis.direction == "Bullish":
            if analysis.poi_type in ["Bullish OB", "Bullish FVG"]:
                entry = analysis.poi_zone
                sl = analysis.poi_zone.split("–")[0].strip() if "–" in analysis.poi_zone else analysis.poi_zone
                tp = f"{float(sl) + 0.0020:.5f}"
                return "BUY", entry, sl, tp, f"Bullish setup with {confidence}% confidence"
        
        elif analysis.direction == "Bearish":
            if analysis.poi_type in ["Bearish OB", "Bearish FVG"]:
                entry = analysis.poi_zone
                sl = analysis.poi_zone.split("–")[1].strip() if "–" in analysis.poi_zone else analysis.poi_zone
                tp = f"{float(sl) - 0.0020:.5f}"
                return "SELL", entry, sl, tp, f"Bearish setup with {confidence}% confidence"
        
        return "NO TRADE", "N/A", "N/A", "N/A", "Waiting for better confluence"
    
    async def analyze_symbol(self, symbol: str) -> SMCAnalysis:
        """Perform complete SMC analysis on a symbol."""
        analysis = SMCAnalysis()
        analysis.symbol = symbol
        
        try:
            # Get data for all timeframes
            candles_4h = await self.provider.get_candles(symbol, "4H", 100)
            candles_30m = await self.provider.get_candles(symbol, "30M", 200)
            candles_5m = await self.provider.get_candles(symbol, "5M", 100)
            
            analysis.data_status = "Deriv WebSocket success"
            
            # Step 1: Direction (Market Bias) - 4H
            analysis.direction, analysis.trend_4h, analysis.event_4h = self._detect_bos_choch(candles_4h)
            analysis.bias_4h = analysis.direction
            
            # Step 2: POI (Point of Interest) - 30M
            poi = None
            
            # Try FVG first
            fvg = self._detect_fvg(candles_30m)
            if fvg:
                poi = fvg
                analysis.poi_type = fvg['type']
                analysis.poi_zone = f"{fvg['bottom']:.5f}–{fvg['top']:.5f}"
            
            # Try Order Block if no FVG
            if not poi:
                ob = self._detect_order_blocks(candles_30m)
                if ob:
                    poi = ob
                    analysis.poi_type = ob['type']
                    analysis.poi_zone = f"{ob['low']:.5f}–{ob['high']:.5f}"
            
            # Step 3: Liquidity Sweep - 30M
            if poi:
                analysis.liquidity_sweep, analysis.sweep_details = self._detect_liquidity_sweep(candles_30m, poi)
            
            # Step 4: Confirmation - 5M
            if analysis.direction != "Neutral":
                analysis.confirmation_pattern, _ = self._detect_confirmation_patterns(candles_5m, analysis.direction)
            
            # Calculate confidence and generate signal
            analysis.confidence = self._calculate_confidence(analysis)
            analysis.signal, analysis.entry_zone, analysis.invalidation_level, analysis.target1, analysis.ai_reasons = self._generate_signal(analysis)
            
            # Generate risk notes
            if analysis.signal != "NO TRADE":
                analysis.risk_notes = f"Manage risk below {analysis.invalidation_level}, target at {analysis.target1}"
            else:
                analysis.risk_notes = "Wait for better setup with higher confluence"
            
        except Exception as e:
            # Fallback analysis
            analysis.data_status = "Fallback: Free historical SMC analysis"
            analysis.direction = "Neutral"
            analysis.bias_4h = "Neutral"
            analysis.trend_4h = "None"
            analysis.event_4h = "None"
            analysis.poi_type = "None"
            analysis.poi_zone = "N/A"
            analysis.liquidity_sweep = "No"
            analysis.confirmation_pattern = "None"
            analysis.signal = "NO TRADE"
            analysis.confidence = 0
            analysis.ai_reasons = f"Analysis based on recent historical data – verify live on Deriv/TradingView. Error: {str(e)}"
            analysis.risk_notes = "Analysis failed - check data connection"
        
        return analysis
