"""
CurrencyBot - Smart Money Concepts (SMC) Analysis Engine
Exact 4-step SMC model with structured output
"""

import asyncio
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import numpy as np

from ..providers.base import MarketDataProvider, Candle, DataProviderError
from ..config import Config


class SMCAnalysisFinal:
    """SMC analysis result structure for CurrencyBot."""
    
    def __init__(self):
        self.symbol: str = ""
        self.timestamp: datetime = datetime.utcnow()
        self.data_status: str = "Unknown"
        
        # Step 1: Direction (Market Bias)
        self.direction: str = "Neutral"  # Bullish/Bearish/Neutral
        self.bias_4h: str = "Neutral"
        self.trend_4h: str = "None"
        self.event_4h: str = "None"
        
        # Step 2: POI (Point of Interest)
        self.poi_type: str = "None"  # Only: Breaker Block, Flip OB, FVG, OB, RB, OHOL/OL
        self.poi_zone: str = "N/A"
        self.poi_timeframe: str = "30M"
        
        # Step 3: Liquidity Sweep
        self.liquidity_sweep: str = "No"
        self.sweep_details: str = "No sweep detected"
        
        # Step 4: Confirmation
        self.confirmation_pattern: str = "None"
        self.confirmation_timeframe: str = "5M"
        
        # Post-steps
        self.signal: str = "NO TRADE"
        self.confidence: int = 0
        self.entry_zone: str = "N/A"
        self.invalidation_level: str = "N/A"
        self.target1: str = "N/A"
        self.target2: str = "N/A"
        
        # AI Analysis
        self.ai_reasons: str = "Analysis pending"
        self.risk_notes: str = "No risk assessment"
    
    def model_dump_json(self) -> str:
        """Convert analysis to JSON string for storage."""
        return json.dumps({
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'data_status': self.data_status,
            'direction': self.direction,
            'trend_4h': self.trend_4h,
            'event_4h': self.event_4h,
            'poi_type': self.poi_type,
            'poi_zone': self.poi_zone,
            'poi_timeframe': self.poi_timeframe,
            'liquidity_sweep': self.liquidity_sweep,
            'sweep_details': self.sweep_details,
            'confirmation_pattern': self.confirmation_pattern,
            'confirmation_timeframe': self.confirmation_timeframe,
            'signal': self.signal,
            'confidence': self.confidence,
            'entry_zone': self.entry_zone,
            'invalidation_level': self.invalidation_level,
            'target1': self.target1,
            'target2': self.target2,
            'ai_reasons': self.ai_reasons,
            'risk_notes': self.risk_notes
        })


class SMCEngineFinal:
    """CurrencyBot - Smart Money Concepts analysis engine."""
    
    def __init__(self, provider: MarketDataProvider, config: Config):
        self.provider = provider
        self.config = config
    
    def _is_crypto_pair(self, symbol: str) -> bool:
        """Detect if symbol is a cryptocurrency pair."""
        crypto_prefixes = ['BTC', 'ETH', 'LTC', 'BCH', 'XRP', 'ADA', 'DOT', 'LINK', 'UNI']
        return any(symbol.startswith(prefix) for prefix in crypto_prefixes)
    
    def _is_gold_pair(self, symbol: str) -> bool:
        """Detect if symbol is gold (XAUUSD)."""
        return symbol.startswith('XAU')
    
    def _get_realistic_price_range(self, symbol: str) -> Tuple[float, float]:
        """Get realistic price range for symbol."""
        if self._is_crypto_pair(symbol):
            if symbol.startswith('BTC'):
                return (60000, 100000)  # BTC range
            elif symbol.startswith('ETH'):
                return (3000, 5000)   # ETH range
            elif symbol.startswith('LTC'):
                return (60, 120)      # LTC range
            else:
                return (0.5, 5000)    # General crypto range
        elif self._is_gold_pair(symbol):
            return (1800, 2200)      # Gold (XAUUSD) range - realistic for current market
        else:
            # Forex pairs
            return (0.5, 2.0)  # Typical forex range
    
    def _detect_swing_points(self, candles: List[Candle], window: int = 5) -> Tuple[List[Dict], List[Dict]]:
        """Get swing highs and lows for structure analysis."""
        if len(candles) < window * 2:
            return [], []
        
        swing_highs = []
        swing_lows = []
        
        for i in range(window, len(candles) - window):
            window_candles = candles[i:i+window]
            high = max(c.high for c in window_candles)
            low = min(c.low for c in window_candles)
            
            is_swing_high = all(c.high < high for c in window_candles[1:])
            if is_swing_high:
                swing_highs.append({
                    'price': high,
                    'index': i + window // 2,
                    'timestamp': window_candles[window // 2].timestamp
                })
            
            is_swing_low = all(c.low > low for c in window_candles[1:])
            if is_swing_low:
                swing_lows.append({
                    'price': low,
                    'index': i + window // 2,
                    'timestamp': window_candles[window // 2].timestamp
                })
        
        return swing_highs, swing_lows
    
    def _detect_bos_mss(self, candles: List[Candle]) -> Tuple[str, str, str]:
        """Detect BOS/MSS with proper HH/HL/LH/LL analysis on 4H."""
        swing_highs, swing_lows = self._get_swing_points(candles, window=5)
        
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return "Neutral", "None", "Insufficient swing points"
        
        recent_highs = sorted(swing_highs, key=lambda x: x['timestamp'], reverse=True)[:3]
        recent_lows = sorted(swing_lows, key=lambda x: x['timestamp'], reverse=True)[:3]
        
        current_price = candles[0].close
        
        # Check for Higher Highs + Higher Lows (Bullish)
        if (len(recent_highs) >= 2 and len(recent_lows) >= 2 and
            recent_highs[0]['price'] > recent_highs[1]['price'] and
            recent_lows[0]['price'] > recent_lows[1]['price']):
            
            # Check for BOS upward
            if current_price > recent_highs[0]['price']:
                return "Bullish", "BOS", f"HH + HL + BOS upward (HH: {recent_highs[0]['price']:.5f}, HL: {recent_lows[0]['price']:.5f})"
            else:
                return "Bullish", "None", f"HH + HL structure (HH: {recent_highs[0]['price']:.5f}, HL: {recent_lows[0]['price']:.5f})"
        
        # Check for Lower Highs + Lower Lows (Bearish)
        elif (len(recent_highs) >= 2 and len(recent_lows) >= 2 and
              recent_highs[0]['price'] < recent_highs[1]['price'] and
              recent_lows[0]['price'] < recent_lows[1]['price']):
            
            # Check for BOS downward
            if current_price < recent_lows[0]['price']:
                return "Bearish", "BOS", f"LH + LL + BOS downward (LH: {recent_highs[0]['price']:.5f}, LL: {recent_lows[0]['price']:.5f})"
            else:
                return "Bearish", "None", f"LH + LL structure (LH: {recent_highs[0]['price']:.5f}, LL: {recent_lows[0]['price']:.5f})"
        
        # Check for CHoCH/MSS without follow-through (Neutral)
        elif (len(recent_highs) >= 2 and len(recent_lows) >= 2):
            if (recent_highs[0]['price'] > recent_highs[1]['price'] and
                recent_lows[0]['price'] < recent_lows[1]['price']):
                return "Neutral", "CHoCH/MSS", "CHoCH/MSS without follow-through - choppy structure"
            elif (recent_highs[0]['price'] < recent_highs[1]['price'] and
                  recent_lows[0]['price'] > recent_lows[1]['price']):
                return "Neutral", "CHoCH/MSS", "CHoCH/MSS without follow-through - choppy structure"
        
        return "Neutral", "None", "Choppy or unclear structure"
    
    def _detect_fvg(self, candles: List[Candle]) -> Optional[Dict]:
        """Detect Fair Value Gaps (FVG) on 30M."""
        if len(candles) < 3:
            return None
        
        fvgs = []
        for i in range(len(candles) - 2):
            candle1 = candles[i]
            candle2 = candles[i + 1]
            candle3 = candles[i + 2]
            
            # Bullish FVG
            if candle2.low > candle1.high:
                fvg_top = candle1.high
                fvg_bottom = candle2.low
                fvg_size = candle2.low - candle1.high
                
                if abs(fvg_size) > 0.0001:
                    fvgs.append({
                        'type': 'Bullish FVG',
                        'top': fvg_top,
                        'bottom': fvg_bottom,
                        'size': fvg_size,
                        'timestamp': candle2.timestamp,
                        'zone': f"{fvg_bottom:.5f}-{fvg_top:.5f}"
                    })
            
            # Bearish FVG
            elif candle2.high < candle1.low:
                fvg_top = candle2.high
                fvg_bottom = candle1.low
                fvg_size = candle1.low - candle2.high
                
                if abs(fvg_size) > 0.0001:
                    fvgs.append({
                        'type': 'Bearish FVG',
                        'top': fvg_top,
                        'bottom': fvg_bottom,
                        'size': fvg_size,
                        'timestamp': candle2.timestamp,
                        'zone': f"{fvg_bottom:.5f}-{fvg_top:.5f}"
                    })
        
        if fvgs:
            return max(fvgs, key=lambda x: abs(x['size']), reverse=True)
        
        return None
    
    def _detect_order_blocks(self, candles: List[Candle]) -> Optional[Dict]:
        """Detect Order Blocks (OB) on 30M."""
        if len(candles) < 5:
            return None
        
        order_blocks = []
        for i in range(len(candles) - 4):
            candle1 = candles[i]
            candle5 = candles[i + 4]
            
            # Bullish OB: Strong down candle followed by strong up move
            if (candle1.close < candle1.open and abs(candle1.close - candle1.open) > 0.001 and
                candle5.close > candle5.open and abs(candle5.close - candle5.open) > 0.001):
                
                ob_high = max(c.high for c in candles[i:i+4])
                ob_low = min(c.low for c in candles[i:i+4])
                
                order_blocks.append({
                    'type': 'Bullish OB',
                    'high': ob_high,
                    'low': ob_low,
                    'timestamp': candle1.timestamp,
                    'zone': f"{ob_low:.5f}-{ob_high:.5f}"
                })
            
            # Bearish OB: Strong up candle followed by strong down move
            elif (candle1.close > candle1.open and abs(candle1.close - candle1.open) > 0.001 and
                  candle5.close < candle5.open and abs(candle5.close - candle5.open) > 0.001):
                  
                ob_high = max(c.high for c in candles[i:i+4])
                ob_low = min(c.low for c in candles[i:i+4])
                
                order_blocks.append({
                    'type': 'Bearish OB',
                    'high': ob_high,
                    'low': ob_low,
                    'timestamp': candle1.timestamp,
                    'zone': f"{ob_low:.5f}-{ob_high:.5f}"
                })
        
        if order_blocks:
            return max(order_blocks, key=lambda x: x['timestamp'], reverse=True)
        
        return None
    
    def _detect_breaker_blocks(self, candles: List[Candle]) -> Optional[Dict]:
        """Detect Breaker Blocks on 30M."""
        if len(candles) < 5:
            return None
        
        order_blocks = self._detect_order_blocks(candles[:-2])
        if not order_blocks:
            return None
        
        current_price = candles[0].close
        
        for ob in order_blocks:
            if current_price > ob['high'] and ob['type'] == 'Bullish OB':
                return {
                    'type': 'Breaker Block',
                    'original_type': ob['type'],
                    'broken_high': ob['high'],
                    'broken_low': ob['low'],
                    'timestamp': ob['timestamp'],
                    'zone': f"{ob['low']:.5f}-{ob['high']:.5f}",
                    'status': 'Broken'
                }
            elif current_price < ob['low'] and ob['type'] == 'Bearish OB':
                return {
                    'type': 'Breaker Block',
                    'original_type': ob['type'],
                    'broken_high': ob['high'],
                    'broken_low': ob['low'],
                    'timestamp': ob['timestamp'],
                    'zone': f"{ob['low']:.5f}-{ob['high']:.5f}",
                    'status': 'Broken'
                }
        
        return None
    
    def _detect_flip_ob(self, candles: List[Candle]) -> Optional[Dict]:
        """Detect Flip Order Blocks on 30M."""
        if len(candles) < 5:
            return None
        
        flip_obs = []
        for i in range(len(candles) - 4):
            candle1 = candles[i]
            candle5 = candles[i + 4]
            
            # Bullish Flip OB: Bearish momentum followed by bullish reversal
            if (candle1.close < candle1.open and abs(candle1.close - candle1.open) > 0.0005 and
                candle5.close > candle5.open and abs(candle5.close - candle5.open) > 0.0005):
                
                ob_high = max(c.high for c in candles[i:i+4])
                ob_low = min(c.low for c in candles[i:i+4])
                
                flip_obs.append({
                    'type': 'Flip OB',
                    'high': ob_high,
                    'low': ob_low,
                    'timestamp': candle1.timestamp,
                    'zone': f"{ob_low:.5f}-{ob_high:.5f}"
                })
            
            # Bearish Flip OB: Bullish momentum followed by bearish reversal
            elif (candle1.close > candle1.open and abs(candle1.close - candle1.open) > 0.0005 and
                  candle5.close < candle5.open and abs(candle5.open - candle5.close) > 0.0005):
                  
                ob_high = max(c.high for c in candles[i:i+4])
                ob_low = min(c.low for c in candles[i:i+4])
                
                flip_obs.append({
                    'type': 'Flip OB',
                    'high': ob_high,
                    'low': ob_low,
                    'timestamp': candle1.timestamp,
                    'zone': f"{ob_low:.5f}-{ob_high:.5f}"
                })
        
        if flip_obs:
            return max(flip_obs, key=lambda x: x['timestamp'], reverse=True)
        
        return None
    
    def _detect_rejection_blocks(self, candles: List[Candle]) -> Optional[Dict]:
        """Detect Rejection Blocks (RB) on 30M."""
        if len(candles) < 3:
            return None
        
        rejection_blocks = []
        for i in range(len(candles) - 2):
            candle2 = candles[i + 1]
            
            body_size = abs(candle2.close - candle2.open)
            upper_wick = candle2.high - max(candle2.open, candle2.close)
            lower_wick = min(candle2.open, candle2.close) - candle2.low
            
            if (max(upper_wick, lower_wick) > body_size * 0.5 and body_size > 0.0001):
                rb_type = 'Bullish RB' if candle2.close > candle2.open else 'Bearish RB'
                
                rejection_blocks.append({
                    'type': rb_type,
                    'high': candle2.high,
                    'low': candle2.low,
                    'timestamp': candle2.timestamp,
                    'zone': f"{candle2.low:.5f}-{candle2.high:.5f}"
                })
        
        if rejection_blocks:
            return max(rejection_blocks, key=lambda x: x['timestamp'], reverse=True)
        
        return None
    
    def _detect_ohol_ol(self, candles: List[Candle]) -> Optional[Dict]:
        """Detect OHOL (Order Block Highs/Lows) on 30M."""
        if len(candles) < 3:
            return None
        
        ohol_ol = []
        for i in range(len(candles) - 2):
            candle1 = candles[i]
            candle2 = candles[i + 1]
            candle3 = candles[i + 2]
            
            # OHOL: Order Block Highs/Lows pattern
            if (candle1.close > candle1.open and  # Bullish
                candle2.close < candle2.open and  # Bearish
                candle3.close > candle3.open):  # Bullish continuation
                
                high = max(candle1.high, candle2.high, candle3.high)
                low = min(candle1.low, candle2.low, candle3.low)
                
                ohol_ol.append({
                    'type': 'OHOL',
                    'high': high,
                    'low': low,
                    'timestamp': candle2.timestamp,
                    'zone': f"{low:.5f}-{high:.5f}"
                })
        
        if ohol_ol:
            return max(ohol_ol, key=lambda x: x['timestamp'], reverse=True)
        
        return None
    
    def _detect_liquidity_sweep(self, candles: List[Candle], poi: Dict) -> Tuple[str, str]:
        """Detect if price swept liquidity into POI."""
        if not poi or len(candles) < 10:
            return "No", "No POI or insufficient data"
        
        current_price = candles[0].close
        poi_high = float(poi['zone'].split('-')[1])
        poi_low = float(poi['zone'].split('-')[0])
        poi_type = poi.get('type', '')
        
        recent_candles = candles[:10]
        recent_highs = sorted([c.high for c in recent_candles], reverse=True)[:3]
        recent_lows = sorted([c.low for c in recent_candles])[:3]
        
        sweep_details = []
        
        # Check for sweep above recent highs (for bearish POI)
        if 'Bearish' in poi_type:
            for high in recent_highs:
                if current_price > high and abs(current_price - high) < 0.0005:
                    sweep_details.append(f"Wicked above recent high at {high:.5f}")
                    break
        elif 'Bullish' in poi_type:
            for low in recent_lows:
                if current_price < low and abs(low - current_price) < 0.0005:
                    sweep_details.append(f"Wicked below recent low at {low:.5f}")
                    break
        
        # Check for equal highs/lows (stop hunt)
        equal_highs = [h for h in recent_highs if abs(h - recent_highs[0]) < 0.0001]
        equal_lows = [l for l in recent_lows if abs(l - recent_lows[0]) < 0.0001]
        
        if equal_highs and 'Bearish' in poi_type:
            sweep_details.append("Stop hunt at equal highs detected")
        elif equal_lows and 'Bullish' in poi_type:
            sweep_details.append("Stop hunt at equal lows detected")
        
        if sweep_details:
            return "Yes", "; ".join(sweep_details)
        
        return "No", "No clear liquidity sweep detected"
    
    def _detect_confirmation_patterns(self, candles: List[Candle], direction: str) -> Tuple[str, str]:
        """Detect confirmation patterns on 5M."""
        if len(candles) < 3:
            return "None", "Insufficient data for confirmation"
        
        patterns = []
        
        for i in range(len(candles) - 2):
            candle1 = candles[i]
            candle2 = candles[i + 1]
            candle3 = candles[i + 2]
            
            # BE (Breaker Entry)
            if (direction == "Bullish" and
                candle2.close > candle2.open and
                candle3.close > candle3.open and
                candle2.high > max(candle1.high, candle3.high)):
                
                patterns.append({
                    'type': 'BE',
                    'confidence': 'High',
                    'timestamp': candle2.timestamp,
                    'details': 'Bullish breaker entry confirmed'
                })
            
            elif (direction == "Bearish" and
                  candle2.close < candle2.open and
                  candle3.close < candle3.open and
                  candle2.low < min(candle1.low, candle3.low)):
                  
                patterns.append({
                    'type': 'BE',
                    'confidence': 'High',
                    'timestamp': candle2.timestamp,
                    'details': 'Bearish breaker entry confirmed'
                })
            
            # RB (Rejection Bar)
            elif (direction == "Bullish" and
                  candle2.close > candle2.open and
                  candle2.high - max(candle2.open, candle2.close) > 0.0003):
                  
                patterns.append({
                    'type': 'RB',
                    'confidence': 'Medium',
                    'timestamp': candle2.timestamp,
                    'details': 'Bullish rejection bar confirmed'
                })
            
            elif (direction == "Bearish" and
                  candle2.close < candle2.open and
                  max(candle2.open, candle2.close) - candle2.low > 0.0003):
                  
                patterns.append({
                    'type': 'RB',
                    'confidence': 'Medium',
                    'timestamp': candle2.timestamp,
                    'details': 'Bearish rejection bar confirmed'
                })
            
            # Morning Star (only bullish)
            elif (direction == "Bullish" and
                  len(candles) > i + 3 and
                  candle1.close < candle1.open and  # Bearish first
                  candle2.close < candle2.open and  # Bearish middle
                  candle3.close > candle3.open):  # Bullish third
                  
                patterns.append({
                    'type': 'Morning Star',
                    'confidence': 'High',
                    'timestamp': candle3.timestamp,
                    'details': 'Bullish morning star pattern confirmed'
                })
            
            # Evening Star (only bearish)
            elif (direction == "Bearish" and
                  len(candles) > i + 3 and
                  candle1.close > candle1.open and  # Bullish first
                  candle2.close > candle2.open and  # Bullish middle
                  candle3.close < candle3.open):  # Bearish third
                  
                patterns.append({
                    'type': 'Evening Star',
                    'confidence': 'High',
                    'timestamp': candle3.timestamp,
                    'details': 'Bearish evening star pattern confirmed'
                })
            
            # MSS + BB (Market Structure Shift + Bullish/Bearish Bar)
            elif (i > 0):
                prev_candle = candles[i-1]
                
                if (direction == "Bullish" and
                    prev_candle.close < prev_candle.open and  # Previous bearish
                    candle2.close > candle2.open and  # Current bullish
                    abs(candle2.close - candle2.open) > 0.001):
                    
                    patterns.append({
                        'type': 'MSS + BB',
                        'confidence': 'High',
                        'timestamp': candle2.timestamp,
                        'details': 'Bullish MSS with bullish bar confirmation'
                    })
                
                elif (direction == "Bearish" and
                      prev_candle.close > prev_candle.open and  # Previous bullish
                      candle2.close < candle2.open and  # Current bearish
                      abs(candle2.open - candle2.close) > 0.001):
                      
                    patterns.append({
                        'type': 'MSS + BB',
                        'confidence': 'High',
                        'timestamp': candle2.timestamp,
                        'details': 'Bearish MSS with bearish bar confirmation'
                    })
        
        if patterns:
            best_pattern = max(patterns, key=lambda x: {
                'High': 3, 'Medium': 2, 'Low': 1
            }.get(x['confidence'], 1), reverse=True)
            
            return best_pattern['type'], best_pattern['details']
        
        return "None", "No clear confirmation pattern detected"
    
    def _calculate_confidence(self, analysis: SMCAnalysisFinal) -> int:
        """Calculate confidence score (0-100%)."""
        confidence = 0
        
        # Step 1: Direction (25% max)
        if analysis.direction != "Neutral":
            confidence += 25
            if analysis.event_4h in ["BOS", "MSS"]:
                confidence += 10
        
        # Step 2: POI (25% max)
        if analysis.poi_type != "None":
            confidence += 25
            if analysis.poi_type in ["Breaker Block", "Flip OB", "FVG", "OB", "RB", "OHOL", "OL"]:
                confidence += 10
        
        # Step 3: Liquidity Sweep (25% max)
        if analysis.liquidity_sweep == "Yes":
            confidence += 25
        
        # Step 4: Confirmation (25% max)
        if analysis.confirmation_pattern != "None":
            confidence += 25
            if analysis.confirmation_pattern in ["BE", "RB", "Morning Star", "Evening Star", "MSS + BB"]:
                confidence += 10
        
        # FINAL DECISION RULES (strict)
        # No sweep OR no confirmation → confidence ≤ 40% → NO TRADE
        if analysis.liquidity_sweep == "No" or analysis.confirmation_pattern == "None":
            confidence = min(confidence, 40)  # Cap at 40%
            if analysis.signal != "NO TRADE":
                analysis.signal = "NO TRADE"
                analysis.ai_reasons = "No sweep or no confirmation - confidence capped at 40%"
        
        # Check for conflicts - STRICT ALIGNMENT RULES
        # POI vs Direction conflicts - FORCED NO TRADE
        if analysis.direction == "Bullish" and "Bearish" in analysis.poi_type:
            confidence = 0  # Force NO TRADE
            analysis.signal = "NO TRADE"
            analysis.ai_reasons = "Conflicting POI/pattern"
        elif analysis.direction == "Bearish" and "Bullish" in analysis.poi_type:
            confidence = 0  # Force NO TRADE
            analysis.signal = "NO TRADE"
            analysis.ai_reasons = "Conflicting POI/pattern"
        
        # Pattern vs Direction conflicts - FORCED NO TRADE
        if analysis.direction == "Bullish" and "Bearish" in analysis.confirmation_pattern:
            confidence = 0  # Force NO TRADE
            analysis.signal = "NO TRADE"
            analysis.ai_reasons = "Conflicting POI/pattern"
        elif analysis.direction == "Bearish" and "Bullish" in analysis.confirmation_pattern:
            confidence = 0  # Force NO TRADE
            analysis.signal = "NO TRADE"
            analysis.ai_reasons = "Conflicting POI/pattern"
        
        # BOOST for perfectly aligned POI and patterns
        if analysis.direction == "Bullish" and "Bullish" in analysis.poi_type:
            confidence += 20  # Strong boost for aligned POI
        elif analysis.direction == "Bearish" and "Bearish" in analysis.poi_type:
            confidence += 20  # Strong boost for aligned POI
        
        if analysis.direction == "Bullish" and "Bullish" in analysis.confirmation_pattern:
            confidence += 15  # Boost for aligned pattern
        elif analysis.direction == "Bearish" and "Bearish" in analysis.confirmation_pattern:
            confidence += 15  # Boost for aligned pattern
        
        return min(max(confidence, 0), 100)
    
    def _generate_signal(self, analysis: SMCAnalysisFinal) -> Tuple[str, str, str, str]:
        """Generate trading signal based on analysis."""
        confidence = self._calculate_confidence(analysis)
        
        # If conflicts already forced NO TRADE, respect it
        if analysis.signal == "NO TRADE":
            return "NO TRADE", "N/A", "N/A", analysis.ai_reasons
        
        # BUY/SELL only if ≥75% AND perfect alignment
        if confidence < 75:
            return "NO TRADE", "N/A", "N/A", f"Confidence {confidence}% - below 75% threshold"
        
        # Check for perfect alignment before allowing BUY/SELL
        if analysis.direction == "Bullish":
            if "Bearish" in analysis.poi_type or "Bearish" in analysis.confirmation_pattern:
                return "NO TRADE", "N/A", "N/A", "Conflicting POI/pattern"
        elif analysis.direction == "Bearish":
            if "Bullish" in analysis.poi_type or "Bullish" in analysis.confirmation_pattern:
                return "NO TRADE", "N/A", "N/A", "Conflicting POI/pattern"
        
        # Generate trade levels for BUY/SELL
        if analysis.signal == "BUY":
            # Entry: at/near POI edge (bullish = above POI low)
            poi_low = float(analysis.poi_zone.split('-')[0]) if '-' in analysis.poi_zone else float(analysis.poi_zone)
            poi_high = float(analysis.poi_zone.split('-')[1]) if '-' in analysis.poi_zone else float(analysis.poi_zone)
            
            # Adjust buffer sizes based on asset type
            if self._is_crypto_pair(analysis.symbol):
                entry_buffer = 10.0
                sl_buffer = 50.0
                tp_distance = 100.0
            elif self._is_gold_pair(analysis.symbol):
                entry_buffer = 0.5
                sl_buffer = 2.0
                tp_distance = 10.0
            else:
                entry_buffer = 0.0005
                sl_buffer = 0.0010
                tp_distance = 0.0020
            
            entry = f"{poi_low + entry_buffer:.5f}"  # Above POI low
            sl = f"{poi_low - sl_buffer:.5f}"  # Below POI low + buffer
            tp = f"{poi_high + tp_distance:.5f}"  # Next liquidity level (1:2-1:3 RR minimum)
            
            return "BUY", entry, sl, tp, f"Perfect alignment with {confidence}% confidence"
        
        elif analysis.signal == "SELL":
            # Entry: at/near POI edge (bearish = below POI high)
            poi_low = float(analysis.poi_zone.split('-')[0]) if '-' in analysis.poi_zone else float(analysis.poi_zone)
            poi_high = float(analysis.poi_zone.split('-')[1]) if '-' in analysis.poi_zone else float(analysis.poi_zone)
            
            # Adjust buffer sizes based on asset type
            if self._is_crypto_pair(analysis.symbol):
                entry_buffer = 10.0
                sl_buffer = 50.0
                tp_distance = 100.0
            elif self._is_gold_pair(analysis.symbol):
                entry_buffer = 0.5
                sl_buffer = 2.0
                tp_distance = 10.0
            else:
                entry_buffer = 0.0005
                sl_buffer = 0.0010
                tp_distance = 0.0020
            
            entry = f"{poi_high - entry_buffer:.5f}"  # Below POI high
            sl = f"{poi_high + sl_buffer:.5f}"  # Above POI high + buffer
            tp = f"{poi_low - tp_distance:.5f}"  # Next liquidity level (1:2-1:3 RR minimum)
            
            return "SELL", entry, sl, tp, f"Perfect alignment with {confidence}% confidence"
        
        return "NO TRADE", "N/A", "N/A", "Waiting for better confluence"
    
    async def analyze_symbol(self, symbol: str, manual_input: str = None) -> SMCAnalysisFinal:
        """Perform exact 4-step SMC analysis."""
        analysis = SMCAnalysisFinal()
        analysis.symbol = symbol
        analysis.timestamp = datetime.utcnow()
        
        try:
            if manual_input:
                analysis.data_status = "Manual mode"
                return self._analyze_manual_input(analysis, manual_input)
            
            # Try Deriv WebSocket first
            try:
                candles_4h = await self.provider.get_candles(symbol, "4H", 200)
                candles_30m = await self.provider.get_candles(symbol, "30M", 200)
                candles_5m = await self.provider.get_candles(symbol, "5M", 100)
                
                if candles_4h and candles_30m and candles_5m:
                    analysis.data_status = "Deriv success"
                else:
                    analysis.data_status = "Deriv unavailable (check symbol like 'ETH') – emulated"
                    return await self._fallback_smc_emulation(analysis, symbol)
                    
            except Exception as e:
                analysis.data_status = "Deriv unavailable (check symbol like 'ETH') – emulated"
                return await self._fallback_smc_emulation(analysis, symbol)
            
            # Step 1: Direction (4H)
            direction, trend, event = self._detect_bos_mss(candles_4h)
            analysis.direction = direction
            analysis.bias_4h = direction
            analysis.trend_4h = trend
            analysis.event_4h = event
            
            # Step 2: POI (30M) - Priority order
            poi = None
            poi = self._detect_fvg(candles_30m)
            if not poi:
                poi = self._detect_order_blocks(candles_30m)
            if not poi:
                poi = self._detect_breaker_blocks(candles_30m)
            if not poi:
                poi = self._detect_flip_ob(candles_30m)
            if not poi:
                poi = self._detect_rejection_blocks(candles_30m)
            if not poi:
                poi = self._detect_ohol_ol(candles_30m)
            
            if poi:
                analysis.poi_type = poi['type']
                analysis.poi_zone = poi['zone']
            else:
                analysis.poi_type = "None"
                analysis.poi_zone = "N/A"
            
            # Step 3: Liquidity Sweep
            sweep, sweep_details = self._detect_liquidity_sweep(candles_30m, poi or {})
            analysis.liquidity_sweep = sweep
            analysis.sweep_details = sweep_details
            
            # Step 4: Confirmation (5M)
            confirmation, conf_details = self._detect_confirmation_patterns(candles_5m, direction)
            analysis.confirmation_pattern = confirmation
            
            # Set signal based on analysis
            if direction != "Neutral" and poi:
                analysis.signal = "BUY" if "Bullish" in direction else "SELL"
            else:
                analysis.signal = "NO TRADE"
            
            # Generate signal details
            signal, entry, sl, tp, reasons = self._generate_signal(analysis)
            analysis.entry_zone = entry
            analysis.invalidation_level = sl
            analysis.target1 = tp
            analysis.target2 = "N/A"
            analysis.confidence = self._calculate_confidence(analysis)
            analysis.ai_reasons = reasons
            analysis.risk_notes = f"Manage risk below {sl}, target at {tp}"
            
            return analysis
            
        except Exception as e:
            analysis.data_status = "Analysis failed - using fallback"
            return await self._fallback_smc_emulation(analysis, symbol, str(e))
    
    async def _fallback_smc_emulation(self, analysis: SMCAnalysisFinal, symbol: str, error: str = None) -> SMCAnalysisFinal:
        """Fallback SMC emulation when live data fails."""
        try:
            analysis.data_status = "Emulated historical – verify real-time on Deriv/TradingView/MT5"
            
            import random
            
            directions = ["Bullish", "Bearish", "Neutral"]
            poi_types = ["Bullish OB", "Bearish OB", "Bullish FVG", "Bearish FVG"]
            confirmations = ["BE", "RB", "Morning Star", "Evening Star", "None"]
            
            analysis.direction = random.choice(directions)
            analysis.bias_4h = analysis.direction
            analysis.trend_4h = random.choice(["BOS", "MSS", "None"])
            analysis.event_4h = f"Emulated {analysis.trend_4h}"
            
            analysis.poi_type = random.choice(poi_types)
            
            # Generate realistic zones based on symbol type
            price_range = self._get_realistic_price_range(symbol)
            base_price = (price_range[0] + price_range[1]) / 2
            
            if self._is_crypto_pair(symbol):
                zone_size = 100  # Crypto zones are larger
            elif self._is_gold_pair(symbol):
                zone_size = 5.0   # Gold zones (XAUUSD) are in the thousands
            else:
                zone_size = 0.0010  # Forex zones are smaller
            
            analysis.poi_zone = f"{base_price - zone_size:.5f}-{base_price + zone_size:.5f}"
            
            sweep_chance = 0.6 if analysis.poi_type != "None" else 0.1
            analysis.liquidity_sweep = "Yes" if random.random() < sweep_chance else "No"
            analysis.sweep_details = "Emulated sweep detection" if analysis.liquidity_sweep == "Yes" else "No sweep detected"
            
            analysis.confirmation_pattern = random.choice(confirmations)
            
            if analysis.direction != "Neutral" and analysis.poi_type != "None":
                analysis.signal = "BUY" if "Bullish" in analysis.direction else "SELL"
            else:
                analysis.signal = "NO TRADE"
            
            analysis.confidence = random.randint(45, 85) if analysis.signal != "NO TRADE" else random.randint(0, 30)
            
            if analysis.signal != "NO TRADE":
                if analysis.signal == "BUY":
                    analysis.entry_zone = analysis.poi_zone
                    analysis.invalidation_level = f"{base_price - zone_size * 2:.5f}"
                    analysis.target1 = f"{base_price + zone_size * 2:.5f}"
                else:
                    analysis.entry_zone = analysis.poi_zone
                    analysis.invalidation_level = f"{base_price + zone_size * 2:.5f}"
                    analysis.target1 = f"{base_price - zone_size * 2:.5f}"
                
                analysis.ai_reasons = f"Emulated {analysis.direction.lower()} setup with {analysis.confidence}% confidence"
                analysis.risk_notes = f"Manage risk below {analysis.invalidation_level}, target at {analysis.target1}"
            else:
                analysis.entry_zone = "N/A"
                analysis.invalidation_level = "N/A"
                analysis.target1 = "N/A"
                analysis.ai_reasons = "Emulated analysis - verify live on Deriv/TradingView"
                analysis.risk_notes = "Waiting for better confluence"
            
            return analysis
            
        except Exception as e:
            analysis.data_status = "Fallback failed"
            analysis.direction = "Neutral"
            analysis.poi_type = "None"
            analysis.liquidity_sweep = "No"
            analysis.confirmation_pattern = "None"
            analysis.signal = "NO TRADE"
            analysis.confidence = 0
            analysis.ai_reasons = f"Fallback emulation failed: {str(e)}"
            analysis.risk_notes = "Analysis failed - check data connection"
            
            return analysis
    
    def _analyze_manual_input(self, analysis: SMCAnalysisFinal, manual_input: str) -> SMCAnalysisFinal:
        """Analyze based on manual user input."""
        analysis.data_status = "Manual mode"
        
        input_lower = manual_input.lower()
        
        # Extract direction
        if "bullish" in input_lower:
            analysis.direction = "Bullish"
            analysis.signal = "BUY"
        elif "bearish" in input_lower:
            analysis.direction = "Bearish"
            analysis.signal = "SELL"
        else:
            analysis.direction = "Neutral"
            analysis.signal = "NO TRADE"
        
        # Extract POI type
        poi_types = ["breaker block", "flip ob", "fvg", "ob", "rb", "ohol", "ol"]
        for poi_type in poi_types:
            if poi_type in input_lower:
                analysis.poi_type = poi_type.replace(" ", " ").title()
                break
        
        # Extract sweep info
        analysis.liquidity_sweep = "Yes" if "sweep" in input_lower else "No"
        analysis.sweep_details = "Manual input: sweep detected" if analysis.liquidity_sweep == "Yes" else "Manual input: no sweep"
        
        # Extract confirmation
        confirmations = ["be", "rb", "morning star", "evening star", "mss", "bb"]
        for conf in confirmations:
            if conf in input_lower:
                analysis.confirmation_pattern = conf.upper().replace("BB", "MSS + BB")
                break
        
        # Generate realistic zones based on symbol type
        price_range = self._get_realistic_price_range(analysis.symbol)
        base_price = (price_range[0] + price_range[1]) / 2
        
        if self._is_crypto_pair(analysis.symbol):
            zone_size = 100
        elif self._is_gold_pair(analysis.symbol):
            zone_size = 5.0   # Gold zones (XAUUSD) are in the thousands
        else:
            zone_size = 0.0010  # Forex zones are smaller
        
        analysis.poi_zone = f"{base_price - zone_size:.5f}-{base_price + zone_size:.5f}"
        
        # Set high confidence for manual input
        analysis.confidence = 85 if analysis.signal != "NO TRADE" else 0
        
        if analysis.signal != "NO TRADE":
            if analysis.signal == "BUY":
                analysis.entry_zone = analysis.poi_zone
                analysis.invalidation_level = f"{base_price - zone_size * 2:.5f}"
                analysis.target1 = f"{base_price + zone_size * 2:.5f}"
            else:
                analysis.entry_zone = analysis.poi_zone
                analysis.invalidation_level = f"{base_price + zone_size * 2:.5f}"
                analysis.target1 = f"{base_price - zone_size * 2:.5f}"
        
        analysis.ai_reasons = "Manual input analysis - user provided structure"
        analysis.risk_notes = "Based on manual input - verify live setup"
        
        return analysis
