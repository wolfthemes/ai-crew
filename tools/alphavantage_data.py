import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, Any, Type, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

class ForexRateInput(BaseModel):
    """Input schema for forex rate lookup"""
    from_currency: str = Field(default="EUR", description="Base currency code (e.g., EUR)")
    to_currency: str = Field(default="USD", description="Quote currency code (e.g., USD)")

class AlphaVantageDataTool(BaseTool):
    """Tool for retrieving forex data from Alpha Vantage API"""
    
    name: str = "AlphaVantageData"
    description: str = "Get real-time and historical forex data from Alpha Vantage API"
    args_schema: Type[BaseModel] = ForexRateInput
    
    def __init__(self, api_key=None):
        """
        Initialize the Alpha Vantage API client
        
        Args:
            api_key (str, optional): API key for Alpha Vantage. If None, loads from environment
        """
        # Initialize the BaseTool
        super().__init__()
        
        # Load API key
        load_dotenv()
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        
        if not self.api_key:
            raise ValueError("No Alpha Vantage API key found. Please set ALPHA_VANTAGE_API_KEY in your environment or .env file")
        
        self.base_url = "https://www.alphavantage.co/query"
        self.cached_data = {}
    
    def _run(self, from_currency: str = "EUR", to_currency: str = "USD") -> str:
        """
        Get the exchange rate for a currency pair
        
        Args:
            from_currency: Base currency
            to_currency: Quote currency
        
        Returns:
            Formatted string with exchange rate information
        """
        try:
            rate_data = self.get_forex_rate(from_currency, to_currency)
            
            if "error" in rate_data:
                return f"Error retrieving {from_currency}/{to_currency} rate: {rate_data.get('error')}"
            
            # Format the output
            result = f"## {from_currency}/{to_currency} Exchange Rate\n\n"
            result += f"Current rate: **{rate_data['exchange_rate']:.5f}**\n"
            result += f"Last updated: {rate_data['last_refreshed']} {rate_data['time_zone']}\n"
            
            return result
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_forex_rate(self, from_currency="EUR", to_currency="USD") -> Dict[str, Any]:
        """
        Get the current exchange rate for a currency pair
        
        Args:
            from_currency (str): Base currency
            to_currency (str): Quote currency
            
        Returns:
            Dict[str, Any]: Exchange rate data
        """
        cache_key = f"forex_rate_{from_currency}_{to_currency}"
        if cache_key in self.cached_data:
            # Use cached data if less than 15 minutes old
            if (datetime.now() - self.cached_data[cache_key]["timestamp"]).total_seconds() < 900:
                return self.cached_data[cache_key]["data"]
        
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency,
            "to_currency": to_currency,
            "apikey": self.api_key
        }
        
        response = requests.get(self.base_url, params=params)
        data = response.json()
        
        # Handle potential error or rate limit responses
        if "Realtime Currency Exchange Rate" in data:
            result = {
                "from_currency": from_currency,
                "to_currency": to_currency,
                "exchange_rate": float(data["Realtime Currency Exchange Rate"]["5. Exchange Rate"]),
                "last_refreshed": data["Realtime Currency Exchange Rate"]["6. Last Refreshed"],
                "time_zone": data["Realtime Currency Exchange Rate"]["7. Time Zone"]
            }
            # Cache the result
            self.cached_data[cache_key] = {
                "data": result,
                "timestamp": datetime.now()
            }
            return result
        elif "Error Message" in data:
            return {"error": data["Error Message"]}
        elif "Information" in data:
            return {"error": "Rate limit reached", "message": data["Information"]}
        else:
            return {"error": "Unexpected response format", "data": data}
    
    def get_price_data_context(self, from_currency="EUR", to_currency="USD") -> str:
        """
        Get a formatted context string with current price data for agents
        
        Args:
            from_currency (str): Base currency
            to_currency (str): Quote currency
            
        Returns:
            str: Formatted price data context
        """
        try:
            # Get current exchange rate
            rate_data = self.get_forex_rate(from_currency, to_currency)
            
            if "error" in rate_data:
                return f"Error getting price data: {rate_data.get('error')}"
            
            # Format context string
            context = f"CURRENT {from_currency}/{to_currency} PRICE DATA:\n\n"
            context += f"Exchange Rate: {rate_data['exchange_rate']:.5f}\n"
            context += f"Last Updated: {rate_data['last_refreshed']} {rate_data['time_zone']}\n"
            
            return context
            
        except Exception as e:
            return f"Error generating price data context: {str(e)}"

# Example usage
if __name__ == "__main__":
    try:
        av_tool = AlphaVantageDataTool()
        result = av_tool._run(from_currency="EUR", to_currency="USD")
        print(result)
        
        # Test direct method call
        rate_data = av_tool.get_forex_rate("EUR", "USD")
        print(f"Current EUR/USD Rate: {rate_data['exchange_rate']:.5f}")
        
        context = av_tool.get_price_data_context("EUR", "USD")
        print("\nPrice Data Context:")
        print(context)
    except Exception as e:
        print(f"Error: {e}")