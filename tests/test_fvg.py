import pytest
from datetime import datetime
from bot.providers.base import Candle
from bot.analysis.poi import POIDetector

class TestFVGDetection:
    """Test Fair Value Gap detection."""
    
    def create_candle(self, timestamp, open_price, high, low, close):
        """Helper to create test candle."""
        return Candle(
            timestamp=timestamp,
            open=open_price,
            high=high,
            low=low,
            close=close
        )
    
    def test_bullish_fvg_detection(self):
        """Test bullish Fair Value Gap detection."""
        detector = POIDetector()
        
        # Create candles with bullish FVG (actual gap)
        candles = [
            self.create_candle(datetime(2024, 1, 1, 10, 0), 1.1000, 1.1010, 1.0990, 1.1005),  # candle1
            self.create_candle(datetime(2024, 1, 1, 10, 30), 1.1005, 1.1020, 1.1000, 1.1015),  # candle2
            self.create_candle(datetime(2024, 1, 1, 11, 0), 1.1015, 1.1035, 1.1020, 1.1025)    # candle3 - gap from 1.1010 to 1.1020
        ]
        
        fvg_list = detector.detect_fvg(candles)
        
        assert len(fvg_list) == 1
        fvg = fvg_list[0]
        assert fvg.is_bullish == True
        assert fvg.bottom == 1.1010  # candle1.high
        assert fvg.top == 1.1020     # candle3.low
    
    def test_bearish_fvg_detection(self):
        """Test bearish Fair Value Gap detection."""
        detector = POIDetector()
        
        # Create candles with bearish FVG (actual gap)
        candles = [
            self.create_candle(datetime(2024, 1, 1, 10, 0), 1.1030, 1.1040, 1.1020, 1.1035),  # candle1
            self.create_candle(datetime(2024, 1, 1, 10, 30), 1.1035, 1.1040, 1.1015, 1.1020), # candle2
            self.create_candle(datetime(2024, 1, 1, 11, 0), 1.0980, 1.0990, 1.0975, 1.0980)   # candle3 - high is 1.0990, creating gap from 1.1020 to 1.0990
        ]
        
        fvg_list = detector.detect_fvg(candles)
        
        assert len(fvg_list) == 1
        fvg = fvg_list[0]
        assert fvg.is_bullish == False
        assert fvg.top == 1.1020     # candle1.low
        assert fvg.bottom == 1.0990  # candle3.high
    
    def test_no_fvg_detection(self):
        """Test no FVG when there's no gap."""
        detector = POIDetector()
        
        # Create candles without gap
        candles = [
            self.create_candle(datetime(2024, 1, 1, 10, 0), 1.1000, 1.1010, 1.0990, 1.1005),
            self.create_candle(datetime(2024, 1, 1, 10, 30), 1.1005, 1.1015, 1.0995, 1.1010),
            self.create_candle(datetime(2024, 1, 1, 11, 0), 1.1010, 1.1020, 1.1000, 1.1015)
        ]
        
        fvg_list = detector.detect_fvg(candles)
        
        assert len(fvg_list) == 0
    
    def test_small_gap_ignored(self):
        """Test that very small gaps are ignored."""
        detector = POIDetector()
        
        # Create candles with very small gap (below tolerance)
        candles = [
            self.create_candle(datetime(2024, 1, 1, 10, 0), 1.1000, 1.1001, 1.0999, 1.1000),
            self.create_candle(datetime(2024, 1, 1, 10, 30), 1.1000, 1.1002, 1.0998, 1.1001),
            self.create_candle(datetime(2024, 1, 1, 11, 0), 1.1001, 1.1002, 1.0999, 1.1001)
        ]
        
        fvg_list = detector.detect_fvg(candles)
        
        assert len(fvg_list) == 0
