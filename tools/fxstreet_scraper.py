# tools/fxstreet_scraper.py
from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import requests
from bs4 import BeautifulSoup

class FXStreetInput(BaseModel):
    limit: int = Field(default=5, description="Number of latest articles to fetch from FXStreet")

class FetchFXNews(BaseTool):
    name: str = "fetch_fxstreet_news"
    description: str = "Fetches the latest EUR/USD headlines from FXStreet"
    args_schema: Type[BaseModel] = FXStreetInput

    def _run(self, limit: int = 5) -> str:
        url = "https://www.fxstreet.com/news?q=&hPP=17&idx=FxsIndexPro&p=0&dFR%5BTags%5D%5B0%5D=EURUSD"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")

        articles = []
        for article in soup.select("#hits article")[:limit]:
            title = article.select_one(".fxs_headline_tiny > a").text.strip()
            link = article.select_one("a")["href"]
            time = article.select_one(".time")
            #summary_text = summary.text.strip() if summary else ""
            articles.append(f"- **{title}**\n{time} ([Read more]({link}))")

        return "\n\n".join(articles) if articles else "No articles found."

    def run(self, query: str) -> str:
        return "Use structured input with `limit` as number of articles to fetch."
