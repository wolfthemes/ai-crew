# 🧠 AI Crew

A modular AI assistant team powered by CrewAI, OpenAI, and LangChain — built to automate my support workflow, WordPress development, trading insights, and more.

## ✅ Features

- Support agent replies to customer tickets in my natural tone
- Modular structure for adding new agents (dev, trading, RSS, etc.)
- Future integration with Ticksy, Notion, GitHub, and FX feeds

## 📁 Project Layout

- agents/ — agent definitions  
- tasks/ — agent tasks  
- crews/ — crew orchestration  
- main.py — main entry point  
- .env.example — environment variable template  

## ⚙️ Setup

1. Create a virtual environment:  
   `python -m venv venv`

2. Activate it (Windows):  
   `source venv/Scripts/activate`

3. Install dependencies:  
   `pip install -r requirements.txt`

4. Create a `.env` file like:

OPENAI_API_KEY=your-key
NOTION_API_KEY=your-key
GITHUB_USERNAME=your-username
GITHUB_TOKEN=your-key
TICKSY_DOMAIN=your-username
TICKSY_API_KEY=your-key

---

Private project. Built to save time and scale with AI.