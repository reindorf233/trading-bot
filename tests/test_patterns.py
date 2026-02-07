import pytest
from datetime import datetime
from bot.providers.base import Candle
from bot.analysis.confirmation import ConfirmationDetector

class TestConfirmationPatterns:
    """Test confirmation pattern detection."""
    
    def create_candle(self, timestamp, open_price, high, low, close):
        """Helper to create test candle."""
        return Candle(
            timestamp=timestamp,
            open=open_price,
            high=high,
            low=low,
            close=close
        )
    
    def test_morning_star_detection(self):
        """Test Morning Star pattern detection."""
        detector = ConfirmationDetector()
        
        # Create Morning Star pattern
        candles = [
            self.create_candle(datetime(2024, 1, 1, 10, 0), 1.1020, 1.1030, 1.1010, 1.1015),  # Bearish
            self.create_candle(datetime(2024, 1, 1, 10, 30), 1.1015, 1.1020, 1.1010, 1.1012),  # Small body
            self.create_candle(datetime(2024, 1, 1, 11, 0), 1.1012, 1.1025, 1.1010, 1.1022),  # Bullish
        ]
        
        patterns = detector.detect_morning_star(candles)
        
        assert len(patterns) == 1
        pattern = patterns[0]
        assert pattern.pattern_type == "MORNING_STAR"
        assert pattern.is_bullish == True
        assert pattern.confidence > 0
    
    def test_evening_star_detection(self):
        """Test Evening Star pattern detection."""
        detector = ConfirmationDetector()
        
        # Create Evening Star pattern
        candles = [
            self.create_candle(datetime(2024, 1, 1, 10, 0), 1.1010, 1.1020, 1.1000, 1.1015),  # Bullish
            self.create_candle(datetime(2024, 1, 1, 10, 30), 1.1015, 1.1020, 1.1010, 1.1012),  # Small body
            self.create_candle(datetime(2024, 1, 1, 11, 0), 1.1012, 1.1018, 1.1000, 1.1005),  # Bearish
        ]
        
        patterns = detector.detect_evening_star(candles)
        
        assert len(patterns) == 1
        pattern = patterns[0]
        assert pattern.pattern_type == "EVENING_STAR"
        assert pattern.is_bullish == False
        assert pattern.confidence > 0
    
    def test_break_entry_bullish(self):
        """Test bullish break entry pattern."""
        detector = ConfirmationDetector()
        
        # Create break entry pattern
        candles = [
            self.create_candle(datetime(2024, 1, 1, 9, 0), 1.1000, 1.1010, 1.0990, 1.1005),
            self.create_candle(datetime(2024, 1, 1, 9, 30), 1.1005, 1.1015, 1.0995, 1.1010),
            self.create_candle(datetime(2024, 1, 1, 10, 0), 1.1010, 1.1020, 1.1000, 1.1015),
            self.create_candle(datetime(2024, 1, 1, 10, 30), 1.1015, 1.1025, 1.1005, 1.1020),
            self.create_candle(datetime(2024, 1, 1, 11, 0), 1.1020, 1.1035, 1.1015, 1.1032),  # Break above high
            self.create_candle(datetime(2024, 1, 1, 11, 30), 1.1032, 1.1038, 1.1020, 1.1025),  # Retest
            self.create_candle(datetime(2024, 1, 1, 12, 0), 1.1025, 1.1030, 1.1022, 1.1028),  # Bullish rejection
        ]
        
        patterns = detector.detect_break_entry(candles)
        
        # Should detect bullish break entry
        bullish_patterns = [p for p in patterns if p.is_bullish]
        assert len(bullish_patterns) >= 1
        
        pattern = bullish_patterns[0]
        assert pattern.pattern_type == "BREAK_ENTRY"
        assert pattern.is_bullish == True
    
    def test_break_entry_bearish(self):
        """Test bearish break entry pattern."""
        detector = ConfirmationDetector()
        
        # Create bearish break entry pattern
        candles = [
            self.create_candle(datetime(2024, 1, 1, 9, 0), 1.1030, 1.1040, 1.1020, 1.1025),
            self.create_candle(datetime(2024, 1, 1, 9, 30), 1.1025, 1.1030, 1.1010, 1.1015),
            self.create_candle(datetime(2024, 1, 1, 10, 0), 1.1015, 1.1020, 1.1000, 1.1005),
            self.create_candle(datetime(2024, 1, 1, 10, 30), 1.1005, 1.1010, 1.0990, 1.0995),
            self.create_candle(datetime(2024, 1, 1, 11, 0), 1.0995, 1.1000, 1.0980, 1.0985),  # Break below low
            self.create_candle(datetime(2024, 1, 1, 11, 30), 1.0985, 1.0995, 1.0980, 1.0988),  # Retest
            self.create_candle(datetime(2024, 1, 1, 12, 0), 1.0988, 1.0992, 1.0980, 1.0982),  # Bearish rejection
        ]
        
        patterns = detector.detect_break_entry(candles)
        
        # Should detect bearish break entry
        bearish_patterns = [p for p in patterns if not p.is_bullish]
        assert len(bearish_patterns) >= 1
        
        pattern = bearish_patterns[0]
        assert pattern.pattern_type == "BREAK_ENTRY"
        assert pattern.is_bullish == False
    
    def test_rejection_candle_upper_wick(self):
        """Test rejection candle with long upper wick."""
        detector = ConfirmationDetector()
        
        # Create candle with long upper wick
        candles = [
            self.create_candle(datetime(2024, 1, 1, 10, 0), 1.1000, 1.1030, 1.0995, 1.1005),  # Long upper wick
        ]
        
        patterns = detector.detect_rejection_candle(candles)
        
        assert len(patterns) == 1
        pattern = patterns[0]
        assert pattern.pattern_type == "REJECTION"
        assert pattern.is_bullish == False  # Upper rejection is bearish
        assert pattern.confidence > 0.5  # Long wick should give high confidence
    
    def test_rejection_candle_lower_wick(self):
        """Test rejection candle with long lower wick."""
        detector = ConfirmationDetector()
        
        # Create candle with long lower wick
        candles = [
            self.create_candle(datetime(2024, 1, 1, 10, 0), 1.1005, 1.1010, 1.0970, 1.1000),  # Long lower wick
        ]
        
        patterns = detector.detect_rejection_candle(candles)
        
        assert len(patterns) == 1
        pattern = patterns[0]
        assert pattern.pattern_type == "REJECTION"
        assert pattern.is_bullish == True  # Lower rejection is bullish
        assert pattern.confidence > 0.5  # Long wick should give high confidence
    
    def test_bias_filtering(self):
        """Test that patterns are filtered by bias."""
        detector = ConfirmationDetector()
        
        # Create mixed patterns
        candles = [
            # Morning Star (bullish)
            self.create_candle(datetime(2024, 1, 1, 10, 0), 1.1020, 1.1030, 1.1010, 1.1015),
            self.create_candle(datetime(2024, 1, 1, 10, 30), 1.1015, 1.1020, 1.1010, 1.1012),
            self.create_candle(datetime(2024, 1, 1, 11, 0), 1.1012, 1.1025, 1.1010, 1.1022),
            # Evening Star (bearish)
            self.create_candle(datetime(2024, 1, 1, 12, 0), 1.1010, 1.1020, 1.1000, 1.1015),
            self.create_candle(datetime(2024, 1, 1, 12, 30), 1.1015, 1.1020, 1.1010, 1.1012),
            self.create_candle(datetime(2024, 1, 1, 13, 0), 1.1012, 1.1018, 1.1000, 1.1005),
        ]
        
        # Test LONG bias - should only return bullish patterns
        long_patterns = detector.get_confirmations(candles, "LONG")
        assert all(p.is_bullish for p in long_patterns)
        
        # Test SHORT bias - should only return bearish patterns
        short_patterns = detector.get_confirmations(candles, "SHORT")
        assert all(not p.is_bullish for p in short_patterns)
        
        # Test NEUTRAL bias - should return all patterns
        neutral_patterns = detector.get_confirmations(candles, "NEUTRAL")
        assert len(neutral_patterns) >= len(long_patterns) and len(neutral_patterns) >= len(short_patterns)
