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
        url = "https://www.fxstreet.com/currencies/eurusd"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")

        articles = []
        for article in soup.select(".news-item")[:limit]:
            title = article.select_one(".title").text.strip()
            link = article.select_one("a")["href"]
            summary = article.select_one(".description")
            summary_text = summary.text.strip() if summary else ""
            articles.append(f"- **{title}**\n{summary_text} ([Read more]({link}))")

        return "\n\n".join(articles) if articles else "No articles found."

    def run(self, query: str) -> str:
        return "Use structured input with `limit` as number of articles to fetch."
