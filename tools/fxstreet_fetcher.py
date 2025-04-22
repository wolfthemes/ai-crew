from typing import Type, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from datetime import date, datetime, timedelta
import os
import json
import requests
from bs4 import BeautifulSoup
import time
import random
from utils.fxstreet_downloader import get_fxstreet_events

class FXStreetQueryInput(BaseModel):
    currency_pair: str = Field(default="EUR/USD", description="Currency pair to fetch news for")
    days_back: int = Field(default=7, description="Number of days to look back")
    days_forward: int = Field(default=7, description="Number of days to look forward")
    impact_level: str = Field(default="high", description="Impact level: 'high', 'medium', 'low', or 'all'")

class FetchFXStreetNews(BaseTool):
    name: str = "fetch_fxstreet_news"
    description: str = "Fetches forex news and economic calendar events from FXStreet"
    args_schema: Type[BaseModel] = FXStreetQueryInput
    
    # Add cache property
    _cache_file: str = "data/cache/fxstreet_cache.json"
    _cache_expiry: int = 3600  # 1 hour in seconds
    
    class Config:
        arbitrary_types_allowed = True
    
    def _fetch_mock_news(self, currency_pair: str, days_back: int, days_forward: int, impact_level: str) -> List[Dict[str, Any]]:
        """
        Generate mock news data for testing when we can't actually fetch from FXStreet
        
        Returns structured data mimicking what we'd get from the real API
        """
        today = date.today()
        start_date = today - timedelta(days=days_back)
        end_date = today + timedelta(days=days_forward)
        
        # Mock events that would impact EUR/USD
        events = []
        
        # Past events (with actual outcomes)
        events.extend([
            {
                "date": (start_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                "time": "08:30",
                "currency": "EUR",
                "event": "German Manufacturing PMI",
                "impact": "high",
                "actual": "47.8",
                "forecast": "48.2",
                "previous": "48.0",
                "market_reaction": "EUR weakened as manufacturing remained in contraction territory"
            },
            {
                "date": (start_date + timedelta(days=2)).strftime("%Y-%m-%d"),
                "time": "14:00",
                "currency": "USD",
                "event": "US Consumer Confidence",
                "impact": "high",
                "actual": "105.2",
                "forecast": "102.8",
                "previous": "103.1",
                "market_reaction": "USD strengthened on better-than-expected confidence figures"
            },
            {
                "date": (start_date + timedelta(days=3)).strftime("%Y-%m-%d"),
                "time": "12:30",
                "currency": "EUR",
                "event": "ECB Monetary Policy Statement",
                "impact": "high",
                "actual": "Rate unchanged at 3.75%",
                "forecast": "No change",
                "previous": "3.75%",
                "market_reaction": "EUR initially rose then fell as ECB was seen as dovish in press conference"
            },
            {
                "date": (start_date + timedelta(days=4)).strftime("%Y-%m-%d"),
                "time": "08:30",
                "currency": "USD",
                "event": "US Nonfarm Payrolls",
                "impact": "high",
                "actual": "182K",
                "forecast": "170K",
                "previous": "187K",
                "market_reaction": "USD gained modestly as jobs data remained resilient"
            },
            {
                "date": (start_date + timedelta(days=6)).strftime("%Y-%m-%d"),
                "time": "10:00",
                "currency": "EUR",
                "event": "Eurozone CPI YoY",
                "impact": "high",
                "actual": "2.4%",
                "forecast": "2.5%",
                "previous": "2.6%",
                "market_reaction": "EUR declined as inflation came in lower than expected"
            }
        ])
        
        # Upcoming events (forecast only)
        events.extend([
            {
                "date": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
                "time": "12:30",
                "currency": "USD",
                "event": "US Core PCE Price Index MoM",
                "impact": "high",
                "actual": "",
                "forecast": "0.3%",
                "previous": "0.2%"
            },
            {
                "date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
                "time": "09:00",
                "currency": "EUR",
                "event": "Eurozone Unemployment Rate",
                "impact": "medium",
                "actual": "",
                "forecast": "6.4%",
                "previous": "6.5%"
            },
            {
                "date": (today + timedelta(days=3)).strftime("%Y-%m-%d"),
                "time": "14:15",
                "currency": "USD",
                "event": "ADP Employment Change",
                "impact": "high",
                "actual": "",
                "forecast": "165K",
                "previous": "143K"
            },
            {
                "date": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
                "time": "08:30",
                "currency": "USD",
                "event": "US Nonfarm Payrolls",
                "impact": "high",
                "actual": "",
                "forecast": "180K",
                "previous": "182K"
            },
            {
                "date": (today + timedelta(days=6)).strftime("%Y-%m-%d"),
                "time": "10:00",
                "currency": "EUR",
                "event": "ECB President Lagarde Speech",
                "impact": "high",
                "actual": "",
                "forecast": "",
                "previous": ""
            }
        ])
        
        # Filter by impact level if not 'all'
        if impact_level != 'all':
            events = [e for e in events if e['impact'].lower() == impact_level.lower()]
            
        # Sort by date
        events.sort(key=lambda x: (x['date'], x['time']))
        
        # Add news articles
        news_articles = [
            {
                "date": (start_date + timedelta(days=2)).strftime("%Y-%m-%d"),
                "title": "EUR/USD struggles to maintain upward momentum as US dollar recovers",
                "source": "FXStreet",
                "url": "https://www.fxstreet.com/example-article-1",
                "summary": "EUR/USD faced resistance near 1.0850 as the US dollar found support following strong economic data."
            },
            {
                "date": (start_date + timedelta(days=4)).strftime("%Y-%m-%d"),
                "title": "ECB signals potential rate cuts as inflation pressures ease",
                "source": "FXStreet",
                "url": "https://www.fxstreet.com/example-article-2",
                "summary": "European Central Bank officials hinted at possible rate cuts later this year as inflation continues to moderate."
            },
            {
                "date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
                "title": "Federal Reserve maintains hawkish stance, USD gains across the board",
                "source": "FXStreet",
                "url": "https://www.fxstreet.com/example-article-3",
                "summary": "Fed officials pushed back against early rate cut expectations, boosting the US dollar against major currencies."
            },
            {
                "date": today.strftime("%Y-%m-%d"),
                "title": "EUR/USD technical analysis: Key support at 1.0700 under pressure",
                "source": "FXStreet",
                "url": "https://www.fxstreet.com/example-article-4",
                "summary": "The EUR/USD pair is testing critical support at 1.0700, with bears targeting a move toward 1.0650 if broken."
            }
        ]
        
        return {
            "economic_events": events,
            "news_articles": news_articles,
            "currency_pair": currency_pair,
            "generated_at": datetime.now().isoformat(),
            "note": "This data is generated for testing purposes"
        }
    
    def _check_cache(self, currency_pair: str, impact_level: str) -> Optional[Dict[str, Any]]:
        """Check if we have cached data that's still valid"""
        if not os.path.exists(self._cache_file):
            return None
            
        try:
            with open(self._cache_file, 'r') as f:
                cache = json.load(f)
                
            # Check if cache is valid
            if (datetime.now().timestamp() - cache.get('timestamp', 0) < self._cache_expiry and
                cache.get('currency_pair') == currency_pair and
                cache.get('impact_level') == impact_level):
                print("Using cached FXStreet data")
                return cache.get('data')
                
        except Exception as e:
            print(f"Cache error: {e}")
            
        return None
    
    def _save_to_cache(self, data: Dict[str, Any], currency_pair: str, impact_level: str) -> None:
        """Save data to cache"""
        cache = {
            'timestamp': datetime.now().timestamp(),
            'currency_pair': currency_pair,
            'impact_level': impact_level,
            'data': data
        }
        
        try:
            with open(self._cache_file, 'w') as f:
                json.dump(cache, f)
        except Exception as e:
            print(f"Failed to save cache: {e}")
    
    def _fetch_actual_news(self, currency_pair: str, days_back: int, days_forward: int, impact_level: str) -> Dict[str, Any]:
        """
        Attempt to fetch actual news from FXStreet
        This is a template - actual implementation would need to use their API or scrape the site
        """
        today = date.today()
        start_date = today - timedelta(days=days_back)
        end_date = today + timedelta(days=days_forward)
        
        # Fetch Events
        events = get_fxstreet_events()

        # Add news articles
        news_articles = [
            {
                "date": (start_date + timedelta(days=2)).strftime("%Y-%m-%d"),
                "title": "EUR/USD struggles to maintain upward momentum as US dollar recovers",
                "source": "FXStreet",
                "url": "https://www.fxstreet.com/example-article-1",
                "summary": "EUR/USD faced resistance near 1.0850 as the US dollar found support following strong economic data."
            },
            {
                "date": (start_date + timedelta(days=4)).strftime("%Y-%m-%d"),
                "title": "ECB signals potential rate cuts as inflation pressures ease",
                "source": "FXStreet",
                "url": "https://www.fxstreet.com/example-article-2",
                "summary": "European Central Bank officials hinted at possible rate cuts later this year as inflation continues to moderate."
            },
            {
                "date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
                "title": "Federal Reserve maintains hawkish stance, USD gains across the board",
                "source": "FXStreet",
                "url": "https://www.fxstreet.com/example-article-3",
                "summary": "Fed officials pushed back against early rate cut expectations, boosting the US dollar against major currencies."
            },
            {
                "date": today.strftime("%Y-%m-%d"),
                "title": "EUR/USD technical analysis: Key support at 1.0700 under pressure",
                "source": "FXStreet",
                "url": "https://www.fxstreet.com/example-article-4",
                "summary": "The EUR/USD pair is testing critical support at 1.0700, with bears targeting a move toward 1.0650 if broken."
            }
        ]
        
        return {
            "economic_events": events,
            "news_articles": news_articles,
            "currency_pair": currency_pair,
            "generated_at": datetime.now().isoformat(),
            "note": "This data is generated for testing purposes"
        }
    
    def _run(self, currency_pair: str = "EUR/USD", days_back: int = 7, days_forward: int = 7, impact_level: str = "high") -> str:
        """Fetch news and economic events from FXStreet"""
        
        # Check cache first
        cached_data = self._check_cache(currency_pair, impact_level)
        if cached_data:
            return json.dumps(cached_data, indent=2)
        
        try:
            # Fetch data (using mock for now)
            data = self._fetch_actual_news(currency_pair, days_back, days_forward, impact_level)
            
            # Save to cache
            self._save_to_cache(data, currency_pair, impact_level)
            
            # Format the response as JSON
            return json.dumps(data, indent=2)
            
        except Exception as e:
            return f"Error fetching FXStreet news: {str(e)}"
    
    def run(self, query: str) -> str:
        return "Use structured input with currency_pair, days_back, days_forward, and impact_level parameters."