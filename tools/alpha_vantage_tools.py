import os
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
import io
import base64
from datetime import datetime, timedelta
from dotenv import load_dotenv
from crewai import Tool

# Load environment variables
load_dotenv()
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
if not ALPHA_VANTAGE_API_KEY:
    raise ValueError("No Alpha Vantage API key found. Please add it to your .env file.")

class ForexDataTool(Tool):
    """Tool to retrieve forex data via the Alpha Vantage API."""
    
    name = "ForexDataTool"
    description = "Retrieves forex data for currency pairs via Alpha Vantage"
    
    def _run(self, from_symbol="EUR", to_symbol="USD", interval="Daily", outputsize="compact", datatype="json"):
        """
        Retrieves forex data for the specified currency pair.
        
        Args:
            from_symbol (str): From currency (e.g., "EUR")
            to_symbol (str): To currency (e.g., "USD")
            interval (str): Time interval - options:
                - "1min", "5min", "15min", "30min", "60min" for intraday
                - "Daily", "Weekly", "Monthly" for longer timeframes
            outputsize (str): "compact" (latest 100 data points) or "full" (up to 20 years)
            datatype (str): "json" or "csv"
            
        Returns:
            pandas.DataFrame: DataFrame containing OHLC data
        """
        try:
            base_url = "https://www.alphavantage.co/query"
            
            # Determine the API function based on the interval
            if interval in ["1min", "5min", "15min", "30min", "60min"]:
                function = "FX_INTRADAY"
                params = {
                    "function": function,
                    "from_symbol": from_symbol,
                    "to_symbol": to_symbol,
                    "interval": interval,
                    "outputsize": outputsize,
                    "datatype": datatype,
                    "apikey": ALPHA_VANTAGE_API_KEY
                }
            elif interval == "Daily":
                function = "FX_DAILY"
                params = {
                    "function": function,
                    "from_symbol": from_symbol,
                    "to_symbol": to_symbol,
                    "outputsize": outputsize,
                    "datatype": datatype,
                    "apikey": ALPHA_VANTAGE_API_KEY
                }
            elif interval == "Weekly":
                function = "FX_WEEKLY"
                params = {
                    "function": function,
                    "from_symbol": from_symbol,
                    "to_symbol": to_symbol,
                    "datatype": datatype,
                    "apikey": ALPHA_VANTAGE_API_KEY
                }
            elif interval == "Monthly":
                function = "FX_MONTHLY"
                params = {
                    "function": function,
                    "from_symbol": from_symbol,
                    "to_symbol": to_symbol,
                    "datatype": datatype,
                    "apikey": ALPHA_VANTAGE_API_KEY
                }
            else:
                return f"Invalid interval: {interval}"
            
            # Make the request
            response = requests.get(base_url, params=params)
            data = response.json()
            
            # Alpha Vantage returns error messages in the response JSON
            if "Error Message" in data:
                return f"API Error: {data['Error Message']}"
            
            if "Information" in data:
                return f"API Information: {data['Information']}"
            
            # Determine the key for the time series data based on the function
            if function == "FX_INTRADAY":
                time_series_key = f"Time Series FX ({interval})"
            elif function == "FX_DAILY":
                time_series_key = "Time Series FX (Daily)"
            elif function == "FX_WEEKLY":
                time_series_key = "Time Series FX (Weekly)"
            elif function == "FX_MONTHLY":
                time_series_key = "Time Series FX (Monthly)"
            
            # Check if the time series key exists in the response
            if time_series_key not in data:
                return f"No data found for {from_symbol}/{to_symbol} with interval {interval}"
            
            # Convert the nested JSON to a DataFrame
            df = pd.DataFrame.from_dict(data[time_series_key], orient="index")
            
            # Rename columns to OHLC format
            df = df.rename(columns={
                "1. open": "open",
                "2. high": "high",
                "3. low": "low",
                "4. close": "close"
            })
            
            # Convert string values to float
            for col in ["open", "high", "low", "close"]:
                df[col] = df[col].astype(float)
            
            # Convert index to datetime and sort by date
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            return f"Error retrieving forex data: {str(e)}"


class ForexRealTimeTool(Tool):
    """Tool to retrieve real-time forex exchange rates."""
    
    name = "ForexRealTimeTool"
    description = "Retrieves real-time forex exchange rates"
    
    def _run(self, from_symbol="EUR", to_symbol="USD"):
        """
        Gets the real-time exchange rate for a currency pair.
        
        Args:
            from_symbol (str): From currency (e.g., "EUR")
            to_symbol (str): To currency (e.g., "USD")
            
        Returns:
            dict: Exchange rate information
        """
        try:
            base_url = "https://www.alphavantage.co/query"
            params = {
                "function": "CURRENCY_EXCHANGE_RATE",
                "from_currency": from_symbol,
                "to_currency": to_symbol,
                "apikey": ALPHA_VANTAGE_API_KEY
            }
            
            response = requests.get(base_url, params=params)
            data = response.json()
            
            # Alpha Vantage returns error messages in the response JSON
            if "Error Message" in data:
                return f"API Error: {data['Error Message']}"
            
            if "Information" in data:
                return f"API Information: {data['Information']}"
            
            # Extract the exchange rate information
            if "Realtime Currency Exchange Rate" in data:
                exchange_info = data["Realtime Currency Exchange Rate"]
                result = {
                    "from_currency": exchange_info["1. From_Currency Code"],
                    "to_currency": exchange_info["3. To_Currency Code"],
                    "exchange_rate": float(exchange_info["5. Exchange Rate"]),
                    "last_refreshed": exchange_info["6. Last Refreshed"],
                    "timezone": exchange_info["7. Time Zone"],
                    "bid_price": float(exchange_info.get("8. Bid Price", 0)),
                    "ask_price": float(exchange_info.get("9. Ask Price", 0))
                }
                return result
            else:
                return f"No real-time exchange rate found for {from_symbol}/{to_symbol}"
            
        except Exception as e:
            return f"Error retrieving real-time forex data: {str(e)}"


class ChartGenerationTool(Tool):
    """Tool to generate forex charts from Alpha Vantage data."""
    
    name = "ChartGenerationTool"
    description = "Generates forex charts for technical analysis"
    
    def _run(self, data=None, from_symbol="EUR", to_symbol="USD", 
             interval="Daily", outputsize="compact", chart_type="candle", 
             indicators=None, highlight_levels=None):
        """
        Generates a forex chart based on provided or retrieved data.
        
        Args:
            data (pandas.DataFrame, optional): DataFrame with OHLC data
            from_symbol (str): From currency if data not provided
            to_symbol (str): To currency if data not provided
            interval (str): Time interval if data not provided
            outputsize (str): Data size if data not provided
            chart_type (str): Chart type (candle, line, etc.)
            indicators (dict, optional): Indicators to add to the chart
                Ex: {"sma": [20, 50, 200], "rsi": 14}
            highlight_levels (list, optional): Levels to highlight
                Ex: [1.0850, 1.0750]
                
        Returns:
            str: Base64 encoded image for display
        """
        try:
            # If data is not provided, use ForexDataTool to retrieve data
            if data is None or isinstance(data, str):
                forex_tool = ForexDataTool()
                data = forex_tool._run(
                    from_symbol=from_symbol,
                    to_symbol=to_symbol,
                    interval=interval,
                    outputsize=outputsize
                )
                if isinstance(data, str):  # Error returned
                    return data
            
            # Prepare data for mplfinance
            df = data.copy()
            
            # Configuration of the chart style
            mc = mpf.make_marketcolors(
                up='green', down='red',
                edge='inherit',
                wick={'up':'green', 'down':'red'},
                volume='blue'
            )
            
            s = mpf.make_mpf_style(
                base_mpf_style='yahoo',
                marketcolors=mc,
                gridstyle=':',
                y_on_right=True
            )
            
            # Prepare indicators
            addplot = []
            if indicators:
                if "sma" in indicators:
                    for period in indicators["sma"]:
                        df[f'SMA_{period}'] = df['close'].rolling(window=period).mean()
                        addplot.append(
                            mpf.make_addplot(df[f'SMA_{period}'], color=f'C{period%9}', width=1)
                        )
                if "ema" in indicators:
                    for period in indicators["ema"]:
                        df[f'EMA_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
                        addplot.append(
                            mpf.make_addplot(df[f'EMA_{period}'], color=f'C{period%9}', linestyle='--', width=1)
                        )
                if "rsi" in indicators:
                    period = indicators["rsi"]
                    # Calculate RSI
                    delta = df['close'].diff()
                    gain = delta.where(delta > 0, 0)
                    loss = -delta.where(delta < 0, 0)
                    avg_gain = gain.rolling(window=period).mean()
                    avg_loss = loss.rolling(window=period).mean()
                    rs = avg_gain / avg_loss
                    df['RSI'] = 100 - (100 / (1 + rs))
                    # Add RSI in a separate panel
                    addplot.append(
                        mpf.make_addplot(df['RSI'], panel=1, color='purple', ylim=(0, 100))
                    )
                    # Add reference lines at 30 and 70
                    addplot.append(
                        mpf.make_addplot([30] * len(df), panel=1, color='green', linestyle='--')
                    )
                    addplot.append(
                        mpf.make_addplot([70] * len(df), panel=1, color='red', linestyle='--')
                    )
            
            # Add price levels to highlight
            if highlight_levels:
                for level in highlight_levels:
                    addplot.append(
                        mpf.make_addplot([level] * len(df), color='blue', linestyle='-.')
                    )
            
            # Create buffer for the image
            buf = io.BytesIO()
            
            # Configure panels
            if indicators and "rsi" in indicators:
                panels = [0, 1]
                panel_ratios = (4, 1)
                panel_titles = [f"{from_symbol}/{to_symbol}", "RSI"]
            else:
                panels = None
                panel_ratios = None
                panel_titles = None
            
            # Generate chart
            title = f"{from_symbol}/{to_symbol} ({interval})"
            fig, axes = mpf.plot(
                df,
                type=chart_type,
                style=s,
                title=title,
                volume=False,
                figsize=(12, 8),
                panel_ratios=panel_ratios,
                addplot=addplot,
                returnfig=True,
                warn_too_much_data=10000
            )
            
            # Add titles to panels if needed
            if panel_titles:
                for i, title in enumerate(panel_titles):
                    if i < len(axes):
                        axes[i].set_title(title)
            
            # Save image
            fig.savefig(buf, format='png', bbox_inches='tight')
            buf.seek(0)
            
            # Encode to base64
            image_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
            
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            return f"Error generating chart: {str(e)}"


class MarketStructureTool(Tool):
    """Tool to analyze forex market structure."""
    
    name = "MarketStructureTool"
    description = "Analyzes forex market structure (CiSD, FVG, etc.)"
    
    def _run(self, data=None, from_symbol="EUR", to_symbol="USD", interval="Daily", outputsize="compact"):
        """
        Analyzes market structure to identify relevant patterns.
        
        Args:
            data (pandas.DataFrame, optional): DataFrame with OHLC data
            from_symbol (str): From currency if data not provided
            to_symbol (str): To currency if data not provided
            interval (str): Time interval if data not provided
            outputsize (str): Data size if data not provided
            
        Returns:
            dict: Results of structural analysis
        """
        try:
            # If data is not provided, use ForexDataTool to retrieve data
            if data is None or isinstance(data, str):
                forex_tool = ForexDataTool()
                data = forex_tool._run(
                    from_symbol=from_symbol,
                    to_symbol=to_symbol,
                    interval=interval,
                    outputsize=outputsize
                )
                if isinstance(data, str):  # Error returned
                    return data
            
            # Copy data for analysis
            df = data.copy()
            
            # Initialize results
            result = {
                "trend": None,
                "structure": None,
                "fvg": [],
                "poi": [],
                "support_resistance": []
            }
            
            # Simple trend analysis (based on EMA 20 vs EMA 50)
            df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
            df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
            
            if df['EMA_20'].iloc[-1] > df['EMA_50'].iloc[-1]:
                result["trend"] = "bullish"
            else:
                result["trend"] = "bearish"
            
            # Detect swings (pivots)
            window = 5  # Window for pivot detection
            
            # High pivots
            df['pivot_high'] = df.iloc[window:-window]['high'].rolling(window=2*window+1, center=True).apply(
                lambda x: 1 if x.iloc[window] == max(x) else 0, raw=False
            )
            
            # Low pivots
            df['pivot_low'] = df.iloc[window:-window]['low'].rolling(window=2*window+1, center=True).apply(
                lambda x: 1 if x.iloc[window] == min(x) else 0, raw=False
            )
            
            # Extract significant pivots
            highs = df[df['pivot_high'] == 1].index
            lows = df[df['pivot_low'] == 1].index
            
            # Structure analysis (CiSD - Change in Structure Direction)
            if len(highs) >= 2 and len(lows) >= 2:
                last_two_highs = df.loc[highs[-2:]]['high'].values
                last_two_lows = df.loc[lows[-2:]]['low'].values
                
                if last_two_highs[1] > last_two_highs[0] and last_two_lows[1] > last_two_lows[0]:
                    result["structure"] = "bullish (Higher Highs, Higher Lows)"
                elif last_two_highs[1] < last_two_highs[0] and last_two_lows[1] < last_two_lows[0]:
                    result["structure"] = "bearish (Lower Highs, Lower Lows)"
                else:
                    result["structure"] = "consolidation"
            
            # Detect Fair Value Gaps (FVG)
            for i in range(2, len(df)):
                # Bullish FVG: low[i] > high[i-2]
                if df['low'].iloc[i] > df['high'].iloc[i-2]:
                    fvg = {
                        "type": "bullish",
                        "date": df.index[i].strftime('%Y-%m-%d %H:%M'),
                        "upper_level": df['low'].iloc[i],
                        "lower_level": df['high'].iloc[i-2],
                        "size": df['low'].iloc[i] - df['high'].iloc[i-2]
                    }
                    result["fvg"].append(fvg)
                
                # Bearish FVG: high[i] < low[i-2]
                if df['high'].iloc[i] < df['low'].iloc[i-2]:
                    fvg = {
                        "type": "bearish",
                        "date": df.index[i].strftime('%Y-%m-%d %H:%M'),
                        "upper_level": df['low'].iloc[i-2],
                        "lower_level": df['high'].iloc[i],
                        "size": df['low'].iloc[i-2] - df['high'].iloc[i]
                    }
                    result["fvg"].append(fvg)
            
            # Limit to the 5 most recent FVGs
            result["fvg"] = result["fvg"][-5:] if result["fvg"] else []
            
            # Identify Points of Interest (POI) - significant support/resistance zones
            for idx in highs:
                poi = {
                    "type": "resistance",
                    "date": idx.strftime('%Y-%m-%d %H:%M'),
                    "level": df.loc[idx, 'high'],
                    "significance": 1  # Adjust based on importance
                }
                result["poi"].append(poi)
            
            for idx in lows:
                poi = {
                    "type": "support",
                    "date": idx.strftime('%Y-%m-%d %H:%M'),
                    "level": df.loc[idx, 'low'],
                    "significance": 1  # Adjust based on importance
                }
                result["poi"].append(poi)
            
            # Identify key support and resistance levels (based on recent price action)
            pivot_points = []
            for idx in highs:
                pivot_points.append({
                    "type": "resistance",
                    "level": df.loc[idx, 'high'],
                    "date": idx.strftime('%Y-%m-%d %H:%M')
                })
            
            for idx in lows:
                pivot_points.append({
                    "type": "support",
                    "level": df.loc[idx, 'low'],
                    "date": idx.strftime('%Y-%m-%d %H:%M')
                })
            
            # Sort pivot points by level
            pivot_points.sort(key=lambda x: x["level"])
            
            # Group nearby levels (within 0.5% of price)
            grouped_levels = []
            if pivot_points:
                current_group = [pivot_points[0]]
                current_level = pivot_points[0]["level"]
                
                for point in pivot_points[1:]:
                    if abs(point["level"] - current_level) / current_level < 0.005:  # 0.5% threshold
                        current_group.append(point)
                    else:
                        # Calculate average level for the group
                        avg_level = sum(p["level"] for p in current_group) / len(current_group)
                        grouped_levels.append({
                            "type": current_group[0]["type"],  # Use the type of the first point in group
                            "level": avg_level,
                            "touches": len(current_group),
                            "dates": [p["date"] for p in current_group]
                        })
                        # Start a new group
                        current_group = [point]
                        current_level = point["level"]
                
                # Add the last group
                if current_group:
                    avg_level = sum(p["level"] for p in current_group) / len(current_group)
                    grouped_levels.append({
                        "type": current_group[0]["type"],
                        "level": avg_level,
                        "touches": len(current_group),
                        "dates": [p["date"] for p in current_group]
                    })
            
            # Sort by significance (number of touches)
            grouped_levels.sort(key=lambda x: x["touches"], reverse=True)
            
            # Take the top 5 most significant levels
            result["support_resistance"] = grouped_levels[:5]
            
            return result
            
        except Exception as e:
            return f"Error analyzing market structure: {str(e)}"

# Example usage:
if __name__ == "__main__":
    # Test the ForexDataTool
    forex_tool = ForexDataTool()
    data = forex_tool._run(from_symbol="EUR", to_symbol="USD", interval="Daily")
    print(data.head())
    
    # Test the ForexRealTimeTool
    realtime_tool = ForexRealTimeTool()
    rate = realtime_tool._run(from_symbol="EUR", to_symbol="USD")
    print(rate)
    
    # Test the ChartGenerationTool
    chart_tool = ChartGenerationTool()
    chart = chart_tool._run(data=data, indicators={"sma": [20, 50, 200]})
    
    # Save the chart to a file for testing
    if not isinstance(chart, str) or not chart.startswith("Error"):
        # Extract the base64 image data
        image_data = chart.split(',')[1]
        with open("eurusd_chart.png", "wb") as f:
            f.write(base64.b64decode(image_data))
        print("Chart saved to eurusd_chart.png")
    else:
        print(chart)