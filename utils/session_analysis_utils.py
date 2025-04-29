import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Union, Optional

def calculate_atr(high: List[float], low: List[float], close: List[float], periods: int = 14) -> float:
    """
    Calculate the Average True Range (ATR) for volatility assessment
    
    Args:
        high: List of high prices
        low: List of low prices
        close: List of close prices (shifted by 1 for TR calculation)
        periods: Number of periods for ATR calculation (default: 14)
        
    Returns:
        Current ATR value
    """
    # Convert inputs to numpy arrays
    high_np = np.array(high)
    low_np = np.array(low)
    close_np = np.array(close)
    
    # Calculate True Range
    tr1 = high_np - low_np
    tr2 = np.abs(high_np - np.roll(close_np, 1))
    tr3 = np.abs(low_np - np.roll(close_np, 1))
    
    # Replace NaN values in the first row
    tr2[0] = tr1[0]
    tr3[0] = tr1[0]
    
    # Get the maximum of the three TR calculations
    tr = np.maximum(tr1, np.maximum(tr2, tr3))
    
    # Calculate ATR using simple moving average (can be changed to EMA)
    atr = np.mean(tr[-periods:])
    
    return atr

def calculate_choppiness_index(high: List[float], low: List[float], close: List[float], periods: int = 14) -> float:
    """
    Calculate the Choppiness Index to identify trending vs choppy market conditions
    
    Choppiness Index:
    - Range: 0-100
    - Values > 61.8 indicate choppy market conditions
    - Values < 38.2 indicate trending market conditions
    
    Args:
        high: List of high prices
        low: List of low prices
        close: List of close prices
        periods: Number of periods for calculation (default: 14)
        
    Returns:
        Current Choppiness Index value
    """
    # Convert inputs to numpy arrays
    high_np = np.array(high[-periods:])
    low_np = np.array(low[-periods:])
    close_np = np.array(close[-periods:])
    
    # Calculate the sum of the ATR for the given period
    tr1 = high_np - low_np
    tr2 = np.abs(high_np - np.roll(close_np, 1))
    tr3 = np.abs(low_np - np.roll(close_np, 1))
    
    # Replace NaN in first position
    tr2[0] = tr1[0]
    tr3[0] = tr1[0]
    
    tr = np.maximum(tr1, np.maximum(tr2, tr3))
    atr_sum = np.sum(tr)
    
    # Calculate the highest high and lowest low for the given period
    highest_high = np.max(high_np)
    lowest_low = np.min(low_np)
    
    # Calculate the choppiness index
    if highest_high - lowest_low == 0:  # Avoid division by zero
        return 100.0  # Maximum choppiness
    
    choppiness = 100 * np.log10(atr_sum / (highest_high - lowest_low)) / np.log10(periods)
    
    return choppiness

def next_day_model(
    prev_day_open: float, 
    prev_day_high: float, 
    prev_day_low: float, 
    prev_day_close: float
) -> Dict[str, Union[str, float, Dict[str, float]]]:
    """
    Implement the Next Day Model for immediate directional bias
    
    Args:
        prev_day_open: Previous day's opening price
        prev_day_high: Previous day's high price
        prev_day_low: Previous day's low price
        prev_day_close: Previous day's closing price
        
    Returns:
        Dictionary containing:
        - bias: The directional bias (bullish/bearish/neutral)
        - confidence: Confidence level (high/medium/low)
        - targets: Dictionary of target levels
        - key_levels: Dictionary of key price levels to watch
    """
    # Calculate price action characteristics
    range_size = prev_day_high - prev_day_low
    close_position = (prev_day_close - prev_day_low) / range_size if range_size > 0 else 0.5
    
    # Calculate key levels
    mid_point = prev_day_low + (range_size / 2)
    upper_quarter = prev_day_low + (range_size * 0.75)
    lower_quarter = prev_day_low + (range_size * 0.25)
    
    # Default bias is neutral
    bias = "neutral"
    confidence = "medium"
    
    # Determine bias based on close position
    if close_position > 0.75:  # Close in upper quarter
        bias = "bearish"  # Next day tendency to revisit previous day's body
        confidence = "high" if close_position > 0.9 else "medium"
    elif close_position < 0.25:  # Close in lower quarter
        bias = "bullish"  # Next day tendency to revisit previous day's body
        confidence = "high" if close_position < 0.1 else "medium"
    else:  # Close in middle range
        bias = "neutral"
        confidence = "low"
    
    # Calculate targets based on bias
    targets = {}
    key_levels = {
        "prev_day_high": prev_day_high,
        "prev_day_low": prev_day_low,
        "mid_point": mid_point
    }
    
    if bias == "bullish":
        targets = {
            "initial": mid_point,
            "primary": upper_quarter,
            "extended": prev_day_high,
            "maximum": prev_day_high + (range_size * 0.3)
        }
        key_levels["stop_level"] = prev_day_low - (range_size * 0.1)
        
    elif bias == "bearish":
        targets = {
            "initial": mid_point,
            "primary": lower_quarter,
            "extended": prev_day_low,
            "maximum": prev_day_low - (range_size * 0.3)
        }
        key_levels["stop_level"] = prev_day_high + (range_size * 0.1)
        
    else:  # neutral
        targets = {
            "upper_target": upper_quarter,
            "lower_target": lower_quarter
        }
        key_levels["upper_breakout"] = prev_day_high + (range_size * 0.1)
        key_levels["lower_breakout"] = prev_day_low - (range_size * 0.1)
    
    # Return consolidated analysis
    return {
        "bias": bias,
        "confidence": confidence,
        "targets": targets,
        "key_levels": key_levels,
        "range_size": range_size,
        "close_position": close_position
    }

def analyze_session_bias(
    prev_day_open: float,
    prev_day_high: float,
    prev_day_low: float,
    prev_day_close: float,
    current_price: float,
    h4_prices: Dict[str, List[float]],
    volatility_threshold: float = 0.0007,  # ~7 pips in EUR/USD
    choppiness_threshold: float = 61.8
) -> Dict[str, any]:
    """
    Analyze session-specific bias with multiple factors
    
    Args:
        prev_day_open: Previous day's opening price
        prev_day_high: Previous day's high price
        prev_day_low: Previous day's low price
        prev_day_close: Previous day's closing price
        current_price: Current price at analysis time
        h4_prices: Dictionary with h4 OHLC data arrays
        volatility_threshold: Minimum ATR for viable trading conditions
        choppiness_threshold: Maximum choppiness index for viable trading
        
    Returns:
        Dictionary with comprehensive session bias analysis
    """
    # Apply Next Day Model
    ndm_analysis = next_day_model(
        prev_day_open, 
        prev_day_high, 
        prev_day_low, 
        prev_day_close
    )
    
    # Calculate volatility metrics
    atr_value = calculate_atr(
        h4_prices['high'], 
        h4_prices['low'], 
        h4_prices['close']
    )
    
    choppiness = calculate_choppiness_index(
        h4_prices['high'], 
        h4_prices['low'], 
        h4_prices['close']
    )
    
    # Determine if volatility is sufficient for trading
    is_volatile_enough = atr_value >= volatility_threshold
    is_trending = choppiness <= choppiness_threshold
    
    # Check current price relative to previous day
    above_prev_high = current_price > prev_day_high
    below_prev_low = current_price < prev_day_low
    in_prev_range = not (above_prev_high or below_prev_low)
    
    # Determine h4 trend direction (simple method - can be enhanced)
    h4_closes = h4_prices['close']
    h4_trend = "bullish" if h4_closes[-1] > h4_closes[-3] else "bearish"
    
    # Adjust confidence based on multiple factors
    final_confidence = ndm_analysis['confidence']
    
    # Lower confidence if volatility is insufficient
    if not is_volatile_enough:
        final_confidence = "low"
    
    # Lower confidence if market is choppy
    if choppiness > choppiness_threshold:
        final_confidence = "low"
    
    # Increase confidence if h4 trend aligns with NDM bias
    if ndm_analysis['bias'] == h4_trend and final_confidence == "medium":
        final_confidence = "high"
    
    # Lower confidence if h4 trend contradicts NDM bias
    if ndm_analysis['bias'] != h4_trend and ndm_analysis['bias'] != "neutral":
        final_confidence = "low"
    
    # Final bias determination based on weighted factors
    final_bias = ndm_analysis['bias']
    
    # Override with h4 trend if current price has already broken out of previous day's range
    if above_prev_high:
        final_bias = "bullish"
        if h4_trend == "bullish":
            final_confidence = "high"
    elif below_prev_low:
        final_bias = "bearish"
        if h4_trend == "bearish":
            final_confidence = "high"
    
    # Session-specific probabilities (example values - should be calibrated)
    session_probabilities = {}
    
    if final_bias == "bullish":
        session_probabilities = {
            "trend_continuation": 0.65 if final_confidence == "high" else 0.55,
            "reversal": 0.25 if final_confidence == "high" else 0.35,
            "choppy": 0.10 if is_trending else 0.40
        }
    elif final_bias == "bearish":
        session_probabilities = {
            "trend_continuation": 0.65 if final_confidence == "high" else 0.55,
            "reversal": 0.25 if final_confidence == "high" else 0.35,
            "choppy": 0.10 if is_trending else 0.40
        }
    else:  # neutral
        session_probabilities = {
            "upside_breakout": 0.40,
            "downside_breakout": 0.40,
            "remain_range_bound": 0.70 if choppiness > choppiness_threshold else 0.20
        }
    
    # Return consolidated analysis
    return {
        "bias": final_bias,
        "confidence": final_confidence,
        "ndm_analysis": ndm_analysis,
        "current_price": current_price,
        "atr": atr_value,
        "choppiness": choppiness,
        "is_volatile_enough": is_volatile_enough,
        "is_trending": is_trending,
        "h4_trend": h4_trend,
        "position_to_prev_day": "above" if above_prev_high else "below" if below_prev_low else "inside",
        "session_probabilities": session_probabilities,
        "key_levels": ndm_analysis["key_levels"],
        "targets": ndm_analysis["targets"],
        "trading_viability": "high" if is_volatile_enough and is_trending else 
                            "medium" if is_volatile_enough or is_trending else 
                            "low"
    }

def create_session_decision_tree(
    bias_analysis: Dict[str, any], 
    session_name: str = "London"
) -> Dict[str, any]:
    """
    Create a sequential decision tree for session trading
    
    Args:
        bias_analysis: The result from analyze_session_bias
        session_name: The name of the trading session (default: London)
        
    Returns:
        Dictionary with decision tree for the session
    """
    bias = bias_analysis["bias"]
    confidence = bias_analysis["confidence"]
    key_levels = bias_analysis["key_levels"]
    targets = bias_analysis["targets"]
    current_price = bias_analysis["current_price"]
    
    # Create decision tree
    decision_tree = {
        "session": session_name,
        "primary_bias": bias,
        "confidence": confidence,
        "initial_action": "Observe" if confidence == "low" else "Prepare for entry",
        "steps": []
    }
    
    # Step 1: Initial assessment
    if bias == "bullish":
        decision_tree["steps"].append({
            "step": 1,
            "description": "Initial market assessment",
            "action": "Look for buying opportunities",
            "confirmation_level": key_levels.get("prev_day_low", 0) + 
                                 (key_levels.get("prev_day_high", 0) - key_levels.get("prev_day_low", 0)) * 0.25
        })
    elif bias == "bearish":
        decision_tree["steps"].append({
            "step": 1,
            "description": "Initial market assessment",
            "action": "Look for selling opportunities",
            "confirmation_level": key_levels.get("prev_day_high", 0) - 
                                 (key_levels.get("prev_day_high", 0) - key_levels.get("prev_day_low", 0)) * 0.25
        })
    else:  # neutral
        decision_tree["steps"].append({
            "step": 1,
            "description": "Initial market assessment",
            "action": "Wait for directional break",
            "breakout_levels": {
                "upper": key_levels.get("upper_breakout", 0),
                "lower": key_levels.get("lower_breakout", 0)
            }
        })
    
    # Step 2: Session confirmation
    if bias == "bullish":
        decision_tree["steps"].append({
            "step": 2,
            "description": "Session confirmation",
            "action": "Enter long if price holds above confirmation level during first hour",
            "invalidation": "Bias invalidated if price breaks below previous day's low",
            "stop_level": key_levels.get("stop_level", key_levels.get("prev_day_low", 0) * 0.9998)
        })
    elif bias == "bearish":
        decision_tree["steps"].append({
            "step": 2,
            "description": "Session confirmation",
            "action": "Enter short if price holds below confirmation level during first hour",
            "invalidation": "Bias invalidated if price breaks above previous day's high",
            "stop_level": key_levels.get("stop_level", key_levels.get("prev_day_high", 0) * 1.0002)
        })
    else:  # neutral
        decision_tree["steps"].append({
            "step": 2,
            "description": "Session confirmation",
            "action": "Enter on break of range with stop below/above entry candle",
            "invalidation": "Bias remains neutral if price stays within range"
        })
    
    # Step 3: Target management
    if bias == "bullish":
        decision_tree["steps"].append({
            "step": 3,
            "description": "Target management",
            "targets": {
                "initial": targets.get("initial", 0),
                "primary": targets.get("primary", 0),
                "extended": targets.get("extended", 0)
            },
            "management": "Scale out at targets or trail stop after first target reached"
        })
    elif bias == "bearish":
        decision_tree["steps"].append({
            "step": 3,
            "description": "Target management",
            "targets": {
                "initial": targets.get("initial", 0),
                "primary": targets.get("primary", 0),
                "extended": targets.get("extended", 0)
            },
            "management": "Scale out at targets or trail stop after first target reached"
        })
    else:  # neutral
        decision_tree["steps"].append({
            "step": 3,
            "description": "Target management",
            "targets": {
                "upper": targets.get("upper_target", 0),
                "lower": targets.get("lower_target", 0)
            },
            "management": "Take profits quickly at targets, don't hold through session"
        })
    
    # Step 4: Session progress assessment
    decision_tree["steps"].append({
        "step": 4,
        "description": "Mid-session assessment",
        "action": "Reassess bias after 2 hours into session",
        "adaptation": "Look for reversal if initial bias failed, or continuation if successful"
    })
    
    return decision_tree