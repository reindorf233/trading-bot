from typing import List, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel

from ..providers.base import Candle
from .swings import SwingDetector, MarketStructure, SwingPoint

class BOSMSSResult(BaseModel):
    """Break of Structure or Market Structure Shift result."""
    event_type: str  # "BOS_UP", "BOS_DOWN", "MSS_UP", "MSS_DOWN", "NONE"
    timestamp: datetime
    price: float
    swing_level: float
    candle_index: int
    confidence: float = 1.0

class StructureAnalyzer:
    """Analyze market structure for BOS and MSS patterns."""
    
    def __init__(self, lookback: int = 3):
        self.swing_detector = SwingDetector(lookback)
    
    def detect_bos_mss(self, candles: List[Candle]) -> List[BOSMSSResult]:
        """Detect Break of Structure and Market Structure Shift."""
        if len(candles) < 20:  # Minimum candles for analysis
            return []
        
        structure = self.swing_detector.analyze_structure(candles)
        results = []
        
        # Get recent swing points
        swings = self.swing_detector.detect_swings(candles)
        
        if not swings:
            return []
        
        # Check for BOS (Break of Structure)
        for i, candle in enumerate(candles):
            # Skip recent candles to avoid false signals
            if i < 10:
                continue
            
            # Bullish BOS: Close breaks above last swing high
            if structure.last_swing_high and structure.trend in ["uptrend", "sideways"]:
                if (candle.close > structure.last_swing_high.price and 
                    i > structure.last_swing_high.candle_index):
                    
                    # Check if this is a new BOS (not already detected)
                    is_new = True
                    for result in results:
                        if (result.event_type == "BOS_UP" and 
                            abs(result.timestamp - candle.timestamp).total_seconds() < 3600):
                            is_new = False
                            break
                    
                    if is_new:
                        results.append(BOSMSSResult(
                            event_type="BOS_UP",
                            timestamp=candle.timestamp,
                            price=candle.close,
                            swing_level=structure.last_swing_high.price,
                            candle_index=i
                        ))
            
            # Bearish BOS: Close breaks below last swing low
            if structure.last_swing_low and structure.trend in ["downtrend", "sideways"]:
                if (candle.close < structure.last_swing_low.price and 
                    i > structure.last_swing_low.candle_index):
                    
                    # Check if this is a new BOS
                    is_new = True
                    for result in results:
                        if (result.event_type == "BOS_DOWN" and 
                            abs(result.timestamp - candle.timestamp).total_seconds() < 3600):
                            is_new = False
                            break
                    
                    if is_new:
                        results.append(BOSMSSResult(
                            event_type="BOS_DOWN",
                            timestamp=candle.timestamp,
                            price=candle.close,
                            swing_level=structure.last_swing_low.price,
                            candle_index=i
                        ))
        
        # Check for MSS (Market Structure Shift)
        # MSS occurs when a protected swing level breaks against the trend
        for i, candle in enumerate(candles):
            if i < 10:
                continue
            
            # Bullish MSS: In downtrend, break above recent swing low
            if (structure.trend == "downtrend" and 
                structure.last_swing_low and 
                candle.close > structure.last_swing_low.price and
                i > structure.last_swing_low.candle_index):
                
                # Verify this breaks the downtrend structure
                if len(structure.lower_lows) >= 2:
                    results.append(BOSMSSResult(
                        event_type="MSS_UP",
                        timestamp=candle.timestamp,
                        price=candle.close,
                        swing_level=structure.last_swing_low.price,
                        candle_index=i,
                        confidence=0.8
                    ))
            
            # Bearish MSS: In uptrend, break below recent swing high
            if (structure.trend == "uptrend" and 
                structure.last_swing_high and 
                candle.close < structure.last_swing_high.price and
                i > structure.last_swing_high.candle_index):
                
                # Verify this breaks the uptrend structure
                if len(structure.higher_highs) >= 2:
                    results.append(BOSMSSResult(
                        event_type="MSS_DOWN",
                        timestamp=candle.timestamp,
                        price=candle.close,
                        swing_level=structure.last_swing_high.price,
                        candle_index=i,
                        confidence=0.8
                    ))
        
        # Sort by timestamp (newest first) and return most recent
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[:5]  # Return up to 5 most recent events
    
    def get_bias(self, candles: List[Candle]) -> Tuple[str, Optional[BOSMSSResult]]:
        """Determine market bias from BOS/MSS analysis."""
        events = self.detect_bos_mss(candles)
        
        if not events:
            return "NEUTRAL", None
        
        # Get most recent significant event
        latest_event = events[0]
        
        if latest_event.event_type in ["BOS_UP", "MSS_UP"]:
            return "LONG", latest_event
        elif latest_event.event_type in ["BOS_DOWN", "MSS_DOWN"]:
            return "SHORT", latest_event
        else:
            return "NEUTRAL", None
