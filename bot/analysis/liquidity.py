from typing import List, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel

from ..providers.base import Candle
from ..config import Config

class LiquidityPool(BaseModel):
    """Liquidity pool (equal highs/lows or range extremes)."""
    price_level: float
    touches: List[Tuple[datetime, int]]  # (timestamp, candle_index)
    pool_type: str  # "EQUAL_HIGHS", "EQUAL_LOWS", "RANGE_HIGH", "RANGE_LOW"
    strength: float = 1.0

class LiquiditySweep(BaseModel):
    """Liquidity sweep event."""
    timestamp: datetime
    sweep_price: float
    pool_price: float
    pool_type: str
    is_swept_up: bool
    is_swept_down: bool
    rejection_price: float
    candle_index: int
    proximity_to_poi: Optional[float] = None

class LiquidityDetector:
    """Detect liquidity pools and sweeps."""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
    
    def find_liquidity_pools(self, candles: List[Candle]) -> List[LiquidityPool]:
        """Find liquidity pools (equal highs/lows, range extremes)."""
        pools = []
        
        # Find equal highs
        high_touches = {}
        tolerance = self.config.LIQUIDITY_TOLERANCE
        
        for i, candle in enumerate(candles):
            # Group similar high prices
            for level in list(high_touches.keys()):
                if abs(candle.high - level) <= tolerance:
                    high_touches[level].append((candle.timestamp, i))
                    break
            else:
                high_touches[candle.high] = [(candle.timestamp, i)]
        
        # Filter for pools with multiple touches
        for level, touches in high_touches.items():
            if len(touches) >= 2:
                pools.append(LiquidityPool(
                    price_level=level,
                    touches=touches,
                    pool_type="EQUAL_HIGHS",
                    strength=len(touches)
                ))
        
        # Find equal lows
        low_touches = {}
        for i, candle in enumerate(candles):
            for level in list(low_touches.keys()):
                if abs(candle.low - level) <= tolerance:
                    low_touches[level].append((candle.timestamp, i))
                    break
            else:
                low_touches[candle.low] = [(candle.timestamp, i)]
        
        for level, touches in low_touches.items():
            if len(touches) >= 2:
                pools.append(LiquidityPool(
                    price_level=level,
                    touches=touches,
                    pool_type="EQUAL_LOWS",
                    strength=len(touches)
                ))
        
        # Find range extremes (recent swing highs/lows)
        if len(candles) >= 20:
            recent_candles = candles[:20]  # Most recent 20 candles
            
            # Range high
            range_high = max(candle.high for candle in recent_candles)
            high_candles = [c for c in recent_candles if abs(c.high - range_high) <= tolerance]
            if len(high_candles) >= 1:
                pools.append(LiquidityPool(
                    price_level=range_high,
                    pool_type="RANGE_HIGH",
                    touches=[(c.timestamp, i) for i, c in enumerate(recent_candles) if c in high_candles],
                    strength=1.0
                ))
            
            # Range low
            range_low = min(candle.low for candle in recent_candles)
            low_candles = [c for c in recent_candles if abs(c.low - range_low) <= tolerance]
            if len(low_candles) >= 1:
                pools.append(LiquidityPool(
                    price_level=range_low,
                    pool_type="RANGE_LOW",
                    touches=[(c.timestamp, i) for i, c in enumerate(recent_candles) if c in low_candles],
                    strength=1.0
                ))
        
        return pools
    
    def detect_sweeps(self, candles: List[Candle], pools: List[LiquidityPool]) -> List[LiquiditySweep]:
        """Detect liquidity sweeps into pools."""
        sweeps = []
        
        for pool in pools:
            # Get the most recent touch of this pool
            latest_touch = max(pool.touches, key=lambda x: x[1])  # (timestamp, index)
            latest_touch_index = latest_touch[1]
            
            # Look for sweep after the latest touch
            for i in range(latest_touch_index + 1, len(candles)):
                candle = candles[i]
                
                # Check for upward sweep (for low pools)
                if pool.pool_type in ["EQUAL_LOWS", "RANGE_LOW"]:
                    if candle.low < pool.price_level:
                        # Look for rejection (close back above)
                        for j in range(i, min(i + 5, len(candles))):
                            rejection_candle = candles[j]
                            if rejection_candle.close > pool.price_level:
                                sweeps.append(LiquiditySweep(
                                    timestamp=rejection_candle.timestamp,
                                    sweep_price=candle.low,
                                    pool_price=pool.price_level,
                                    pool_type=pool.pool_type,
                                    is_swept_up=True,
                                    is_swept_down=False,
                                    rejection_price=rejection_candle.close,
                                    candle_index=j
                                ))
                                break
                
                # Check for downward sweep (for high pools)
                elif pool.pool_type in ["EQUAL_HIGHS", "RANGE_HIGH"]:
                    if candle.high > pool.price_level:
                        # Look for rejection (close back below)
                        for j in range(i, min(i + 5, len(candles))):
                            rejection_candle = candles[j]
                            if rejection_candle.close < pool.price_level:
                                sweeps.append(LiquiditySweep(
                                    timestamp=rejection_candle.timestamp,
                                    sweep_price=candle.high,
                                    pool_price=pool.price_level,
                                    pool_type=pool.pool_type,
                                    is_swept_up=False,
                                    is_swept_down=True,
                                    rejection_price=rejection_candle.close,
                                    candle_index=j
                                ))
                                break
        
        # Sort by timestamp (newest first)
        sweeps.sort(key=lambda x: x.timestamp, reverse=True)
        return sweeps[:10]  # Return up to 10 most recent sweeps
    
    def check_sweep_into_poi(
        self, 
        candles: List[Candle], 
        sweeps: List[LiquiditySweep],
        poi_price: float,
        max_candles_away: int
    ) -> Optional[LiquiditySweep]:
        """Check if there's a sweep near a POI."""
        for sweep in sweeps:
            # Calculate distance between sweep and POI
            distance = abs(sweep.pool_price - poi_price)
            
            # Check if sweep is within acceptable distance
            if distance <= self.config.LIQUIDITY_TOLERANCE * 10:  # Allow some tolerance
                # Check if sweep happened recently enough
                for i, candle in enumerate(candles):
                    if candle.timestamp == sweep.timestamp:
                        # Check proximity in candle count
                        if i <= max_candles_away:
                            sweep.proximity_to_poi = distance
                            return sweep
                        break
        
        return None
