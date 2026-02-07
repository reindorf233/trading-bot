import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel

from ..providers.base import MarketDataProvider, Candle
from ..config import Config
from .structure import StructureAnalyzer
from .poi import POIDetector, POIResult
from .liquidity import LiquidityDetector, LiquiditySweep
from .confirmation import ConfirmationDetector, ConfirmationPattern
from .ai_verifier import AIVerifier, AIVerification

logger = logging.getLogger(__name__)

class SignalResult(BaseModel):
    """Complete signal analysis result."""
    symbol: str
    timestamp: datetime
    decision: str  # "BUY", "SELL", "NO_TRADE"
    confidence: int  # 0-100
    bias: str  # "LONG", "SHORT", "NEUTRAL"
    
    # 4H Analysis
    trend_4h: str
    bos_mss_4h: str
    swing_high_4h: Optional[float]
    swing_low_4h: Optional[float]
    
    # 30M Analysis  
    poi_type: Optional[str]
    poi_zone: Optional[str]
    poi_strength: Optional[float]
    
    # Liquidity Analysis
    liquidity_sweep: bool
    sweep_details: Optional[Dict[str, Any]]
    
    # 5M Confirmation
    confirmation_pattern: Optional[str]
    confirmation_confidence: Optional[float]
    
    # AI Verification
    ai_reasons: Dict[str, str]
    missing_conditions: list[str]
    risk_notes: str
    
    # Trade Plan
    entry_zone: Optional[str]
    invalidation_level: Optional[str]
    target1: Optional[str]
    target2: Optional[str]

class SignalEngine:
    """Main signal analysis engine."""
    
    def __init__(self, data_provider: MarketDataProvider, config: Config):
        self.data_provider = data_provider
        self.config = config
        
        # Initialize analyzers
        self.structure_analyzer = StructureAnalyzer(config.SWING_LOOKBACK)
        self.poi_detector = POIDetector(config)
        self.liquidity_detector = LiquidityDetector(config)
        self.confirmation_detector = ConfirmationDetector()
        self.ai_verifier = AIVerifier(config)
    
    async def analyze_symbol(self, symbol: str) -> SignalResult:
        """Perform complete 3-timeframe analysis."""
        try:
            # Get data for all timeframes
            candles_4h = await self.data_provider.get_candles(symbol, "4H", 200)
            candles_30m = await self.data_provider.get_candles(symbol, "30M", 500)
            candles_5m = await self.data_provider.get_candles(symbol, "5M", 500)
            
            if not all([candles_4h, candles_30m, candles_5m]):
                raise ValueError(f"Insufficient data for {symbol}")
            
            logger.info(f"Analyzing {symbol} - 4H: {len(candles_4h)}, 30M: {len(candles_30m)}, 5M: {len(candles_5m)}")
            
            # Step 1: 4H Direction Analysis
            bias_4h, bos_mss_event = self.structure_analyzer.get_bias(candles_4h)
            structure_4h = self.structure_analyzer.swing_detector.analyze_structure(candles_4h)
            
            # Step 2: 30M POI Detection
            pois_30m = self.poi_detector.get_all_pois(candles_30m)
            best_poi = self._find_best_poi(pois_30m, bias_4h)
            
            # Step 3: Liquidity Sweep Analysis
            pools = self.liquidity_detector.find_liquidity_pools(candles_30m)
            sweeps = self.liquidity_detector.detect_sweeps(candles_30m, pools)
            relevant_sweep = self._find_relevant_sweep(sweeps, best_poi, candles_30m)
            
            # Step 4: 5M Confirmation
            confirmations = self.confirmation_detector.get_confirmations(candles_5m, bias_4h)
            best_confirmation = confirmations[0] if confirmations else None
            
            # Deterministic decision
            deterministic_decision = self._make_deterministic_decision(
                bias_4h, best_poi, relevant_sweep, best_confirmation
            )
            
            # Prepare data for AI verification
            analysis_data = self._prepare_analysis_data(
                symbol, bias_4h, structure_4h, best_poi, relevant_sweep, best_confirmation,
                bos_mss_event
            )
            
            # AI verification
            ai_verification = await self.ai_verifier.verify_signal(
                analysis_data, deterministic_decision
            )
            
            # Final decision (use AI if available, otherwise deterministic)
            final_decision = ai_verification.decision
            final_confidence = ai_verification.confidence
            
            # Generate trade plan
            trade_plan = self._generate_trade_plan(
                final_decision, best_poi, structure_4h, candles_30m
            )
            
            return SignalResult(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                decision=final_decision,
                confidence=final_confidence,
                bias=bias_4h,
                
                # 4H Analysis
                trend_4h=structure_4h.trend,
                bos_mss_4h=bos_mss_event.event_type if bos_mss_event else "NONE",
                swing_high_4h=structure_4h.last_swing_high.price if structure_4h.last_swing_high else None,
                swing_low_4h=structure_4h.last_swing_low.price if structure_4h.last_swing_low else None,
                
                # 30M Analysis
                poi_type=best_poi.poi_type if best_poi else None,
                poi_zone=f"{best_poi.zone_low:.5f}-{best_poi.zone_high:.5f}" if best_poi else None,
                poi_strength=best_poi.strength if best_poi else None,
                
                # Liquidity Analysis
                liquidity_sweep=relevant_sweep is not None,
                sweep_details={
                    "type": relevant_sweep.pool_type,
                    "price": relevant_sweep.pool_price,
                    "sweep_price": relevant_sweep.sweep_price
                } if relevant_sweep else None,
                
                # 5M Confirmation
                confirmation_pattern=best_confirmation.pattern_type if best_confirmation else None,
                confirmation_confidence=best_confirmation.confidence if best_confirmation else None,
                
                # AI Verification
                ai_reasons=ai_verification.reasons,
                missing_conditions=ai_verification.missing_conditions,
                risk_notes=ai_verification.risk_notes,
                
                # Trade Plan
                entry_zone=trade_plan.get("entry_zone"),
                invalidation_level=trade_plan.get("invalidation_level"),
                target1=trade_plan.get("target1"),
                target2=trade_plan.get("target2")
            )
            
        except Exception as e:
            logger.error(f"Analysis failed for {symbol}: {e}")
            return self._create_error_result(symbol, str(e))
    
    def _find_best_poi(self, pois: list[POIResult], bias: str) -> Optional[POIResult]:
        """Find the best POI aligned with bias."""
        if not pois:
            return None
        
        # Filter by bias alignment
        aligned_pois = []
        for poi in pois:
            if bias == "LONG" and poi.poi_type in ["OB", "FVG"] and poi.is_bullish:
                aligned_pois.append(poi)
            elif bias == "SHORT" and poi.poi_type in ["OB", "FVG"] and not poi.is_bullish:
                aligned_pois.append(poi)
        
        # If no aligned POIs, return the strongest recent one
        if not aligned_pois and pois:
            return pois[0]  # Most recent
        
        # Return the strongest aligned POI
        if aligned_pois:
            return max(aligned_pois, key=lambda x: x.strength)
        
        return None
    
    def _find_relevant_sweep(
        self, 
        sweeps: list[LiquiditySweep], 
        poi: Optional[POIResult],
        candles: list[Candle]
    ) -> Optional[LiquiditySweep]:
        """Find sweep relevant to POI."""
        if not poi or not sweeps:
            return None
        
        poi_price = (poi.zone_high + poi.zone_low) / 2
        return self.liquidity_detector.check_sweep_into_poi(
            candles, sweeps, poi_price, self.config.POI_PROXIMITY_CANDLES
        )
    
    def _make_deterministic_decision(
        self,
        bias: str,
        poi: Optional[POIResult],
        sweep: Optional[LiquiditySweep],
        confirmation: Optional[ConfirmationPattern]
    ) -> str:
        """Make deterministic decision based on strict rules."""
        
        # Rule 1: Need clear bias
        if bias not in ["LONG", "SHORT"]:
            return "NO_TRADE"
        
        # Rule 2: Need valid POI aligned with bias
        if not poi:
            return "NO_TRADE"
        
        if bias == "LONG" and not poi.is_bullish:
            return "NO_TRADE"
        
        if bias == "SHORT" and poi.is_bullish:
            return "NO_TRADE"
        
        # Rule 3: Need liquidity sweep
        if not sweep:
            return "NO_TRADE"
        
        # Rule 4: Need confirmation
        if not confirmation:
            return "NO_TRADE"
        
        # All rules passed - return bias-aligned decision
        return "BUY" if bias == "LONG" else "SELL"
    
    def _prepare_analysis_data(
        self,
        symbol: str,
        bias: str,
        structure: Any,
        poi: Optional[POIResult],
        sweep: Optional[LiquiditySweep],
        confirmation: Optional[ConfirmationPattern],
        bos_mss_event: Any
    ) -> Dict[str, Any]:
        """Prepare analysis data for AI verification."""
        return {
            "symbol": symbol,
            "4h_trend": structure.trend,
            "4h_bias": bias,
            "4h_last_event": bos_mss_event.event_type if bos_mss_event else "None",
            "4h_swing_high": structure.last_swing_high.price if structure.last_swing_high else None,
            "4h_swing_low": structure.last_swing_low.price if structure.last_swing_low else None,
            
            "30m_poi_type": poi.poi_type if poi else None,
            "30m_poi_zone": f"{poi.zone_low:.5f}-{poi.zone_high:.5f}" if poi else None,
            "30m_poi_strength": poi.strength if poi else None,
            
            "liquidity_sweep": sweep is not None,
            "swept_pool_type": sweep.pool_type if sweep else None,
            "sweep_price": sweep.pool_price if sweep else None,
            
            "5m_pattern": confirmation.pattern_type if confirmation else None,
            "5m_confidence": confirmation.confidence if confirmation else None,
            "5m_entry_price": confirmation.price if confirmation else None
        }
    
    def _generate_trade_plan(
        self,
        decision: str,
        poi: Optional[POIResult],
        structure: Any,
        candles: list[Candle]
    ) -> Dict[str, str]:
        """Generate basic trade plan."""
        if decision == "NO_TRADE" or not poi:
            return {}
        
        entry_zone = f"{poi.zone_low:.5f}-{poi.zone_high:.5f}"
        
        # Set invalidation based on POI
        if poi.is_bullish:
            invalidation = f"{poi.zone_low:.5f}"
        else:
            invalidation = f"{poi.zone_high:.5f}"
        
        # Target 1: Recent swing level
        target1 = None
        if structure.last_swing_high and decision == "BUY":
            target1 = f"{structure.last_swing_high.price:.5f}"
        elif structure.last_swing_low and decision == "SELL":
            target1 = f"{structure.last_swing_low.price:.5f}"
        
        # Target 2: 2R from entry
        entry_mid = (poi.zone_high + poi.zone_low) / 2
        risk = abs(entry_mid - float(invalidation))
        reward = risk * self.config.DEFAULT_RISK_R
        
        if decision == "BUY":
            target2 = f"{entry_mid + reward:.5f}"
        else:
            target2 = f"{entry_mid - reward:.5f}"
        
        return {
            "entry_zone": entry_zone,
            "invalidation_level": invalidation,
            "target1": target1,
            "target2": target2
        }
    
    def _create_error_result(self, symbol: str, error: str) -> SignalResult:
        """Create error result."""
        return SignalResult(
            symbol=symbol,
            timestamp=datetime.utcnow(),
            decision="NO_TRADE",
            confidence=0,
            bias="ERROR",
            
            trend_4h="ERROR",
            bos_mss_4h="ERROR",
            swing_high_4h=None,
            swing_low_4h=None,
            
            poi_type=None,
            poi_zone=None,
            poi_strength=None,
            
            liquidity_sweep=False,
            sweep_details=None,
            
            confirmation_pattern=None,
            confirmation_confidence=None,
            
            ai_reasons={"error": error},
            missing_conditions=["analysis_error"],
            risk_notes=f"Analysis failed: {error}",
            
            entry_zone=None,
            invalidation_level=None,
            target1=None,
            target2=None
        )
