# Template for the daily report
# This should be strictly followed by the daily_report_writer_agent

DAILY_REPORT_TEMPLATE = """
## EURUSD Pre-London Session Report

### Summary

[Provide a concise summary (3-5 sentences) of the current market situation. Include key points about:
- Recent price action impact
- Weekly profile identification (Classic Expansion, Consolidation Reversal, or Midweek Reversal)
- Next Day Model directional bias and target
- Key justification about price action (e.g., taking daily range bottom and closing back into the range)]

**The recommended bias for today is [bullish/bearish/neutral] with [low/medium/high] confidence.**

### Fundamental Context

[Brief reference to the weekly outlook. How does the last day's price action align with the macroeconomic context? 
Are we moving in the direction anticipated in the last Weekly report?]

### Weekly profile

[Detailed analysis of weekly profile:
- Comparison of last weekly candle to current
- Current week's range relative to previous week
- Day-specific analysis based on current day (Tuesday: Monday's action, Thursday: Wednesday reversal potential)
- If pattern not yet identified, state this clearly]

### Daily price action

[Detailed analysis of daily bias framework:
- Recent daily candle structure
- Identification of any failure to displace
- Analysis of daily PD arrays, breaker blocks, order blocks, fair value gaps
- Trend direction assessment
- Next Day Model application (where previous day closed relative to range)
- Specific price levels for PDH/PDL]

### Asian/Frankfurt Session

[Recap of overnight and early morning price action:
- Asian session behavior (ranging, trending)
- Frankfurt session developments
- Key levels established pre-London
- Whether price has taken previous session highs/lows (London reversal model)]

### Technical specifics

[Detailed CISD pattern analysis:
- Identification of any M30 CISD patterns
- Status of daily PD arrays
- Directional bias alignment with CISD patterns
- Best case scenario for entry (e.g., bearish trend with SIBI and M30 bearish CISD)
- Specific price levels for potential setups]
"""