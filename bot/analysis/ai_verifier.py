import json
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class AIVerification(BaseModel):
    """AI verification result."""
    decision: str  # "BUY", "SELL", "NO_TRADE"
    confidence: int  # 0-100
    reasons: Dict[str, str]
    missing_conditions: list[str]
    risk_notes: str

class AIVerifier:
    """AI-based rule verifier using LLM."""
    
    def __init__(self, config):
        self.config = config
        self.enabled = bool(config.OPENAI_API_KEY)
    
    async def verify_signal(
        self, 
        analysis_data: Dict[str, Any],
        deterministic_decision: str
    ) -> AIVerification:
        """Verify signal using AI analysis."""
        
        if not self.enabled:
            # Fallback to deterministic result
            return AIVerification(
                decision=deterministic_decision,
                confidence=70 if deterministic_decision != "NO_TRADE" else 50,
                reasons={
                    "direction": "AI verifier disabled",
                    "poi": "AI verifier disabled", 
                    "liquidity": "AI verifier disabled",
                    "confirmation": "AI verifier disabled"
                },
                missing_conditions=[],
                risk_notes="AI verification disabled - using deterministic analysis only"
            )
        
        try:
            # Prepare structured prompt for AI
            prompt = self._build_prompt(analysis_data, deterministic_decision)
            
            # Call AI API (placeholder - implement with actual OpenAI client)
            response = await self._call_ai(prompt)
            
            # Parse AI response
            ai_result = self._parse_ai_response(response)
            
            # Validate against hard rules
            validated_result = self._validate_against_rules(ai_result, analysis_data)
            
            return validated_result
            
        except Exception as e:
            logger.error(f"AI verification failed: {e}")
            # Fallback to deterministic result
            return AIVerification(
                decision=deterministic_decision,
                confidence=60 if deterministic_decision != "NO_TRADE" else 40,
                reasons={
                    "direction": "AI verification failed",
                    "poi": "AI verification failed",
                    "liquidity": "AI verification failed", 
                    "confirmation": "AI verification failed"
                },
                missing_conditions=[],
                risk_notes=f"AI verification error: {str(e)}"
            )
    
    def _build_prompt(self, analysis_data: Dict[str, Any], deterministic_decision: str) -> str:
        """Build structured prompt for AI analysis."""
        
        prompt = f"""
You are a professional trading analyst. Analyze the following market data and provide a structured trading signal.

SYMBOL: {analysis_data.get('symbol', 'UNKNOWN')}
TIMEFRAMES: 4H, 30M, 5M
DETERMINISTIC DECISION: {deterministic_decision}

MARKET STRUCTURE (4H):
- Trend: {analysis_data.get('4h_trend', 'Unknown')}
- Bias: {analysis_data.get('4h_bias', 'Unknown')}
- Last BOS/MSS: {analysis_data.get('4h_last_event', 'None')}
- Swing High: {analysis_data.get('4h_swing_high', 'N/A')}
- Swing Low: {analysis_data.get('4h_swing_low', 'N/A')}

POINTS OF INTEREST (30M):
- POI Type: {analysis_data.get('30m_poi_type', 'None')}
- POI Zone: {analysis_data.get('30m_poi_zone', 'N/A')}
- POI Strength: {analysis_data.get('30m_poi_strength', 'N/A')}

LIQUIDITY ANALYSIS:
- Liquidity Sweep: {analysis_data.get('liquidity_sweep', 'No')}
- Swept Pool: {analysis_data.get('swept_pool_type', 'None')}
- Sweep Price: {analysis_data.get('sweep_price', 'N/A')}

CONFIRMATION (5M):
- Pattern: {analysis_data.get('5m_pattern', 'None')}
- Pattern Confidence: {analysis_data.get('5m_confidence', 'N/A')}
- Entry Price: {analysis_data.get('5m_entry_price', 'N/A')}

RULES TO EVALUATE:
1. Direction: 4H must establish clear bias (BOS for continuation, MSS for reversal)
2. POI: 30M must have valid POI aligned with bias (OB/FVG minimum)
3. Liquidity: Must show sweep into/near POI
4. Confirmation: 5M must show trigger aligned with bias

RESPONSE FORMAT (JSON ONLY):
{{
    "decision": "BUY"|"SELL"|"NO_TRADE",
    "confidence": 0-100,
    "reasons": {{
        "direction": "brief explanation",
        "poi": "brief explanation", 
        "liquidity": "brief explanation",
        "confirmation": "brief explanation"
    }},
    "missing_conditions": ["condition1", "condition2"],
    "risk_notes": "risk assessment notes"
}}

Analyze strictly by the rules. If any rule fails, decision must be "NO_TRADE".
"""
        
        return prompt
    
    async def _call_ai(self, prompt: str) -> str:
        """Call AI API (placeholder implementation)."""
        # This is a placeholder - implement with actual OpenAI client
        # For now, return a mock response
        return json.dumps({
            "decision": "NO_TRADE",
            "confidence": 50,
            "reasons": {
                "direction": "AI placeholder - implement actual API call",
                "poi": "AI placeholder - implement actual API call",
                "liquidity": "AI placeholder - implement actual API call", 
                "confirmation": "AI placeholder - implement actual API call"
            },
            "missing_conditions": ["AI implementation"],
            "risk_notes": "This is a placeholder response"
        })
    
    def _parse_ai_response(self, response: str) -> AIVerification:
        """Parse AI response into structured format."""
        try:
            data = json.loads(response)
            
            return AIVerification(
                decision=data.get("decision", "NO_TRADE"),
                confidence=min(100, max(0, int(data.get("confidence", 50)))),
                reasons=data.get("reasons", {}),
                missing_conditions=data.get("missing_conditions", []),
                risk_notes=data.get("risk_notes", "")
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            raise ValueError("Invalid JSON response from AI")
    
    def _validate_against_rules(
        self, 
        ai_result: AIVerification, 
        analysis_data: Dict[str, Any]
    ) -> AIVerification:
        """Validate AI result against hard rules."""
        
        # Hard rule checks
        missing_conditions = []
        
        # Rule 1: Direction must be clear
        if not analysis_data.get('4h_bias'):
            missing_conditions.append("No clear 4H bias")
        
        # Rule 2: POI must exist and align with bias
        poi_type = analysis_data.get('30m_poi_type')
        bias = analysis_data.get('4h_bias')
        
        if not poi_type or poi_type == "None":
            missing_conditions.append("No valid POI detected")
        elif bias and poi_type not in ["OB", "FVG"]:  # Minimum requirements
            missing_conditions.append("POI type not sufficient (need OB/FVG)")
        
        # Rule 3: Liquidity sweep required
        if not analysis_data.get('liquidity_sweep'):
            missing_conditions.append("No liquidity sweep detected")
        
        # Rule 4: Confirmation required
        if not analysis_data.get('5m_pattern'):
            missing_conditions.append("No confirmation pattern")
        
        # If any hard rules fail, override AI decision
        if missing_conditions:
            return AIVerification(
                decision="NO_TRADE",
                confidence=max(20, ai_result.confidence - 30),
                reasons=ai_result.reasons,
                missing_conditions=missing_conditions,
                risk_notes=f"Hard rule failures: {', '.join(missing_conditions)}"
            )
        
        # Otherwise, return AI result (possibly adjusted)
        return ai_result
