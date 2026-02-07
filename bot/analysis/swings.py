from typing import List, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel

from ..providers.base import Candle

class SwingPoint(BaseModel):
    """Swing high/low point."""
    timestamp: datetime
    price: float
    is_high: bool  # True for swing high, False for swing low
    candle_index: int

class MarketStructure(BaseModel):
    """Market structure analysis result."""
    trend: str  # "uptrend", "downtrend", "sideways"
    last_swing_high: Optional[SwingPoint]
    last_swing_low: Optional[SwingPoint]
    higher_highs: List[SwingPoint]
    higher_lows: List[SwingPoint]
    lower_highs: List[SwingPoint]
    lower_lows: List[SwingPoint]

class SwingDetector:
    """Detect swing highs and lows using fractal method."""
    
    def __init__(self, lookback: int = 3):
        self.lookback = lookback
    
    def detect_swings(self, candles: List[Candle]) -> List[SwingPoint]:
        """Detect swing points using fractal method."""
        if len(candles) < self.lookback * 2 + 1:
            return []
        
        swings = []
        
        # Iterate through candles (excluding edges)
        for i in range(self.lookback, len(candles) - self.lookback):
            current = candles[i]
            
            # Check for swing high
            is_swing_high = True
            for j in range(i - self.lookback, i + self.lookback + 1):
                if j != i and candles[j].high >= current.high:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                swings.append(SwingPoint(
                    timestamp=current.timestamp,
                    price=current.high,
                    is_high=True,
                    candle_index=i
                ))
            
            # Check for swing low
            is_swing_low = True
            for j in range(i - self.lookback, i + self.lookback + 1):
                if j != i and candles[j].low <= current.low:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                swings.append(SwingPoint(
                    timestamp=current.timestamp,
                    price=current.low,
                    is_high=False,
                    candle_index=i
                ))
        
        return swings
    
    def analyze_structure(self, candles: List[Candle]) -> MarketStructure:
        """Analyze market structure from swing points."""
        swings = self.detect_swings(candles)
        
        if not swings:
            return MarketStructure(
                trend="sideways",
                last_swing_high=None,
                last_swing_low=None,
                higher_highs=[],
                higher_lows=[],
                lower_highs=[],
                lower_lows=[]
            )
        
        # Separate highs and lows
        swing_highs = [s for s in swings if s.is_high]
        swing_lows = [s for s in swings if not s.is_high]
        
        # Get last swing points
        last_swing_high = max(swing_highs, key=lambda x: x.timestamp) if swing_highs else None
        last_swing_low = max(swing_lows, key=lambda x: x.timestamp) if swing_lows else None
        
        # Analyze trend and structure
        higher_highs = []
        higher_lows = []
        lower_highs = []
        lower_lows = []
        
        # Compare consecutive swing points
        for i in range(1, len(swing_highs)):
            prev_high = swing_highs[i-1]
            curr_high = swing_highs[i]
            if curr_high.price > prev_high.price:
                higher_highs.append(curr_high)
            else:
                lower_highs.append(curr_high)
        
        for i in range(1, len(swing_lows)):
            prev_low = swing_lows[i-1]
            curr_low = swing_lows[i]
            if curr_low.price > prev_low.price:
                higher_lows.append(curr_low)
            else:
                lower_lows.append(curr_low)
        
        # Determine trend
        if len(higher_highs) > 0 and len(higher_lows) > 0:
            trend = "uptrend"
        elif len(lower_highs) > 0 and len(lower_lows) > 0:
            trend = "downtrend"
        else:
            trend = "sideways"
        
        return MarketStructure(
            trend=trend,
            last_swing_high=last_swing_high,
            last_swing_low=last_swing_low,
            higher_highs=higher_highs,
            higher_lows=higher_lows,
            lower_highs=lower_highs,
            lower_lows=lower_lows
        )
