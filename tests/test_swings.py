import pytest
from datetime import datetime
from bot.providers.base import Candle
from bot.analysis.swings import SwingDetector, SwingPoint

class TestSwingDetection:
    """Test swing point detection."""
    
    def create_candle(self, timestamp, open_price, high, low, close):
        """Helper to create test candle."""
        return Candle(
            timestamp=timestamp,
            open=open_price,
            high=high,
            low=low,
            close=close
        )
    
    def test_swing_high_detection(self):
        """Test swing high detection."""
        detector = SwingDetector(lookback=2)
        
        # Create candles with clear swing high
        candles = [
            self.create_candle(datetime(2024, 1, 1, 10, 0), 1.1000, 1.1010, 1.0990, 1.1005),
            self.create_candle(datetime(2024, 1, 1, 10, 30), 1.1005, 1.1020, 1.1000, 1.1015),
            self.create_candle(datetime(2024, 1, 1, 11, 0), 1.1015, 1.1030, 1.1010, 1.1025),  # Swing high
            self.create_candle(datetime(2024, 1, 1, 11, 30), 1.1025, 1.1028, 1.1015, 1.1020),
            self.create_candle(datetime(2024, 1, 1, 12, 0), 1.1020, 1.1025, 1.1010, 1.1015)
        ]
        
        swings = detector.detect_swings(candles)
        
        # Should detect the swing high at index 2
        swing_highs = [s for s in swings if s.is_high]
        assert len(swing_highs) == 1
        assert swing_highs[0].price == 1.1030
        assert swing_highs[0].candle_index == 2
    
    def test_swing_low_detection(self):
        """Test swing low detection."""
        detector = SwingDetector(lookback=2)
        
        # Create candles with clear swing low
        candles = [
            self.create_candle(datetime(2024, 1, 1, 10, 0), 1.1020, 1.1030, 1.1010, 1.1025),
            self.create_candle(datetime(2024, 1, 1, 10, 30), 1.1025, 1.1030, 1.1005, 1.1010),
            self.create_candle(datetime(2024, 1, 1, 11, 0), 1.1010, 1.1015, 1.0990, 1.0995),  # Swing low
            self.create_candle(datetime(2024, 1, 1, 11, 30), 1.0995, 1.1005, 1.0992, 1.1000),
            self.create_candle(datetime(2024, 1, 1, 12, 0), 1.1000, 1.1010, 1.0995, 1.1005)
        ]
        
        swings = detector.detect_swings(candles)
        
        # Should detect the swing low at index 2
        swing_lows = [s for s in swings if not s.is_high]
        assert len(swing_lows) == 1
        assert swing_lows[0].price == 1.0990
        assert swing_lows[0].candle_index == 2
    
    def test_multiple_swings(self):
        """Test detection of multiple swing points."""
        detector = SwingDetector(lookback=2)
        
        # Create candles with multiple swings
        candles = [
            self.create_candle(datetime(2024, 1, 1, 9, 0), 1.1000, 1.1010, 1.0990, 1.1005),
            self.create_candle(datetime(2024, 1, 1, 9, 30), 1.1005, 1.1020, 1.1000, 1.1015),
            self.create_candle(datetime(2024, 1, 1, 10, 0), 1.1015, 1.1030, 1.1010, 1.1025),  # Swing high
            self.create_candle(datetime(2024, 1, 1, 10, 30), 1.1025, 1.1028, 1.1015, 1.1020),
            self.create_candle(datetime(2024, 1, 1, 11, 0), 1.1020, 1.1025, 1.0990, 1.0995),  # Swing low
            self.create_candle(datetime(2024, 1, 1, 11, 30), 1.0995, 1.1005, 1.0992, 1.1000),
            self.create_candle(datetime(2024, 1, 1, 12, 0), 1.1000, 1.1010, 1.0995, 1.1005)
        ]
        
        swings = detector.detect_swings(candles)
        
        # Should detect both swing high and swing low
        assert len(swings) == 2
        
        swing_highs = [s for s in swings if s.is_high]
        swing_lows = [s for s in swings if not s.is_high]
        
        assert len(swing_highs) == 1
        assert len(swing_lows) == 1
        assert swing_highs[0].price == 1.1030
        assert swing_lows[0].price == 1.0990
    
    def test_insufficient_candles(self):
        """Test swing detection with insufficient candles."""
        detector = SwingDetector(lookback=3)
        
        # Create fewer candles than needed
        candles = [
            self.create_candle(datetime(2024, 1, 1, 10, 0), 1.1000, 1.1010, 1.0990, 1.1005),
            self.create_candle(datetime(2024, 1, 1, 10, 30), 1.1005, 1.1020, 1.1000, 1.1015),
            self.create_candle(datetime(2024, 1, 1, 11, 0), 1.1015, 1.1030, 1.1010, 1.1025)
        ]
        
        swings = detector.detect_swings(candles)
        
        # Should not detect any swings with insufficient data
        assert len(swings) == 0
    
    def test_equal_highs_no_swing(self):
        """Test that equal highs don't create swing points."""
        detector = SwingDetector(lookback=2)
        
        # Create candles with equal highs
        candles = [
            self.create_candle(datetime(2024, 1, 1, 10, 0), 1.1000, 1.1020, 1.0990, 1.1005),
            self.create_candle(datetime(2024, 1, 1, 10, 30), 1.1005, 1.1020, 1.1000, 1.1015),
            self.create_candle(datetime(2024, 1, 1, 11, 0), 1.1015, 1.1020, 1.1010, 1.1025),  # Same high
            self.create_candle(datetime(2024, 1, 1, 11, 30), 1.1025, 1.1028, 1.1015, 1.1020),
            self.create_candle(datetime(2024, 1, 1, 12, 0), 1.1020, 1.1025, 1.1010, 1.1015)
        ]
        
        swings = detector.detect_swings(candles)
        
        # Should not detect swing high due to equal highs
        swing_highs = [s for s in swings if s.is_high]
        assert len(swing_highs) == 0
