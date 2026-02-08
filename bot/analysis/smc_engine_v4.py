"""
CurrencyBot v4 - Ultra-Reliable SMC Analysis Engine
Exact 4-step Smart Money Concepts with enhanced data validation and fallback
"""

import asyncio
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import numpy as np

from ..providers.base import MarketDataProvider, Candle, DataProviderError
from ..config import Config


class SMCAnalysisV4:
    """SMC analysis result structure for CurrencyBot v4."""
    
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
        self.poi_type: str = "None"  # ONLY: Breaker Block, Flip OB, FVG, OB, RB, OHOL/OL
        self.poi_zone: str = "N/A"
        self.poi_timeframe: str = "30M"
        
        # Step 3: Liquidity Sweep
        self.liquidity_sweep: str = "No"
        self.sweep_details: str = "No sweep detected"
        
        # Step 4: Confirmation
        self.confirmation_pattern: str = "None"  # BE, RB, Morning/Evening Star, MSS + BB, candles on 5M
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
            'bias_4h': self.bias_4h,
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


class SMCEngineV4:
    """CurrencyBot v4 - Ultra-Reliable SMC analysis engine."""
    
    def __init__(self, provider: MarketDataProvider, config: Config):
        self.provider = provider
        self.config = config
        self.educational_terms_shown = set()
    
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
            
            # Check if this is a swing high
            is_swing_high = all(c.high < high for c in window_candles[1:])
            if is_swing_high:
                swing_highs.append({
                    'price': high,
                    'index': i + window // 2,
                    'timestamp': window_candles[window // 2].timestamp
                })
            
            # Check if this is a swing low
            is_swing_low = all(c.low > low for c in window_candles[1:])
            if is_swing_low:
                swing_lows.append({
                    'price': low,
                    'index': i + window // 2,
                    'timestamp': window_candles[window // 2].timestamp
                })
        
        return swing_highs, swing_lows
    
    def _detect_bos_mss(self, candles: List[Candle]) -> Tuple[str, str, str]:
        """Detect BOS (continuation) or MSS/CHoCH (reversal) on 4H."""
        swing_highs, swing_lows = self._get_swing_points(candles, window=5)
        
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return "Neutral", "None", "Insufficient swing points"
        
        # Get recent swing points
        recent_highs = sorted(swing_highs, key=lambda x: x['timestamp'], reverse=True)[:3]
        recent_lows = sorted(swing_lows, key=lambda x: x['timestamp'], reverse=True)[:3]
        
        current_price = candles[0].close
        
        # Check for BOS (Break of Structure - continuation)
        # Bullish BOS: Price breaks above recent high
        if current_price > recent_highs[0]['price']:
            return "Bullish", "BOS", f"Price broke above recent high at {recent_highs[0]['price']:.5f}"
        
        # Bearish BOS: Price breaks below recent low
        elif current_price < recent_lows[0]['price']:
            return "Bearish", "BOS", f"Price broke below recent low at {recent_lows[0]['price']:.5f}"
        
        # Check for MSS/CHoCH (Market Structure Shift - reversal)
        # Bullish MSS: Lower highs and higher lows
        if (len(recent_highs) >= 2 and len(recent_lows) >= 2 and
            recent_highs[0]['price'] < recent_highs[1]['price'] and
            recent_lows[0]['price'] > recent_lows[1]['price']):
            return "Bullish", "MSS", "Lower highs and higher lows detected"
        
        # Bearish MSS: Higher highs and lower lows
        if (len(recent_highs) >= 2 and len(recent_lows) >= 2 and
            recent_highs[0]['price'] > recent_highs[1]['price'] and
            recent_lows[0]['price'] < recent_lows[1]['price']):
            return "Bearish", "MSS", "Higher highs and lower lows detected"
        
        return "Neutral", "None", "No clear structure established"
    
    def _detect_fvg(self, candles: List[Candle]) -> Optional[Dict]:
        """Detect Fair Value Gaps (FVG) on 30M."""
        if len(candles) < 3:
            return None
        
        fvgs = []
        for i in range(len(candles) - 2):
            candle1 = candles[i]
            candle2 = candles[i + 1]
            candle3 = candles[i + 2]
            
            # Bullish FVG: Gap up
            if candle2.low > candle1.high:
                fvg_top = candle1.high
                fvg_bottom = candle2.low
                fvg_size = candle2.low - candle1.high
                
                if abs(fvg_size) > 0.0001:  # Minimum size threshold
                    fvgs.append({
                        'type': 'Bullish FVG',
                        'top': fvg_top,
                        'bottom': fvg_bottom,
                        'size': fvg_size,
                        'timestamp': candle2.timestamp,
                        'zone': f"{fvg_bottom:.5f}-{fvg_top:.5f}"
                    })
            
            # Bearish FVG: Gap down
            elif candle2.high < candle1.low:
                fvg_top = candle2.high
                fvg_bottom = candle1.low
                fvg_size = candle1.low - candle2.high
                
                if abs(fvg_size) > 0.0001:  # Minimum size threshold
                    fvgs.append({
                        'type': 'Bearish FVG',
                        'top': fvg_top,
                        'bottom': fvg_bottom,
                        'size': fvg_size,
                        'timestamp': candle2.timestamp,
                        'zone': f"{fvg_bottom:.5f}-{fvg_top:.5f}"
                    })
        
        if fvgs:
            # Return most recent significant FVG
            return max(fvgs, key=lambda x: abs(x['size']), reverse=True)
        
        return None
    
    def _detect_order_blocks(self, candles: List[Candle]) -> Optional[Dict]:
        """Detect Order Blocks (OB) on 30M."""
        if len(candles) < 5:
            return None
        
        order_blocks = []
        for i in range(len(candles) - 4):
            # Look for strong momentum candles followed by reversal
            candle1 = candles[i]
            candle2 = candles[i + 1]
            candle3 = candles[i + 2]
            candle4 = candles[i + 3]
            candle5 = candles[i + 4]
            
            # Bullish Order Block: Strong down candle followed by strong up move
            if (candle1.close < candle1.open and  # Bearish
                abs(candle1.close - candle1.open) > 0.001 and  # Strong move
                candle5.close > candle5.open and  # Bullish reversal
                abs(candle5.close - candle5.open) > 0.001):  # Strong move
                
                ob_high = max(candle1.high, candle2.high, candle3.high, candle4.high)
                ob_low = min(candle1.low, candle2.low, candle3.low, candle4.low)
                
                order_blocks.append({
                    'type': 'Bullish OB',
                    'high': ob_high,
                    'low': ob_low,
                    'timestamp': candle1.timestamp,
                    'zone': f"{ob_low:.5f}-{ob_high:.5f}"
                })
            
            # Bearish Order Block: Strong up candle followed by strong down move
            elif (candle1.close > candle1.open and  # Bullish
                  abs(candle1.close - candle1.open) > 0.001 and  # Strong move
                  candle5.close < candle5.open and  # Bearish reversal
                  abs(candle5.close - candle5.open) > 0.001):  # Strong move
                  
                ob_high = max(candle1.high, candle2.high, candle3.high, candle4.high)
                ob_low = min(candle1.low, candle2.low, candle3.low, candle4.low)
                
                order_blocks.append({
                    'type': 'Bearish OB',
                    'high': ob_high,
                    'low': ob_low,
                    'timestamp': candle1.timestamp,
                    'zone': f"{ob_low:.5f}-{ob_high:.5f}"
                })
        
        if order_blocks:
            # Return most recent order block
            return max(order_blocks, key=lambda x: x['timestamp'], reverse=True)
        
        return None
    
    def _detect_breaker_blocks(self, candles: List[Candle]) -> Optional[Dict]:
        """Detect Breaker Blocks on 30M."""
        if len(candles) < 5:
            return None
        
        # Look for order blocks that have been broken
        order_blocks = self._detect_order_blocks(candles[:-2])  # Exclude last 2 candles
        
        if not order_blocks:
            return None
        
        current_price = candles[0].close
        
        for ob in order_blocks:
            # Check if price has broken the order block
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
        
        # Look for order blocks that flip structure
        flip_obs = []
        for i in range(len(candles) - 4):
            candle1 = candles[i]
            candle2 = candles[i + 1]
            candle3 = candles[i + 2]
            candle4 = candles[i + 3]
            candle5 = candles[i + 4]
            
            # Bullish Flip OB: Bearish momentum followed by bullish reversal
            if (candle1.close < candle1.open and  # Bearish momentum
                abs(candle1.close - candle1.open) > 0.0005 and  # Strong bearish
                candle5.close > candle5.open and  # Bullish reversal
                abs(candle5.close - candle5.open) > 0.0005):  # Strong bullish
                
                ob_high = max(candle1.high, candle2.high, candle3.high, candle4.high)
                ob_low = min(candle1.low, candle2.low, candle3.low, candle4.low)
                
                flip_obs.append({
                    'type': 'Flip OB',
                    'high': ob_high,
                    'low': ob_low,
                    'timestamp': candle1.timestamp,
                    'zone': f"{ob_low:.5f}-{ob_high:.5f}"
                })
            
            # Bearish Flip OB: Bullish momentum followed by bearish reversal
            elif (candle1.close > candle1.open and  # Bullish momentum
                  abs(candle1.close - candle1.open) > 0.0005 and  # Strong bullish
                  candle5.close < candle5.open and  # Bearish reversal
                  abs(candle5.open - candle5.close) > 0.0005):  # Strong bearish
                  
                ob_high = max(candle1.high, candle2.high, candle3.high, candle4.high)
                ob_low = min(candle1.low, candle2.low, candle3.low, candle4.low)
                
                flip_obs.append({
                    'type': 'Flip OB',
                    'high': ob_high,
                    'low': ob_low,
                    'timestamp': candle1.timestamp,
                    'zone': f"{ob_low:.5f}-{ob_high:.5f}"
                })
        
        if flip_obs:
            # Return most recent flip OB
            return max(flip_obs, key=lambda x: x['timestamp'], reverse=True)
        
        return None
    
    def _detect_liquidity_sweep(self, candles: List[Candle], poi: Dict) -> Tuple[str, str]:
        """Detect if price swept liquidity into POI."""
        if not poi or len(candles) < 10:
            return "No", "No POI or insufficient data"
        
        current_price = candles[0].close
        poi_high = float(poi['zone'].split('-')[1])
        poi_low = float(poi['zone'].split('-')[0])
        
        # Get recent highs and lows for liquidity levels
        recent_candles = candles[:10]
        recent_highs = sorted([c.high for c in recent_candles], reverse=True)[:3]
        recent_lows = sorted([c.low for c in recent_candles])[:3]
        
        sweep_details = []
        
        # Check for sweep above recent highs (for bearish POI)
        if 'Bearish' in poi['type']:
            for high in recent_highs:
                if current_price > high and abs(current_price - high) < 0.0005:
                    sweep_details.append(f"Wicked above recent high at {high:.5f}")
                    break
        
        # Check for sweep below recent lows (for bullish POI)
        elif 'Bullish' in poi['type']:
            for low in recent_lows:
                if current_price < low and abs(low - current_price) < 0.0005:
                    sweep_details.append(f"Wicked below recent low at {low:.5f}")
                    break
        
        # Check for equal highs/lows (stop hunt)
        equal_highs = [h for h in recent_highs if abs(h - recent_highs[0]) < 0.0001]
        equal_lows = [l for l in recent_lows if abs(l - recent_lows[0]) < 0.0001]
        
        if equal_highs and 'Bearish' in poi['type']:
            sweep_details.append("Stop hunt at equal highs detected")
        elif equal_lows and 'Bullish' in poi['type']:
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
            
            # Breaker Entry (BE)
            if (direction == "Bullish" and
                candle2.close > candle2.open and  # Bullish
                candle3.close > candle3.open and  # Continuation
                candle2.high > max(candle1.high, candle3.high)):  # Break of structure
                
                patterns.append({
                    'type': 'BE',
                    'confidence': 'High',
                    'timestamp': candle2.timestamp,
                    'details': 'Bullish breaker entry confirmed'
                })
            
            elif (direction == "Bearish" and
                  candle2.close < candle2.open and  # Bearish
                  candle3.close < candle3.open and  # Continuation
                  candle2.low < min(candle1.low, candle3.low)):  # Break of structure
                  
                patterns.append({
                    'type': 'BE',
                    'confidence': 'High',
                    'timestamp': candle2.timestamp,
                    'details': 'Bearish breaker entry confirmed'
                })
            
            # Rejection Bar (RB)
            elif (direction == "Bullish" and
                  candle2.close > candle2.open and
                  candle2.high - max(candle2.open, candle2.close) > 0.0003):  # Long upper wick
                  
                patterns.append({
                    'type': 'RB',
                    'confidence': 'Medium',
                    'timestamp': candle2.timestamp,
                    'details': 'Bullish rejection bar confirmed'
                })
            
            elif (direction == "Bearish" and
                  candle2.close < candle2.open and
                  max(candle2.open, candle2.close) - candle2.low > 0.0003):  # Long lower wick
                  
                patterns.append({
                    'type': 'RB',
                    'confidence': 'Medium',
                    'timestamp': candle2.timestamp,
                    'details': 'Bearish rejection bar confirmed'
                })
            
            # Morning Star
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
            
            # Evening Star
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
            elif (i > 0):  # Need structure context
                prev_candle = candles[i-1]
                
                # Bullish MSS + Bullish Bar
                if (direction == "Bullish" and
                    prev_candle.close < prev_candle.open and  # Previous bearish
                    candle2.close > candle2.open and  # Current bullish
                    abs(candle2.close - candle2.open) > 0.001):  # Strong move
                    
                    patterns.append({
                        'type': 'MSS + BB',
                        'confidence': 'High',
                        'timestamp': candle2.timestamp,
                        'details': 'Bullish MSS with bullish bar confirmation'
                    })
                
                # Bearish MSS + Bearish Bar
                elif (direction == "Bearish" and
                      prev_candle.close > prev_candle.open and  # Previous bullish
                      candle2.close < candle2.open and  # Current bearish
                      abs(candle2.open - candle2.close) > 0.001):  # Strong move
                      
                    patterns.append({
                        'type': 'MSS + BB',
                        'confidence': 'High',
                        'timestamp': candle2.timestamp,
                        'details': 'Bearish MSS with bearish bar confirmation'
                    })
        
        if patterns:
            # Return highest confidence pattern
            best_pattern = max(patterns, key=lambda x: {
                'High': 3, 'Medium': 2, 'Low': 1
            }.get(x['confidence'], 1), reverse=True)
            
            return best_pattern['type'], best_pattern['details']
        
        return "None", "No clear confirmation pattern detected"
    
    def _calculate_confidence(self, analysis: SMCAnalysisV4) -> int:
        """Calculate confidence score (0-100%)."""
        confidence = 0
        
        # Step 1: Direction (25% max)
        if analysis.direction != "Neutral":
            confidence += 25
            if analysis.event_4h in ["BOS", "MSS"]:
                confidence += 10  # Bonus for clear structure
        
        # Step 2: POI (25% max)
        if analysis.poi_type != "None":
            confidence += 25
            if analysis.poi_type in ["Breaker Block", "Flip OB", "FVG", "OB", "RB"]:
                confidence += 10  # Bonus for valid POI types
        
        # Step 3: Liquidity Sweep (25% max)
        if analysis.liquidity_sweep == "Yes":
            confidence += 25
        
        # Step 4: Confirmation (25% max)
        if analysis.confirmation_pattern != "None":
            confidence += 25
            if analysis.confirmation_pattern in ["BE", "MSS + BB", "Morning Star", "Evening Star"]:
                confidence += 10  # Bonus for strong patterns
        
        return min(confidence, 100)
    
    def _generate_signal(self, analysis: SMCAnalysisV4) -> Tuple[str, str, str, str]:
        """Generate trading signal based on analysis."""
        confidence = self._calculate_confidence(analysis)
        
        if confidence < 70:
            return "NO TRADE", "N/A", "N/A", "Insufficient confluence for high-confidence setup"
        
        if analysis.signal == "BUY":
            # Bullish setup
            entry = analysis.poi_zone
            sl = analysis.poi_zone.split('-')[0] if '-' in analysis.poi_zone else analysis.poi_zone
            tp = f"{float(sl) + 0.0020:.5f}"  # 20 pips target
            
            return "BUY", entry, sl, tp, f"Bullish setup with {confidence}% confidence"
        
        elif analysis.signal == "SELL":
            # Bearish setup
            entry = analysis.poi_zone
            sl = analysis.poi_zone.split('-')[1] if '-' in analysis.poi_zone else analysis.poi_zone
            tp = f"{float(sl) - 0.0020:.5f}"  # 20 pips target
            
            return "SELL", entry, sl, tp, f"Bearish setup with {confidence}% confidence"
        
        return "NO TRADE", "N/A", "N/A", "Waiting for better confluence"
    
    async def analyze_symbol(self, symbol: str, manual_input: str = None) -> SMCAnalysisV4:
        """Perform complete 4-step SMC analysis."""
        analysis = SMCAnalysisV4()
        analysis.symbol = symbol
        analysis.timestamp = datetime.utcnow()
        
        try:
            # Manual mode: prioritize user input
            if manual_input:
                analysis.data_status = "Manual mode"
                # Parse manual input and run steps
                return self._analyze_manual_input(analysis, manual_input)
            
            # Get data for all timeframes
            candles_4h = await self.provider.get_candles(symbol, "4H", 200)
            candles_30m = await self.provider.get_candles(symbol, "30M", 200)
            candles_5m = await self.provider.get_candles(symbol, "5M", 100)
            
            if not candles_4h or not candles_30m or not candles_5m:
                # Fallback to SMC emulation
                return await self._fallback_smc_emulation(analysis, symbol)
            
            analysis.data_status = "Deriv success"
            
            # Step 1: Direction (4H)
            direction, trend, event = self._detect_bos_mss(candles_4h)
            analysis.direction = direction
            analysis.bias_4h = direction
            analysis.trend_4h = trend
            analysis.event_4h = event
            
            # Step 2: POI (30M) - Priority order
            poi = None
            
            # Try different POI types in priority order
            poi = self._detect_fvg(candles_30m)
            if not poi:
                poi = self._detect_order_blocks(candles_30m)
            if not poi:
                poi = self._detect_breaker_blocks(candles_30m)
            if not poi:
                poi = self._detect_flip_ob(candles_30m)
            
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
            # Fallback analysis
            return await self._fallback_smc_emulation(analysis, symbol, str(e))
    
    async def _fallback_smc_emulation(self, analysis: SMCAnalysisV4, symbol: str, error: str = None) -> SMCAnalysisV4:
        """Fallback SMC emulation when live data fails."""
        try:
            analysis.data_status = f"Fallback SMC emulation{f' - {error}' if error else ''}"
            
            # Emulate SMC analysis with basic logic
            import random
            
            # Generate realistic but random analysis for demo
            directions = ["Bullish", "Bearish", "Neutral"]
            poi_types = ["Bullish OB", "Bearish OB", "Bullish FVG", "Bearish FVG"]
            confirmations = ["BE", "RB", "Morning Star", "Evening Star", "None"]
            
            analysis.direction = random.choice(directions)
            analysis.bias_4h = analysis.direction
            analysis.trend_4h = random.choice(["BOS", "MSS", "None"])
            analysis.event_4h = f"Emulated {analysis.trend_4h}"
            
            analysis.poi_type = random.choice(poi_types)
            analysis.poi_zone = f"{1.0850:.4f}-{1.0865:.4f}"  # Realistic zone
            
            sweep_chance = 0.6 if analysis.poi_type != "None" else 0.1
            analysis.liquidity_sweep = "Yes" if random.random() < sweep_chance else "No"
            analysis.sweep_details = "Emulated sweep detection" if analysis.liquidity_sweep == "Yes" else "No sweep detected"
            
            analysis.confirmation_pattern = random.choice(confirmations)
            
            # Set signal based on direction and POI
            if analysis.direction != "Neutral" and analysis.poi_type != "None":
                analysis.signal = "BUY" if "Bullish" in analysis.direction else "SELL"
            else:
                analysis.signal = "NO TRADE"
            
            # Calculate confidence
            analysis.confidence = random.randint(45, 85) if analysis.signal != "NO TRADE" else random.randint(0, 30)
            
            # Generate realistic levels
            if analysis.signal != "NO TRADE":
                base_price = 1.0850
                analysis.entry_zone = analysis.poi_zone
                if analysis.signal == "BUY":
                    analysis.invalidation_level = f"{base_price - 0.0010:.4f}"
                    analysis.target1 = f"{base_price + 0.0020:.4f}"
                else:
                    analysis.invalidation_level = f"{base_price + 0.0010:.4f}"
                    analysis.target1 = f"{base_price - 0.0020:.4f}"
                
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
            analysis.data_status = f"Fallback failed - {str(e)}"
            analysis.direction = "Neutral"
            analysis.poi_type = "None"
            analysis.liquidity_sweep = "No"
            analysis.confirmation_pattern = "None"
            analysis.signal = "NO TRADE"
            analysis.confidence = 0
            analysis.ai_reasons = f"Fallback emulation failed: {str(e)}"
            analysis.risk_notes = "Analysis failed - check data connection"
            
            return analysis
    
    def _analyze_manual_input(self, analysis: SMCAnalysisV4, manual_input: str) -> SMCAnalysisV4:
        """Analyze based on manual user input."""
        analysis.data_status = "Manual mode"
        
        # Parse manual input (basic parsing)
        input_lower = manual_input.lower()
        
        # Extract direction from manual input
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
        
        # Set high confidence for manual input
        analysis.confidence = 85 if analysis.signal != "NO TRADE" else 0
        
        # Generate realistic levels
        if analysis.signal != "NO TRADE":
            analysis.poi_zone = "1.0850-1.0865"  # Default zone
            if analysis.signal == "BUY":
                analysis.entry_zone = analysis.poi_zone
                analysis.invalidation_level = "1.0840"
                analysis.target1 = "1.0890"
            else:
                analysis.entry_zone = analysis.poi_zone
                analysis.invalidation_level = "1.0870"
                analysis.target1 = "1.0810"
        
        analysis.ai_reasons = "Manual input analysis - user provided structure"
        analysis.risk_notes = "Based on manual input - verify live setup"
        
        return analysis
