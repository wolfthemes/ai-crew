import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, Any, Type, Optional, List
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

class HistoricalDataInput(BaseModel):
    """Input schema for historical forex data"""
    from_currency: str = Field(default="EUR", description="Base currency code (e.g., EUR)")
    to_currency: str = Field(default="USD", description="Quote currency code (e.g., USD)")
    days: int = Field(default=5, description="Number of days of data to retrieve (max 100)")

class AlphaVantageHistoricalTool(BaseTool):
    """Tool for retrieving historical forex data from Alpha Vantage API"""
    
    name: str = "AlphaVantageHistorical"
    description: str = "Get historical forex price data from Alpha Vantage API"
    args_schema: Type[BaseModel] = HistoricalDataInput
    
    def __init__(self):
        """Initialize the Alpha Vantage API client"""
        # Initialize BaseTool first
        super().__init__()
        
        # Load environment variables
        load_dotenv()
        
        # Get API key from environment
        self._api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        
        # Check if API key exists
        if not self._api_key:
            raise ValueError("No Alpha Vantage API key found. Please set ALPHA_VANTAGE_API_KEY in your environment or .env file")
        
        # Set up other instance variables
        self._base_url = "https://www.alphavantage.co/query"
        self._cached_data = {}
    
    def _run(self, from_currency: str = "EUR", to_currency: str = "USD", days: int = 5) -> str:
        """
        Get historical forex data for a currency pair
        
        Args:
            from_currency: Base currency
            to_currency: Quote currency
            days: Number of days of data to retrieve
        
        Returns:
            Formatted string with historical price data
        """
        try:
            df = self.get_daily_forex(from_currency, to_currency)
            
            if isinstance(df, pd.DataFrame) and 'error' in df.columns:
                return f"Error retrieving historical {from_currency}/{to_currency} data: {df['error'][0]}"
            
            # Limit to requested number of days
            recent_data = df.iloc[-days:].copy()
            
            # Calculate day-over-day changes
            recent_data['change'] = recent_data['close'].pct_change() * 100
            
            # Format the output
            result = f"## {from_currency}/{to_currency} Historical Data (Last {days} Days)\n\n"
            
            # Add table header
            result += "| Date | Open | High | Low | Close | Change |\n"
            result += "| ---- | ---- | ---- | --- | ----- | ------ |\n"
            
            # Add rows
            for date, row in recent_data.iterrows():
                date_str = date.strftime('%Y-%m-%d')
                change_str = f"{row['change']:.2f}%" if not pd.isna(row['change']) else "N/A"
                result += f"| {date_str} | {row['open']:.5f} | {row['high']:.5f} | {row['low']:.5f} | {row['close']:.5f} | {change_str} |\n"
            
            # Add summary statistics
            result += f"\n### Summary Statistics\n\n"
            result += f"- 5-Day High: **{recent_data['high'].max():.5f}**\n"
            result += f"- 5-Day Low: **{recent_data['low'].min():.5f}**\n"
            result += f"- 5-Day Average Close: **{recent_data['close'].mean():.5f}**\n"
            result += f"- 5-Day Range: **{(recent_data['high'].max() - recent_data['low'].min()):.5f}**\n"
            
            return result
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_daily_forex(self, from_currency="EUR", to_currency="USD", outputsize="compact") -> pd.DataFrame:
        """
        Get daily forex data for a currency pair
        
        Args:
            from_currency (str): Base currency
            to_currency (str): Quote currency
            outputsize (str): 'compact' for last 100 datapoints, 'full' for full history
            
        Returns:
            pd.DataFrame: Daily forex data
        """
        cache_key = f"daily_forex_{from_currency}_{to_currency}_{outputsize}"
        if cache_key in self._cached_data:
            # Use cached data if less than 1 hour old
            if (datetime.now() - self._cached_data[cache_key]["timestamp"]).total_seconds() < 3600:
                return self._cached_data[cache_key]["data"]
        
        params = {
            "function": "FX_DAILY",
            "from_symbol": from_currency,
            "to_symbol": to_currency,
            "outputsize": outputsize,
            "apikey": self._api_key  # Use the private attribute
        }
        
        response = requests.get(self._base_url, params=params)
        data = response.json()
        
        if "Time Series FX (Daily)" in data:
            # Convert the nested JSON to a DataFrame
            time_series = data["Time Series FX (Daily)"]
            df = pd.DataFrame.from_dict(time_series, orient="index")
            
            # Rename columns for clarity
            df.columns = [col.split(". ")[1] for col in df.columns]
            
            # Convert data types
            for col in df.columns:
                df[col] = pd.to_numeric(df[col])
            
            # Add date as an actual column
            df.index = pd.to_datetime(df.index)
            df.sort_index(inplace=True)
            
            # Cache the result
            self._cached_data[cache_key] = {
                "data": df,
                "timestamp": datetime.now()
            }
            return df
        elif "Error Message" in data:
            return pd.DataFrame({"error": [data["Error Message"]]})
        elif "Information" in data:
            return pd.DataFrame({"error": ["Rate limit reached"], "message": [data["Information"]]})
        else:
            return pd.DataFrame({"error": ["Unexpected response format"]})
    
    def get_weekly_range_data(self, from_currency="EUR", to_currency="USD") -> str:
        """
        Get weekly range data for a currency pair
        
        Args:
            from_currency (str): Base currency
            to_currency (str): Quote currency
            
        Returns:
            str: Formatted weekly range data
        """
        try:
            df = self.get_daily_forex(from_currency, to_currency)
            
            if isinstance(df, pd.DataFrame) and 'error' in df.columns:
                return f"Error retrieving data: {df['error'][0]}"
            
            # Get this week and last week data
            today = datetime.now().date()
            start_of_week = today - timedelta(days=today.weekday())
            
            # Filter to the last two weeks
            two_weeks_ago = start_of_week - timedelta(days=14)
            recent_data = df[df.index >= pd.Timestamp(two_weeks_ago)]
            
            # Create a week number column
            recent_data['week'] = recent_data.index.isocalendar().week
            weekly_groups = recent_data.groupby('week')
            
            result = f"## {from_currency}/{to_currency} Weekly Ranges\n\n"
            
            for week, group in weekly_groups:
                week_high = group['high'].max()
                week_low = group['low'].min()
                week_open = group.iloc[0]['open']
                week_close = group.iloc[-1]['close']
                
                week_start = group.index[0].strftime('%Y-%m-%d')
                week_end = group.index[-1].strftime('%Y-%m-%d')
                
                result += f"### Week of {week_start} to {week_end}:\n"
                result += f"- Open: **{week_open:.5f}**\n"
                result += f"- High: **{week_high:.5f}**\n"
                result += f"- Low: **{week_low:.5f}**\n"
                result += f"- Close: **{week_close:.5f}**\n"
                result += f"- Range: **{(week_high - week_low):.5f}**\n"
                result += f"- Change: **{((week_close - week_open) / week_open * 100):.2f}%**\n\n"
            
            return result
            
        except Exception as e:
            return f"Error getting weekly range data: {str(e)}"

# Example usage
if __name__ == "__main__":
    try:
        av_historical = AlphaVantageHistoricalTool()
        result = av_historical._run(from_currency="EUR", to_currency="USD", days=5)
        print(result)
        
        weekly_data = av_historical.get_weekly_range_data("EUR", "USD")
        print("\nWeekly Range Data:")
        print(weekly_data)
    except Exception as e:
        print(f"Error: {e}")