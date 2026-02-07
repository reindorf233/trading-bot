from typing import List, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel

from ..providers.base import Candle
from ..config import Config

class OrderBlock(BaseModel):
    """Order Block zone."""
    timestamp: datetime
    high: float
    low: float
    open_price: float
    close_price: float
    is_bullish: bool
    candle_index: int
    strength: float = 1.0

class FairValueGap(BaseModel):
    """Fair Value Gap zone."""
    timestamp: datetime
    top: float
    bottom: float
    mid: float
    is_bullish: bool
    candle_index: int
    fill_percentage: float = 0.0

class Breaker(BaseModel):
    """Breaker zone."""
    timestamp: datetime
    high: float
    low: float
    original_ob_high: float
    original_ob_low: float
    candle_index: int

class POIResult(BaseModel):
    """Point of Interest detection result."""
    poi_type: str  # "OB", "FVG", "BREAKER", "FLIP_OB", "RB", "OHOL"
    zone_high: float
    zone_low: float
    timestamp: datetime
    candle_index: int
    strength: float = 1.0
    is_bullish: bool
    details: dict = {}

class POIDetector:
    """Detect Points of Interest (POI) in market structure."""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
    
    def detect_order_blocks(self, candles: List[Candle]) -> List[OrderBlock]:
        """Detect Order Blocks from impulsive moves."""
        order_blocks = []
        
        for i in range(2, len(candles)):
            # Look for strong impulsive candles
            current = candles[i]
            prev = candles[i-1]
            prev2 = candles[i-2]
            
            # Bullish Order Block: Strong up move
            if (current.close > prev.close and prev.close > prev2.close and
                current.high > prev.high and prev.high > prev2.high):
                
                # Check for impulsive characteristics
                body_ratio = abs(current.close - current.open) / (current.high - current.low)
                if body_ratio > 0.6:  # Strong candle
                    ob_candle = prev2  # Order block is the candle before impulse
                    order_blocks.append(OrderBlock(
                        timestamp=ob_candle.timestamp,
                        high=max(ob_candle.open, ob_candle.close),
                        low=min(ob_candle.open, ob_candle.close),
                        open_price=ob_candle.open,
                        close_price=ob_candle.close,
                        is_bullish=ob_candle.close > ob_candle.open,
                        candle_index=i-2,
                        strength=body_ratio
                    ))
            
            # Bearish Order Block: Strong down move
            elif (current.close < prev.close and prev.close < prev2.close and
                  current.low < prev.low and prev.low < prev2.low):
                
                body_ratio = abs(current.close - current.open) / (current.high - current.low)
                if body_ratio > 0.6:
                    ob_candle = prev2
                    order_blocks.append(OrderBlock(
                        timestamp=ob_candle.timestamp,
                        high=max(ob_candle.open, ob_candle.close),
                        low=min(ob_candle.open, ob_candle.close),
                        open_price=ob_candle.open,
                        close_price=ob_candle.close,
                        is_bullish=ob_candle.close > ob_candle.open,
                        candle_index=i-2,
                        strength=body_ratio
                    ))
        
        return order_blocks
    
    def detect_fvg(self, candles: List[Candle]) -> List[FairValueGap]:
        """Detect Fair Value Gaps (imbalances)."""
        fvg_list = []
        
        for i in range(2, len(candles)):
            candle1 = candles[i-2]
            candle2 = candles[i-1]
            candle3 = candles[i]
            
            # Bullish FVG: Gap between candle1 high and candle3 low
            if candle1.high < candle3.low:
                gap_size = candle3.low - candle1.high
                if gap_size > self.config.FVG_TOLERANCE:
                    fvg = FairValueGap(
                        timestamp=candle2.timestamp,
                        top=candle3.low,
                        bottom=candle1.high,
                        mid=(candle1.high + candle3.low) / 2,
                        is_bullish=True,
                        candle_index=i-1
                    )
                    fvg_list.append(fvg)
            
            # Bearish FVG: Gap between candle1 low and candle3 high
            elif candle1.low > candle3.high:
                gap_size = candle1.low - candle3.high
                if gap_size > self.config.FVG_TOLERANCE:
                    fvg = FairValueGap(
                        timestamp=candle2.timestamp,
                        top=candle1.low,
                        bottom=candle3.high,
                        mid=(candle1.low + candle3.high) / 2,
                        is_bullish=False,
                        candle_index=i-1
                    )
                    fvg_list.append(fvg)
        
        return fvg_list
    
    def detect_breakers(self, candles: List[Candle], order_blocks: List[OrderBlock]) -> List[Breaker]:
        """Detect Breaker zones (invalidated and retested Order Blocks)."""
        breakers = []
        
        for ob in order_blocks:
            # Check if Order Block was invalidated
            for i in range(ob.candle_index + 1, len(candles)):
                candle = candles[i]
                
                # Bullish OB invalidated if price goes below
                if ob.is_bullish and candle.low < ob.low:
                    # Look for retest after invalidation
                    for j in range(i + 1, min(i + 20, len(candles))):
                        retest_candle = candles[j]
                        if (retest_candle.high > ob.high and 
                            retest_candle.close < retest_candle.open):  # Bearish rejection
                            breakers.append(Breaker(
                                timestamp=retest_candle.timestamp,
                                high=ob.high,
                                low=ob.low,
                                original_ob_high=ob.high,
                                original_ob_low=ob.low,
                                candle_index=j
                            ))
                            break
                
                # Bearish OB invalidated if price goes above
                elif not ob.is_bullish and candle.high > ob.high:
                    # Look for retest after invalidation
                    for j in range(i + 1, min(i + 20, len(candles))):
                        retest_candle = candles[j]
                        if (retest_candle.low < ob.low and 
                            retest_candle.close > retest_candle.open):  # Bullish rejection
                            breakers.append(Breaker(
                                timestamp=retest_candle.timestamp,
                                high=ob.high,
                                low=ob.low,
                                original_ob_high=ob.high,
                                original_ob_low=ob.low,
                                candle_index=j
                            ))
                            break
        
        return breakers
    
    def detect_rejection_blocks(self, candles: List[Candle]) -> List[POIResult]:
        """Detect Rejection Blocks (simplified)."""
        rb_list = []
        
        for i in range(1, len(candles) - 1):
            current = candles[i]
            next_candle = candles[i + 1]
            
            # Bullish Rejection Block: Strong rejection at top
            if (current.high > current.open and current.close < current.open and
                next_candle.low < current.low):
                
                wick_ratio = (current.high - max(current.open, current.close)) / (current.high - current.low)
                if wick_ratio > 0.5:  # Long upper wick
                    rb_list.append(POIResult(
                        poi_type="RB",
                        zone_high=current.high,
                        zone_low=current.low,
                        timestamp=current.timestamp,
                        candle_index=i,
                        is_bullish=False,
                        strength=wick_ratio,
                        details={"wick_ratio": wick_ratio}
                    ))
            
            # Bearish Rejection Block: Strong rejection at bottom
            elif (current.low < current.open and current.close > current.open and
                  next_candle.high > current.high):
                
                wick_ratio = (min(current.open, current.close) - current.low) / (current.high - current.low)
                if wick_ratio > 0.5:  # Long lower wick
                    rb_list.append(POIResult(
                        poi_type="RB",
                        zone_high=current.high,
                        zone_low=current.low,
                        timestamp=current.timestamp,
                        candle_index=i,
                        is_bullish=True,
                        strength=wick_ratio,
                        details={"wick_ratio": wick_ratio}
                    ))
        
        return rb_list
    
    def get_all_pois(self, candles: List[Candle]) -> List[POIResult]:
        """Get all Points of Interest."""
        pois = []
        
        # Order Blocks
        order_blocks = self.detect_order_blocks(candles)
        for ob in order_blocks:
            pois.append(POIResult(
                poi_type="OB",
                zone_high=ob.high,
                zone_low=ob.low,
                timestamp=ob.timestamp,
                candle_index=ob.candle_index,
                is_bullish=ob.is_bullish,
                strength=ob.strength,
                details={
                    "open": ob.open_price,
                    "close": ob.close_price
                }
            ))
        
        # Fair Value Gaps
        fvg_list = self.detect_fvg(candles)
        for fvg in fvg_list:
            pois.append(POIResult(
                poi_type="FVG",
                zone_high=fvg.top,
                zone_low=fvg.bottom,
                timestamp=fvg.timestamp,
                candle_index=fvg.candle_index,
                is_bullish=fvg.is_bullish,
                details={"mid": fvg.mid, "fill_percentage": fvg.fill_percentage}
            ))
        
        # Breakers
        breakers = self.detect_breakers(candles, order_blocks)
        for breaker in breakers:
            pois.append(POIResult(
                poi_type="BREAKER",
                zone_high=breaker.high,
                zone_low=breaker.low,
                timestamp=breaker.timestamp,
                candle_index=breaker.candle_index,
                is_bullish=False,  # Default to bearish context
                details={
                    "original_ob_high": breaker.original_ob_high,
                    "original_ob_low": breaker.original_ob_low
                }
            ))
        
        # Rejection Blocks
        rb_list = self.detect_rejection_blocks(candles)
        pois.extend(rb_list)
        
        # Sort by timestamp (newest first) and return
        pois.sort(key=lambda x: x.timestamp, reverse=True)
        return pois[:20]  # Return up to 20 most recent POIs
