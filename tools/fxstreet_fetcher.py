from typing import Type, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from datetime import date, datetime, timedelta
import os
import json
import time
from utils.fxstreet_events_downloader import get_fxstreet_events
from utils.fxstreet_news_scraper import get_eurusd_news

class FXStreetQueryInput(BaseModel):
    currency_pair: str = Field(default="EUR/USD", description="Currency pair to fetch news for")
    days_back: int = Field(default=7, description="Number of days to look back")
    days_forward: int = Field(default=7, description="Number of days to look forward")
    impact_level: str = Field(default="high", description="Impact level: 'high', 'medium', 'low', or 'all'")
    report_type: str = Field(default="weekly", description="Report type: 'weekly' or 'daily'")

class FetchFXStreetNews(BaseTool):
    name: str = "fetch_fxstreet_news"
    description: str = "Fetches forex news and economic calendar events from FXStreet"
    args_schema: Type[BaseModel] = FXStreetQueryInput
    
    # Add cache property
    _cache_file: str = "data/cache/fxstreet_cache.json"
    _cache_expiry: int = 3600  # 1 hour in seconds
    
    class Config:
        arbitrary_types_allowed = True
    
    def _get_mock_news_articles(self, start_date, end_date, today):
        """Generate mock news articles for testing"""
        return [
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
    
    def _check_cache(self, currency_pair: str, impact_level: str, report_type: str) -> Optional[Dict[str, Any]]:
        """Check if we have cached data that's still valid"""
        if not os.path.exists(self._cache_file):
            return None
            
        try:
            with open(self._cache_file, 'r') as f:
                cache = json.load(f)
                
            # Check if cache is valid
            if (datetime.now().timestamp() - cache.get('timestamp', 0) < self._cache_expiry and
                cache.get('currency_pair') == currency_pair and
                cache.get('impact_level') == impact_level and
                cache.get('report_type') == report_type):
                print("Using cached FXStreet data")
                return cache.get('data')
                
        except Exception as e:
            print(f"Cache error: {e}")
            
        return None
    
    def _save_to_cache(self, data: Dict[str, Any], currency_pair: str, impact_level: str, report_type: str) -> None:
        """Save data to cache"""
        os.makedirs(os.path.dirname(self._cache_file), exist_ok=True)
        cache = {
            'timestamp': datetime.now().timestamp(),
            'currency_pair': currency_pair,
            'impact_level': impact_level,
            'report_type': report_type,
            'data': data
        }
        
        try:
            with open(self._cache_file, 'w') as f:
                json.dump(cache, f)
        except Exception as e:
            print(f"Failed to save cache: {e}")
    
    def _fetch_economic_events(self, report_type, impact_level):
        """
        Fetch economic events based on report type
        
        Args:
            report_type (str): Either 'weekly' or 'daily'
            impact_level (str): Filter by impact level
            
        Returns:
            list: Economic events
        """
        # Get events from the downloader module
        if report_type == "daily":
            events = get_fxstreet_events(period="day")
        else:  # weekly or any other value
            events = get_fxstreet_events(period="week")
            
        # Filter by impact level if not 'all'
        if impact_level != 'all':
            events = [e for e in events if e.get('impact', '').lower() == impact_level.lower()]
            
        # Sort by date and time
        events.sort(key=lambda x: (x.get('date', ''), x.get('time', '')))
        
        return events
    
    def _fetch_news_data(self, currency_pair: str, days_back: int, days_forward: int, impact_level: str, report_type: str) -> Dict[str, Any]:
        """
        Fetch FXStreet data for both weekly and daily reports
        """
        today = date.today()
        start_date = today - timedelta(days=days_back)
        end_date = today + timedelta(days=days_forward)
        
        # Handle Sunday edge case - if today is Sunday, also fetch next week's data
        is_sunday = datetime.now().weekday() == 6
        
        # Fetch Economic Events based on report type
        if report_type == "daily":
            # For daily report, just get today's events
            economic_events = get_fxstreet_events(period="day")
        elif is_sunday and report_type == "weekly":
            # On Sunday, get both this week and next week
            current_week_events = get_fxstreet_events(period="week")
            next_week_events = get_fxstreet_events(period="next_week")
            
            # Combine the events
            economic_events = current_week_events + next_week_events
        else:
            # Regular weekly report
            economic_events = get_fxstreet_events(period="week")
        
        # Filter by impact level if not 'all' <- Not relevant as we only need the major news
        if impact_level != 'all':
            economic_events = [e for e in economic_events if e.get('impact', '').lower() == impact_level.lower()]
            
        # Sort by date and time
        economic_events.sort(key=lambda x: (x.get('date', ''), x.get('time', '')))
        
        # Add news articles (currently using mock data)
        news_articles = get_eurusd_news()
        
        # For daily reports, filter news to only show today's news
        if report_type == "daily":
            today_str = today.strftime("%Y-%m-%d")
            news_articles = [n for n in news_articles if n.get('date') == today_str]
        
        return {
            "economic_events": economic_events,
            "news_articles": news_articles,
            "currency_pair": currency_pair,
            "report_type": report_type,
            "generated_at": datetime.now().isoformat()
        }
    
    def _run(self, currency_pair: str = "EUR/USD", days_back: int = 7, days_forward: int = 7, 
             impact_level: str = "high", report_type: str = "weekly") -> str:
        """Fetch news and economic events from FXStreet"""
        
        # Check cache first
        cached_data = self._check_cache(currency_pair, impact_level, report_type)
        if cached_data:
            return json.dumps(cached_data, indent=2)
        
        try:
            # Fetch data based on report type
            data = self._fetch_news_data(currency_pair, days_back, days_forward, impact_level, report_type)
            
            # Save to cache
            self._save_to_cache(data, currency_pair, impact_level, report_type)
            
            # Format the response as JSON
            return json.dumps(data, indent=2)
            
        except Exception as e:
            return f"Error fetching FXStreet news: {str(e)}"
    
    def run(self, query: str) -> str:
        return "Use structured input with currency_pair, days_back, days_forward, impact_level, and report_type parameters."