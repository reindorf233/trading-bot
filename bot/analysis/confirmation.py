from typing import List, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel

from ..providers.base import Candle

class ConfirmationPattern(BaseModel):
    """Confirmation pattern result."""
    pattern_type: str  # "MORNING_STAR", "EVENING_STAR", "BREAK_ENTRY", "MSS_BB", "REJECTION"
    timestamp: datetime
    price: float
    candle_index: int
    is_bullish: bool
    confidence: float = 1.0
    details: dict = {}

class ConfirmationDetector:
    """Detect confirmation patterns on 5M timeframe."""
    
    def detect_morning_star(self, candles: List[Candle]) -> List[ConfirmationPattern]:
        """Detect Morning Star pattern (bullish reversal)."""
        patterns = []
        
        for i in range(2, len(candles)):
            candle1 = candles[i-2]  # First bearish candle
            candle2 = candles[i-1]  # Small body candle
            candle3 = candles[i]    # Bullish candle
            
            # Check pattern criteria
            if (candle1.close < candle1.open and  # Bearish first candle
                candle2.high < max(candle1.open, candle1.close) and  # Small body below first candle
                candle2.low > min(candle1.open, candle1.close) and
                candle3.close > candle3.open and  # Bullish third candle
                candle3.close > (candle1.open + candle1.close) / 2):  # Recovery
                
                # Calculate confidence based on body sizes
                body1_size = abs(candle1.close - candle1.open)
                body2_size = abs(candle2.close - candle2.open)
                body3_size = abs(candle3.close - candle3.open)
                
                confidence = min(1.0, (body3_size / max(body1_size, 0.0001)) * 
                              (1.0 - body2_size / max(body1_size, 0.0001)))
                
                patterns.append(ConfirmationPattern(
                    pattern_type="MORNING_STAR",
                    timestamp=candle3.timestamp,
                    price=candle3.close,
                    candle_index=i,
                    is_bullish=True,
                    confidence=confidence,
                    details={
                        "candle1": {"open": candle1.open, "close": candle1.close},
                        "candle2": {"open": candle2.open, "close": candle2.close},
                        "candle3": {"open": candle3.open, "close": candle3.close}
                    }
                ))
        
        return patterns
    
    def detect_evening_star(self, candles: List[Candle]) -> List[ConfirmationPattern]:
        """Detect Evening Star pattern (bearish reversal)."""
        patterns = []
        
        for i in range(2, len(candles)):
            candle1 = candles[i-2]  # First bullish candle
            candle2 = candles[i-1]  # Small body candle
            candle3 = candles[i]    # Bearish candle
            
            # Check pattern criteria
            if (candle1.close > candle1.open and  # Bullish first candle
                candle2.high < max(candle1.open, candle1.close) and  # Small body below first candle
                candle2.low > min(candle1.open, candle1.close) and
                candle3.close < candle3.open and  # Bearish third candle
                candle3.close < (candle1.open + candle1.close) / 2):  # Recovery
                
                # Calculate confidence
                body1_size = abs(candle1.close - candle1.open)
                body2_size = abs(candle2.close - candle2.open)
                body3_size = abs(candle3.close - candle3.open)
                
                confidence = min(1.0, (body3_size / max(body1_size, 0.0001)) * 
                              (1.0 - body2_size / max(body1_size, 0.0001)))
                
                patterns.append(ConfirmationPattern(
                    pattern_type="EVENING_STAR",
                    timestamp=candle3.timestamp,
                    price=candle3.close,
                    candle_index=i,
                    is_bullish=False,
                    confidence=confidence,
                    details={
                        "candle1": {"open": candle1.open, "close": candle1.close},
                        "candle2": {"open": candle2.open, "close": candle2.close},
                        "candle3": {"open": candle3.open, "close": candle3.close}
                    }
                ))
        
        return patterns
    
    def detect_break_entry(self, candles: List[Candle]) -> List[ConfirmationPattern]:
        """Detect Break Entry pattern (break and retest)."""
        patterns = []
        
        for i in range(10, len(candles)):
            current = candles[i]
            
            # Look for recent structure break
            recent_candles = candles[i-10:i]
            
            # Find recent high/low structure
            recent_high = max(candle.high for candle in recent_candles)
            recent_low = min(candle.low for candle in recent_candles)
            
            # Bullish break entry: Break above high, then retest
            if current.close > recent_high:
                # Look for retest in next few candles
                for j in range(i + 1, min(i + 8, len(candles))):
                    retest_candle = candles[j]
                    if (abs(retest_candle.low - recent_high) < 0.0001 and
                        retest_candle.close > retest_candle.open):  # Bullish rejection
                        
                        patterns.append(ConfirmationPattern(
                            pattern_type="BREAK_ENTRY",
                            timestamp=retest_candle.timestamp,
                            price=retest_candle.close,
                            candle_index=j,
                            is_bullish=True,
                            confidence=0.8,
                            details={
                                "break_level": recent_high,
                                "break_price": current.close,
                                "retest_price": retest_candle.close
                            }
                        ))
                        break
            
            # Bearish break entry: Break below low, then retest
            elif current.close < recent_low:
                # Look for retest in next few candles
                for j in range(i + 1, min(i + 8, len(candles))):
                    retest_candle = candles[j]
                    if (abs(retest_candle.high - recent_low) < 0.0001 and
                        retest_candle.close < retest_candle.open):  # Bearish rejection
                        
                        patterns.append(ConfirmationPattern(
                            pattern_type="BREAK_ENTRY",
                            timestamp=retest_candle.timestamp,
                            price=retest_candle.close,
                            candle_index=j,
                            is_bullish=False,
                            confidence=0.8,
                            details={
                                "break_level": recent_low,
                                "break_price": current.close,
                                "retest_price": retest_candle.close
                            }
                        ))
                        break
        
        return patterns
    
    def detect_rejection_candle(self, candles: List[Candle]) -> List[ConfirmationPattern]:
        """Detect strong rejection candles."""
        patterns = []
        
        for i, candle in enumerate(candles):
            # Calculate wick ratios
            upper_wick = candle.high - max(candle.open, candle.close)
            lower_wick = min(candle.open, candle.close) - candle.low
            body = abs(candle.close - candle.open)
            total_range = candle.high - candle.low
            
            if total_range == 0:
                continue
            
            upper_wick_ratio = upper_wick / total_range
            lower_wick_ratio = lower_wick / total_range
            body_ratio = body / total_range
            
            # Strong upper rejection (bearish)
            if upper_wick_ratio > 0.6 and body_ratio < 0.4:
                patterns.append(ConfirmationPattern(
                    pattern_type="REJECTION",
                    timestamp=candle.timestamp,
                    price=candle.close,
                    candle_index=i,
                    is_bullish=False,
                    confidence=upper_wick_ratio,
                    details={
                        "wick_type": "upper",
                        "wick_ratio": upper_wick_ratio,
                        "body_ratio": body_ratio
                    }
                ))
            
            # Strong lower rejection (bullish)
            elif lower_wick_ratio > 0.6 and body_ratio < 0.4:
                patterns.append(ConfirmationPattern(
                    pattern_type="REJECTION",
                    timestamp=candle.timestamp,
                    price=candle.close,
                    candle_index=i,
                    is_bullish=True,
                    confidence=lower_wick_ratio,
                    details={
                        "wick_type": "lower",
                        "wick_ratio": lower_wick_ratio,
                        "body_ratio": body_ratio
                    }
                ))
        
        return patterns
    
    def get_confirmations(self, candles: List[Candle], bias: str) -> List[ConfirmationPattern]:
        """Get all confirmation patterns filtered by bias."""
        all_patterns = []
        
        # Detect all pattern types
        all_patterns.extend(self.detect_morning_star(candles))
        all_patterns.extend(self.detect_evening_star(candles))
        all_patterns.extend(self.detect_break_entry(candles))
        all_patterns.extend(self.detect_rejection_candle(candles))
        
        # Filter by bias
        if bias == "LONG":
            filtered = [p for p in all_patterns if p.is_bullish]
        elif bias == "SHORT":
            filtered = [p for p in all_patterns if not p.is_bullish]
        else:
            filtered = all_patterns
        
        # Sort by timestamp (newest first) and confidence
        filtered.sort(key=lambda x: (x.timestamp, x.confidence), reverse=True)
        return filtered[:10]  # Return up to 10 most recent confirmations
