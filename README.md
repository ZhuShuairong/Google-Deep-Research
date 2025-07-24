# Deep Research Agent

🔍 **Deep Research Agent** is an AI-powered research assistant that automatically searches the web, scrapes relevant content, and synthesizes comprehensive reports using a local LLM (via Ollama). It supports both a **command-line interface (CLI)** and a **web-based GUI** built with Streamlit.

```mermaid
graph TD
    A[User Input: Research Query] --> B{Start Research?}
    B -->|Yes| C[Fetch URLs via Google Custom Search API]
    C --> D[Display Top URLs (1–20)]
    D --> E[User Selects 1–5 URLs to Analyze]
    E --> F[Scrape Content from Selected URLs]
    F --> G{Use Playwright first<br>(with human-like behavior)}
    G -->|Success| H[Clean HTML (remove scripts, ads, etc.)]
    G -->|Fail| I[Fallback to BeautifulSoup]
    I --> H
    H --> J[Extract Clean Text Content]
    J --> K[Aggregate All Contexts]
    K --> L[Generate Prompt for LLM]
    L --> M[Ollama LLM (granite3.3:2b) Synthesizes Report]
    M --> N[Display Final Research Report]
    N --> O{Save Data?}
    O -->|Yes| P[Save to CSV: URLs only]
    O -->|Yes| Q[Save JSON to /research_history]
    O --> R[Show in UI & Add to History Sidebar]
    P --> R
    Q --> R
    R --> S[User Can Revisit Past Research]
```

The agent uses:
- **Google Programmable Search Engine (CSE)** to find relevant URLs.
- **Playwright + BeautifulSoup** to scrape and clean web content.
- **Ollama** with a local language model (`granite3.3:2b`) to generate synthesized research reports.
- **Streamlit** for a user-friendly web interface.

---

## 📦 Features

- 🔎 Web search via Google CSE API
- 🕸️ Robust web scraping with anti-bot evasion (Playwright)
- 🧹 Clean text extraction (removes scripts, ads, navigation, etc.)
- 🤖 Report synthesis using a local LLM (no data sent to cloud)
- 🖥️ Interactive GUI with Streamlit
- 💾 Auto-saves research history and exports to CSV/JSON
- 📚 Persistent research history with timestamps

---

## 🛠️ Prerequisites

Before running the project, ensure you have:

1. **Python 3.9+**
2. **Ollama** installed and running: https://ollama.com
   - Pull the model: `ollama pull granite3.3:2b`
3. **Google API Key** and **Custom Search Engine (CSE) ID**
   - Get them from: https://developers.google.com/custom-search/v1/introduction
4. **Playwright** dependencies installed

## Running it all

pip install -r requirements.txt
ollama run granite3.3:2b
playwright install chromium
streamlit run research_gui.py
