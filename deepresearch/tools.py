import os
import json
import uuid
from datetime import datetime
import requests

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None
    
try:
    from googlesearch import search as google_search
except ImportError:
    google_search = None

try:
    import trafilatura
except ImportError:
    trafilatura = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from deepresearch.utils import setup_logger, get_robust_session, rate_limit, call_llm

logger = setup_logger("tools")

def plan_research(topic: str, groq_key_fn=None) -> list:
    """Return structured sub-questions about the topic."""
    logger.info(f"Planning research for topic: {topic}")
    
    system_prompt = "You are an expert research planner. Output your response ONLY as a valid JSON array of strings."
    prompt = f"Given this research topic, generate 5 specific, targeted research sub-questions that would together provide comprehensive coverage of the topic. Return EXACTLY a JSON array of strings. Topic: {topic}"
    
    response_text = call_llm(prompt, system_prompt=system_prompt, groq_key_fn=groq_key_fn)
    
    if "GROQ_API_KEY not found." in response_text:
        raise ValueError(response_text)
    
    try:
        # Try to parse the JSON array
        # Simple extraction in case LLM wraps in markdown
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()
            
        questions = json.loads(json_str)
        if isinstance(questions, list) and len(questions) > 0:
            return questions
    except Exception as e:
        logger.error(f"Failed to parse LLM planning output: {e}\nRaw output: {response_text}")
            
    # Intelligent fallback if JSON parsing fails
    return [
        f"What is the current state and definition of {topic}?",
        f"What are the historical origins and evolution of {topic}?",
        f"Who are the key figures or organizations driving {topic}?",
        f"What are the primary applications or use cases of {topic}?",
        f"What are the main challenges or criticisms regarding {topic}?",
        f"What are the future trends or predictions for {topic}?",
    ]

@rate_limit(calls=1, period=2.0)
def search_web(query: str, num_results: int = 8, tavily_key_fn=None) -> list:
    """Search the web using SerpAPI, Tavily, Google, or DDG."""
    logger.info(f"Searching web for: {query} (max {num_results} results)")
    results = []
    
    tavily_api_key = tavily_key_fn() if tavily_key_fn else os.environ.get("TAVILY_API_KEY")
    if tavily_api_key:
        try:
            resp = requests.post(
                "https://api.tavily.com/search",
                json={"api_key": tavily_api_key, "query": query, "search_depth": "advanced", "max_results": num_results},
                timeout=15
            )
            resp.raise_for_status()
            for r in resp.json().get('results', []):
                results.append({
                    'title': r.get('title', ''),
                    'url': r.get('url', ''),
                    'snippet': r.get('content', '')
                })
            if results: return results
        except Exception as e:
            logger.error(f"Error during Tavily search: {e}")

    serpapi_key = os.environ.get("SERPAPI_API_KEY")
    if serpapi_key:
        try:
            resp = requests.get(
                "https://serpapi.com/search",
                params={"q": query, "api_key": serpapi_key, "num": num_results},
                timeout=15
            )
            resp.raise_for_status()
            for r in resp.json().get('organic_results', []):
                results.append({
                    'title': r.get('title', ''),
                    'url': r.get('link', ''),
                    'snippet': r.get('snippet', '')
                })
            if results: return results
        except Exception as e:
            logger.error(f"Error during SerpAPI search: {e}")
            
    if google_search:
        try:
            search_gen = google_search(query, num_results=num_results, advanced=True)
            for r in search_gen:
                results.append({
                    'title': getattr(r, 'title', ''),
                    'url': getattr(r, 'url', ''),
                    'snippet': getattr(r, 'description', '')
                })
            if results:
                return results
        except Exception as e:
            logger.error(f"Error during Google search: {e}")
            
    if DDGS:
        try:
            with DDGS() as ddgs:
                search_gen = ddgs.text(query, max_results=num_results)
                for r in search_gen:
                    results.append({
                        'title': r.get('title', ''),
                        'url': r.get('href', ''),
                        'snippet': r.get('body', '')
                    })
            if results:
                return results
        except Exception as e:
            logger.error(f"Error during DuckDuckGo search: {e}")
    
    # Final fallback if ALL real searches fail
    logger.warning("Search backends unavailable or failed. Returning fallback empty results.")
    return []

def scrape_page(url: str) -> str:
    """Scrape text from a URL using trafilatura, fallback to beautifulsoup4."""
    logger.info(f"Scraping page: {url}")
    session = get_robust_session()
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        
        # Prevent scraping binary files like PDFs which cause encoding corruption
        content_type = response.headers.get('Content-Type', '').lower()
        if 'application/pdf' in content_type or url.lower().endswith('.pdf'):
            return f"Skipped PDF file to avoid encoding corruption: {url}"
            
        # We also might want to skip other binary files, but focusing on PDF for now is good.
        html_content = response.text
        
        # Try trafilatura first for clean text extraction
        if trafilatura:
            text = trafilatura.extract(html_content)
            if text:
                return text
        
        # Fallback to BeautifulSoup
        if BeautifulSoup:
            soup = BeautifulSoup(html_content, 'html.parser')
            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text(separator=' ')
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            return '\n'.join(chunk for chunk in chunks if chunk)
            
        return html_content
    except Exception as e:
        logger.error(f"Failed to scrape {url}: {e}")
        return f"Error scraping URL: {str(e)}"

def summarize_text(text: str, focus_area: str = None) -> str:
    """Mock text summarization function."""
    logger.info(f"Summarizing text (length: {len(text)})" + (f" focused on {focus_area}" if focus_area else ""))
    summary = text[:400] + "..." if len(text) > 400 else text
    if focus_area:
        return f"[Focus: {focus_area}] Summary: {summary}"
    return f"Summary: {summary}"

def analyze_sources(topic: str, sources: list, groq_key_fn=None) -> str:
    """Intelligent synthesis function returning insights from sources."""
    logger.info(f"Analyzing {len(sources)} sources for topic: {topic}")
    if not sources:
        return "No sources provided to analyze."
    
    # Prepare sources for LLM
    sources_text = ""
    for i, source in enumerate(sources):
        url = source.get('url', f'Source {i+1}')
        body_text = source.get('content') or source.get('snippet', '')
        # Truncate each source a bit to prevent massive context context limits
        content_preview = body_text[:2000]
        sources_text += f"\n--- Source {i+1} : {url} ---\n{content_preview}\n"
        
    system_prompt = "You are an expert research analyst."
    prompt = f"Cross-reference the following sources. Extract key facts, identify any contradictions, note data gaps, and synthesize the key findings relevant to the topic: '{topic}'.\n\nSources:\n{sources_text}"
    
    analysis = call_llm(prompt, system_prompt=system_prompt, groq_key_fn=groq_key_fn)
    if "GROQ_API_KEY not found." in analysis:
        raise ValueError(analysis)
    
    if "Error:" in analysis and len(analysis) < 200:
        # Fallback to the old method if LLM fails
        analysis = "### Synthesized Analysis (LLM Fallback)\n\n"
        for i, source in enumerate(sources):
            title = source.get('title', f'Source {i+1}')
            url = source.get('url', '')
            body_text = source.get('content') or source.get('snippet', '')
            content_preview = body_text[:300] + ('...' if len(body_text) > 300 else '')
            analysis += f"- **{title}** ({url}):\n  {content_preview}\n\n"
        analysis += f"\n**Overall Insight**: The combined {len(sources)} sources highlight diverse perspectives and detailed information concerning {topic}.\n(LLM Error: {analysis})"
    else:
        analysis = f"### Synthesized Analysis\n\n{analysis}\n"
        
    return analysis

def generate_final_report(research_data: dict) -> str:
    """Builds a markdown report from the research data."""
    logger.info("Generating final report.")
    topic = research_data.get('topic', 'Unknown Topic')
    analysis = research_data.get('analysis', 'No analysis available.')
    sub_questions = research_data.get('sub_questions', [])
    sources = research_data.get('sources', [])
    
    report = f"# Comprehensive Research Report: {topic}\n\n"
    report += f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    
    report += "## 1. Key Questions Explored\n"
    for q in sub_questions:
        report += f"- {q}\n"
        
    report += "\n## 2. Analysis & Synthesis\n"
    report += f"{analysis}\n"
    
    report += "\n## 3. Sources Referenced\n"
    for i, s in enumerate(sources):
        title = s.get('title', 'Unknown Title')
        url = s.get('url', 'Unknown URL')
        report += f"{i+1}. [{title}]({url})\n"
        
    return report

def save_research(topic: str, report: str) -> dict:
    """Save markdown and JSON in research_history directory."""
    logger.info(f"Saving research for topic: {topic}")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    _raw_path = os.getenv("RESEARCH_OUTPUT_DIR", "./research_history")
    
    # Resolve relative paths against the project root directory
    if not os.path.isabs(_raw_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        history_dir = os.path.normpath(os.path.join(base_dir, _raw_path))
    else:
        history_dir = _raw_path

    os.makedirs(history_dir, exist_ok=True)
    
    safe_topic = "".join([c if c.isalnum() else "_" for c in topic])[:50]
    run_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    file_prefix = f"{timestamp}_{safe_topic}_{run_id}"
    md_path = os.path.join(history_dir, f"{file_prefix}.md")
    json_path = os.path.join(history_dir, f"{file_prefix}.json")
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(report)
        
    metadata = {
        'topic': topic,
        'timestamp': timestamp,
        'run_id': run_id,
        'report_path': md_path
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=4)
        
    logger.info(f"Research saved successfully: {md_path}")
    return metadata
