import pytest
from datetime import datetime
from bot.providers.base import Candle
from bot.analysis.structure import StructureAnalyzer

class TestBOSMSSDetection:
    """Test Break of Structure and Market Structure Shift detection."""
    
    def create_candle(self, timestamp, open_price, high, low, close):
        """Helper to create test candle."""
        return Candle(
            timestamp=timestamp,
            open=open_price,
            high=high,
            low=low,
            close=close
        )
    
    def test_bullish_bos_detection(self):
        """Test bullish Break of Structure detection."""
        analyzer = StructureAnalyzer()
        
        # Create candles with uptrend and BOS
        candles = [
            # Initial structure
            self.create_candle(datetime(2024, 1, 1, 8, 0), 1.1000, 1.1010, 1.0990, 1.1005),
            self.create_candle(datetime(2024, 1, 1, 8, 30), 1.1005, 1.1020, 1.1000, 1.1015),
            self.create_candle(datetime(2024, 1, 1, 9, 0), 1.1015, 1.1030, 1.1010, 1.1025),  # Swing high
            self.create_candle(datetime(2024, 1, 1, 9, 30), 1.1025, 1.1028, 1.1015, 1.1020),
            self.create_candle(datetime(2024, 1, 1, 10, 0), 1.1020, 1.1025, 1.1000, 1.1005),
            self.create_candle(datetime(2024, 1, 1, 10, 30), 1.1005, 1.1015, 1.0995, 1.1000),
            self.create_candle(datetime(2024, 1, 1, 11, 0), 1.1000, 1.1010, 1.0980, 1.0985),
            # BOS: Break above swing high
            self.create_candle(datetime(2024, 1, 1, 11, 30), 1.0985, 1.1035, 1.0980, 1.1032),  # Breaks above 1.1030
        ]
        
        events = analyzer.detect_bos_mss(candles)
        
        # Should detect bullish BOS
        bullish_events = [e for e in events if e.event_type == "BOS_UP"]
        assert len(bullish_events) >= 1
        
        bos_event = bullish_events[0]
        assert bos_event.event_type == "BOS_UP"
        assert bos_event.price > 1.1030  # Above swing high
        assert bos_event.swing_level == 1.1030
    
    def test_bearish_bos_detection(self):
        """Test bearish Break of Structure detection."""
        analyzer = StructureAnalyzer()
        
        # Create candles with downtrend and BOS
        candles = [
            # Initial structure
            self.create_candle(datetime(2024, 1, 1, 8, 0), 1.1030, 1.1040, 1.1020, 1.1035),
            self.create_candle(datetime(2024, 1, 1, 8, 30), 1.1035, 1.1040, 1.1010, 1.1015),
            self.create_candle(datetime(2024, 1, 1, 9, 0), 1.1015, 1.1020, 1.0990, 1.0995),  # Swing low
            self.create_candle(datetime(2024, 1, 1, 9, 30), 1.0995, 1.1005, 1.0990, 1.1000),
            self.create_candle(datetime(2024, 1, 1, 10, 0), 1.1000, 1.1010, 1.0995, 1.1005),
            self.create_candle(datetime(2024, 1, 1, 10, 30), 1.1005, 1.1015, 1.1000, 1.1010),
            self.create_candle(datetime(2024, 1, 1, 11, 0), 1.1010, 1.1020, 1.1005, 1.1015),
            # BOS: Break below swing low
            self.create_candle(datetime(2024, 1, 1, 11, 30), 1.1015, 1.1020, 1.0985, 1.0988),  # Breaks below 1.0990
        ]
        
        events = analyzer.detect_bos_mss(candles)
        
        # Should detect bearish BOS
        bearish_events = [e for e in events if e.event_type == "BOS_DOWN"]
        assert len(bearish_events) >= 1
        
        bos_event = bearish_events[0]
        assert bos_event.event_type == "BOS_DOWN"
        assert bos_event.price < 1.0990  # Below swing low
        assert bos_event.swing_level == 1.0990
    
    def test_mss_detection(self):
        """Test Market Structure Shift detection."""
        analyzer = StructureAnalyzer()
        
        # Create candles with downtrend followed by MSS (bullish reversal)
        candles = [
            # Downtrend structure
            self.create_candle(datetime(2024, 1, 1, 8, 0), 1.1030, 1.1040, 1.1020, 1.1025),
            self.create_candle(datetime(2024, 1, 1, 8, 30), 1.1025, 1.1030, 1.1005, 1.1010),
            self.create_candle(datetime(2024, 1, 1, 9, 0), 1.1010, 1.1015, 1.0990, 1.0995),  # Lower low
            self.create_candle(datetime(2024, 1, 1, 9, 30), 1.0995, 1.1005, 1.0990, 1.1000),
            self.create_candle(datetime(2024, 1, 1, 10, 0), 1.1000, 1.1010, 1.0985, 1.0990),  # Lower low
            self.create_candle(datetime(2024, 1, 1, 10, 30), 1.0990, 1.1000, 1.0980, 1.0985),
            self.create_candle(datetime(2024, 1, 1, 11, 0), 1.0985, 1.0995, 1.0975, 1.0980),
            # MSS: Break above recent low (against downtrend)
            self.create_candle(datetime(2024, 1, 1, 11, 30), 1.0980, 1.1000, 1.0978, 1.0998),  # Breaks above structure
        ]
        
        events = analyzer.detect_bos_mss(candles)
        
        # Should detect MSS
        mss_events = [e for e in events if e.event_type == "MSS_UP"]
        assert len(mss_events) >= 1
    
    def test_bias_determination(self):
        """Test bias determination from BOS/MSS."""
        analyzer = StructureAnalyzer()
        
        # Test bullish bias
        bullish_candles = [
            self.create_candle(datetime(2024, 1, 1, 8, 0), 1.1000, 1.1010, 1.0990, 1.1005),
            self.create_candle(datetime(2024, 1, 1, 8, 30), 1.1005, 1.1020, 1.1000, 1.1015),
            self.create_candle(datetime(2024, 1, 1, 9, 0), 1.1015, 1.1030, 1.1010, 1.1025),
            self.create_candle(datetime(2024, 1, 1, 9, 30), 1.1025, 1.1028, 1.1015, 1.1020),
            self.create_candle(datetime(2024, 1, 1, 10, 0), 1.1020, 1.1035, 1.1018, 1.1032),  # BOS
        ]
        
        bias, event = analyzer.get_bias(bullish_candles)
        assert bias == "LONG"
        assert event.event_type == "BOS_UP"
        
        # Test bearish bias
        bearish_candles = [
            self.create_candle(datetime(2024, 1, 1, 8, 0), 1.1030, 1.1040, 1.1020, 1.1035),
            self.create_candle(datetime(2024, 1, 1, 8, 30), 1.1035, 1.1040, 1.1010, 1.1015),
            self.create_candle(datetime(2024, 1, 1, 9, 0), 1.1015, 1.1020, 1.0990, 1.0995),
            self.create_candle(datetime(2024, 1, 1, 9, 30), 1.0995, 1.1005, 1.0990, 1.1000),
            self.create_candle(datetime(2024, 1, 1, 10, 0), 1.1000, 1.1005, 1.0985, 1.0988),  # BOS
        ]
        
        bias, event = analyzer.get_bias(bearish_candles)
        assert bias == "SHORT"
        assert event.event_type == "BOS_DOWN"
    
    def test_no_clear_bias(self):
        """Test bias determination with no clear structure."""
        analyzer = StructureAnalyzer()
        
        # Create ranging candles
        ranging_candles = [
            self.create_candle(datetime(2024, 1, 1, 8, 0), 1.1000, 1.1010, 1.0990, 1.1005),
            self.create_candle(datetime(2024, 1, 1, 8, 30), 1.1005, 1.1015, 1.0995, 1.1000),
            self.create_candle(datetime(2024, 1, 1, 9, 0), 1.1000, 1.1010, 1.0990, 1.1005),
            self.create_candle(datetime(2024, 1, 1, 9, 30), 1.1005, 1.1015, 1.0995, 1.1000),
            self.create_candle(datetime(2024, 1, 1, 10, 0), 1.1000, 1.1010, 1.0990, 1.1005),
        ]
        
        bias, event = analyzer.get_bias(ranging_candles)
        assert bias == "NEUTRAL"
        assert event is None
