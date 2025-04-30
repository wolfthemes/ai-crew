# config/cisd_pattern_config.py
"""
Configuration parameters for CISD pattern detection and analysis.
These parameters can be adjusted to fine-tune the pattern recognition criteria.
"""

# CISD Pattern Qualification Parameters
CISD_CONFIG = {
    # Timeframe settings
    "timeframes": {
        "primary": "M30",      # Primary timeframe for CISD detection
        "entry": "M5",         # Entry timeframe for execution
        "context": "H4"        # Context timeframe for trend direction
    },
    
    # Contraction criteria
    "contraction": {
        "min_periods": 3,      # Minimum number of candles in contraction phase
        "max_periods": 8,      # Maximum number of candles in contraction phase
        "min_narrowing": 0.35, # Minimum percentage narrowing vs previous range (35%)
        "volume_decline": 0.2  # Minimum volume decline during contraction (20%)
    },
    
    # Breakout criteria
    "breakout": {
        "min_body_ratio": 0.6,   # Minimum body-to-range ratio for breakout candle
        "min_range_increase": 1.2, # Minimum range increase vs contraction average
        "volume_increase": 1.5   # Minimum volume increase vs contraction average
    },
    
    # Entry parameters
    "entry": {
        "min_cisd_completion": 0.4,  # Minimum CISD range completion before entry (40%)
        "max_cisd_completion": 0.7,  # Maximum CISD range completion before entry (70%)
        "preferred_level": 0.5,      # Preferred entry level within CISD range (50%)
        "time_window_start": "09:30", # Start of preferred entry time window (London time)
        "time_window_end": "11:00"    # End of preferred entry time window (London time)
    },
    
    # Risk management
    "risk_management": {
        "stop_placement": "below_swing", # Stop placement strategy (below_swing, atr_multiple, fixed)
        "atr_multiple": 0.5,           # If using ATR-based stops, the ATR multiple
        "fixed_pips": 15,              # If using fixed stops, the number of pips
        "target_r_multiple": 2.5,      # Target as R-multiple of risk
        "breakeven_move": 0.75         # Move stop to breakeven after this portion of first target
    },
    
    # Pattern probability factors
    "probability_factors": {
        "trend_alignment": 2.0,    # Weight for alignment with larger timeframe trend
        "support_resistance": 1.5, # Weight for proximity to key support/resistance
        "time_of_day": 1.2,        # Weight for optimal time of day
        "news_proximity": 0.8,     # Weight for distance from high-impact news
        "previous_pattern": 1.3    # Weight for success of previous pattern
    },
    
    # London session parameters
    "london_session": {
        "start_time": "08:00",      # London session start time
        "end_time": "16:00",        # London session end time
        "optimal_entry_start": "09:30", # Optimal entry window start
        "optimal_entry_end": "11:00",   # Optimal entry window end
        "session_midpoint": "12:00",    # Session midpoint for bias reassessment
        "late_session_cutoff": "14:30"  # Cut-off time for new entries
    },
    
    # Weekly profile adjustments
    "weekly_profile_adjustments": {
        "monday_factor": 0.8,      # Probability adjustment for Monday patterns
        "tuesday_factor": 0.9,     # Probability adjustment for Tuesday patterns
        "wednesday_factor": 1.2,   # Probability adjustment for Wednesday patterns
        "thursday_factor": 1.1,    # Probability adjustment for Thursday patterns
        "friday_factor": 0.7       # Probability adjustment for Friday patterns
    }
}

# Trading days configuration
TRADING_DAYS_CONFIG = {
    "preferred_days": ["Tuesday", "Wednesday", "Thursday"],
    "avoid_days": ["Monday", "Friday"],
    "avoid_before_holidays": True,
    "avoid_high_impact_news": True
}

# Function to get CISD configuration
def get_cisd_config():
    """Returns the current CISD pattern configuration."""
    return CISD_CONFIG

# Function to get trading days configuration
def get_trading_days_config():
    """Returns the current trading days configuration."""
    return TRADING_DAYS_CONFIG

# Function to determine if today is a tradable day
def is_tradable_day(date=None, high_impact_news=False):
    """
    Determines if the given date is a tradable day based on configuration.
    
    Args:
        date: The date to check (defaults to today)
        high_impact_news: Boolean indicating if high impact news is scheduled
        
    Returns:
        Boolean indicating if the day is tradable
    """
    import datetime
    
    if date is None:
        date = datetime.datetime.now()
        
    day_name = date.strftime("%A")
    config = get_trading_days_config()
    
    # Check if day is in preferred days
    if day_name not in config["preferred_days"]:
        return False
    
    # Check high impact news if configured to avoid
    if config["avoid_high_impact_news"] and high_impact_news:
        return False
        
    # Add holiday check here if needed
    
    return True