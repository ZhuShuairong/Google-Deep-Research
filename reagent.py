import requests
from bs4 import BeautifulSoup
from langchain_ollama import OllamaLLM
import csv
from datetime import datetime
import os
from playwright.sync_api import sync_playwright
import time
import random

# API Configuration
GOOGLE_CSE_ID = "" #Your Google programmable search engine api key (free)
GOOGLE_API_KEY = ""  #Your Google custom search api key (free)
MODEL_NAME = "granite3.3:2b" #Your own OLLAMA downloaded model here, I used granite3.3:2b for fast text summary as I'm running on a 5060

def get_google_urls(query: str, num_results: int = 20) -> list:
    """Get list of URLs from Google Search for the given query, up to num_results."""
    urls = []
    start = 1
    
    while len(urls) < num_results:
        num = min(10, num_results - len(urls))
        try:
            url = f"https://www.googleapis.com/customsearch/v1?q={query}&cx={GOOGLE_CSE_ID}&key={GOOGLE_API_KEY}&start={start}&num={num}"
            response = requests.get(url)
            response.raise_for_status()
            results = response.json()
            
            if 'items' not in results or not results['items']:
                break
            
            items = results['items']
            for item in items:
                urls.append(item['link'])
                if len(urls) >= num_results:
                    break
            
            if len(items) < num:
                break
            
            start += 10
        
        except Exception as e:
            print(f"Error fetching results: {e}")
            break
    
    return urls

def fetch_web_content(url: str) -> str:
    """Fetch and clean webpage content from the given URL using Playwright with fallback to BeautifulSoup"""
    
    # Try Playwright first with human-like settings
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Set human-like headers
            page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            })
            
            # Navigate to the page with realistic timing
            page.goto(url, timeout=15000)
            
            # Add some realistic waiting
            time.sleep(random.uniform(0.5, 2.0))
            
            # Wait for page to load
            page.wait_for_load_state("networkidle")
            
            # Scroll to simulate human behavior
            page.evaluate("window.scrollTo(0, document.body.scrollHeight/3)")
            time.sleep(random.uniform(0.2, 0.8))
            
            # Get the page content
            content = page.content()
            browser.close()
            
            # Clean the content
            soup = BeautifulSoup(content, 'html.parser')
            for tag in soup(['script', 'style', 'img', 'form', 'iframe', 'nav', 'footer']):
                tag.decompose()
            text = soup.get_text(separator=' ', strip=True)
            cleaned_text = ' '.join(text.split())
            
            if len(cleaned_text) > 100:  # If we got meaningful content
                return cleaned_text
                
    except Exception as e:
        print(f"Playwright failed for {url}: {str(e)}")
    
    # Fallback to BeautifulSoup if Playwright fails
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        for tag in soup(['script', 'style', 'img', 'form', 'iframe', 'nav', 'footer']):
            tag.decompose()
        text = soup.get_text(separator=' ', strip=True)
        cleaned_text = ' '.join(text.split())
        
        return cleaned_text if len(cleaned_text) > 100 else f"Content too short from {url}"
        
    except Exception as e:
        return f"Could not retrieve content from {url}: {str(e)}"

def save_to_csv(urls: list, contents: list, filename: str = None):
    """Save URLs and their contents to a CSV file with current datetime as filename"""
    if not filename:
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scraped_content_{now}.csv"
    
    # Ensure the filename has .csv extension
    if not filename.lower().endswith('.csv'):
        filename += '.csv'
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['url', 'content'])
            for url, content in zip(urls, contents):
                writer.writerow([url, content])
        print(f"\nData saved to {os.path.abspath(filename)}")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

class DeepResearchAgent:
    def __init__(self):
        """Initialize the research agent with Ollama model"""
        self.llm = OllamaLLM(model=MODEL_NAME, temperature=0.1)

    def research(self, query: str, save_csv: bool = True) -> str:
        """Perform research on the given query using Google Search and Ollama model"""
        try:
            urls = get_google_urls(query, num_results=20)
            if not urls:
                return "No search results found for the query."
            
            print("\nSEARCH RESULTS:")
            for i, url in enumerate(urls, 1):
                print(f"{i}. {url}")
            
            # Let user select which URLs to scrape
            print("\nSelect which URLs to scrape (enter numbers separated by spaces, e.g. '1 3 5')")
            print("You can select up to 5 URLs.")
            selected_indices = []
            while True:
                try:
                    user_input = input("> ")
                    indices = [int(idx) - 1 for idx in user_input.split() if idx.isdigit()]
                    indices = [idx for idx in indices if 0 <= idx < len(urls)]
                    selected_indices = list(set(indices))[:5]  # Remove duplicates and limit to 5
                    if selected_indices:
                        break
                    print("Please select at least one valid URL number.")
                except ValueError:
                    print("Please enter numbers only.")
            
            selected_urls = [urls[i] for i in selected_indices]
            contexts = [fetch_web_content(url) for url in selected_urls]
            
            # Save to CSV if requested
            if save_csv:
                save_to_csv(selected_urls, contexts)
            
            full_context = "\n\n".join(contexts)
            prompt = f"You are a helpful research assistant, Help me synthesize the information from the context based on the query. Query: {query}\n\nContext: {full_context}" #Adjust prompt to your needs here
            answer = self.llm.invoke(prompt)
            return answer
        except Exception as e:
            return f"Error during research: {str(e)}"

def main():
    """Command-line interface for the research system"""
    researcher = DeepResearchAgent()
    while True:
        query = input("\nEnter your research question (or type 'exit' to quit):\n> ")
        if query.lower() in ['exit', 'quit']:
            break
        if not query.strip():
            print("Please enter a valid question")
            continue
        result = researcher.research(query)
        print("\nRESEARCH REPORT:")
        print(result)

if __name__ == "__main__":
    main()
