# tools/fxstreet_scraper.py
from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import requests
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FXStreetInput(BaseModel):
    limit: int = Field(default=5, description="Number of latest articles to fetch from FXStreet")

class FetchFXNews(BaseTool):
    name: str = "fetch_fxstreet_news"
    description: str = "Fetches the latest EUR/USD headlines from FXStreet"
    args_schema: Type[BaseModel] = FXStreetInput

    def _run(self, limit: int = 5) -> str:
        # Use the specific search URL for EURUSD news
        url = "https://www.fxstreet.com/news?q=&hPP=17&idx=FxsIndexPro&p=0&dFR%5BTags%5D%5B0%5D=EURUSD"
        
        # More comprehensive user-agent to avoid detection
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }
        
        try:
            logger.info(f"Fetching news from {url}")
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # First try the specific search page structure
            articles = self._extract_from_search_page(soup, limit)
            
            # If that fails, try alternative selectors
            if not articles:
                logger.info("No articles found with primary selectors, trying alternatives")
                articles = self._extract_with_alternative_selectors(soup, limit)
            
            if articles:
                logger.info(f"Successfully extracted {len(articles)} articles")
                return "\n\n".join(articles)
            else:
                logger.warning("No articles found with any selectors")
                return "No EUR/USD news articles found. The website structure may have changed or there may be no recent articles."
                
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return f"Error fetching news: {str(e)}"
    
    def _extract_from_search_page(self, soup, limit):
        articles = []
        
        # These selectors are specific to the search results page
        article_containers = soup.select(".fxs_article_showcase")[:limit]
        
        for container in article_containers:
            try:
                # Find the title and link
                title_element = container.select_one(".fxs_article_showcase_header h4 a")
                if not title_element:
                    title_element = container.select_one(".fxs_entryHeading a")
                
                if title_element:
                    title = title_element.text.strip()
                    link = title_element.get("href")
                    if not link.startswith("http"):
                        link = f"https://www.fxstreet.com{link}"
                    
                    # Find the summary
                    summary_element = container.select_one(".fxs_article_showcase_introtext")
                    summary = summary_element.text.strip() if summary_element else ""
                    
                    # Find the date
                    date_element = container.select_one(".fxs_article_showcase_dateAuthor time")
                    date_text = f" ({date_element.text.strip()})" if date_element else ""
                    
                    articles.append(f"- **{title}**{date_text}\n{summary} ([Read more]({link}))")
            except Exception as e:
                logger.error(f"Error extracting article: {e}")
        
        return articles
    
    def _extract_with_alternative_selectors(self, soup, limit):
        articles = []
        
        # Try various common article selectors
        selectors = [
            "article", ".news-item", ".article-item", ".story", 
            ".post", ".entry", "[class*='article']", "[class*='news']"
        ]
        
        for selector in selectors:
            elements = soup.select(selector)[:limit]
            if elements:
                logger.info(f"Found {len(elements)} elements with selector: {selector}")
                
                for element in elements:
                    try:
                        # Look for title
                        title_elem = (element.select_one("h1") or 
                                     element.select_one("h2") or 
                                     element.select_one("h3") or 
                                     element.select_one("h4") or
                                     element.select_one(".title") or
                                     element.select_one("[class*='title']") or
                                     element.select_one("[class*='heading']"))
                        
                        if not title_elem:
                            continue
                            
                        title = title_elem.text.strip()
                        
                        # Look for link
                        link_elem = title_elem.find("a") if title_elem else None
                        if not link_elem:
                            link_elem = element.select_one("a")
                            
                        link = link_elem.get("href", "#") if link_elem else "#"
                        if link and not link.startswith("http"):
                            link = f"https://www.fxstreet.com{link}"
                        
                        # Look for summary
                        summary_elem = (element.select_one("p") or 
                                       element.select_one(".summary") or
                                       element.select_one("[class*='summary']") or
                                       element.select_one("[class*='excerpt']") or
                                       element.select_one("[class*='description']"))
                        
                        summary = summary_elem.text.strip() if summary_elem else ""
                        
                        articles.append(f"- **{title}**\n{summary} ([Read more]({link}))")
                        
                        # If we found enough articles, stop
                        if len(articles) >= limit:
                            break
                            
                    except Exception as e:
                        logger.error(f"Error with alternative extraction: {e}")
                
                # If we found any articles with this selector, we can stop trying others
                if articles:
                    break
        
        return articles

    def run(self, query: str) -> str:
        return "Use structured input with `limit` as number of articles to fetch."
