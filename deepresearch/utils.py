import logging
import time
from functools import wraps
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import json
from dotenv import load_dotenv

load_dotenv() # Load variables from .env file

def setup_logger(name="deepresearch"):
    """Set up and return a robust logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def get_robust_session(retries=3, backoff_factor=0.3, status_forcelist=(429, 500, 502, 503, 504)):
    """Configure a requests Session with retry and backoff."""
    session = requests.Session()
    # Add a real-like User-Agent to avoid 403 Forbidden on sites like Wikipedia
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    })
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def call_llm(prompt: str, system_prompt: str = "You are a helpful research assistant.", groq_key_fn=None) -> str:
    """Call an LLM API (Groq by default) using standard environment variables or a key function."""
    # Use Groq API by default with the key provided
    groq_api_key = groq_key_fn() if groq_key_fn else os.environ.get("GROQ_API_KEY", "")
    
    if not groq_api_key:
        return "GROQ_API_KEY not found. Please add your own key in the MCP config."
    
    if groq_api_key:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"), # Defaults to LLaMA3 70B on Groq
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=30)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            err_details = getattr(e, 'response', '')
            err_text = err_details.text if hasattr(err_details, 'text') else str(e)
            return f"Error calling Groq LLM: {str(e)} - {err_text}"
    
    api_key = os.environ.get("OPENAI_API_KEY", os.environ.get("API_KEY"))
    if api_key:
        # Use OpenAI via requests
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": os.environ.get("OPENAI_MODEL", "gpt-4o"),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=30)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error calling LLM: {str(e)}"
    
    # Fallback to local Ollama if no API key
    try:
        ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
        data = {
            "model": os.environ.get("OLLAMA_MODEL", "llama3"),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }
        resp = requests.post(ollama_url, json=data, timeout=30)
        resp.raise_for_status()
        return resp.json()["message"]["content"]
    except Exception as e:
        return f"Error: No OPENAI_API_KEY set and local Ollama unreachable. Detailed error: {str(e)}"    """Set up and return a robust logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def get_robust_session(retries=3, backoff_factor=0.3, status_forcelist=(429, 500, 502, 503, 504)):
    """Configure a requests Session with retry and backoff."""
    session = requests.Session()
    # Add a real-like User-Agent to avoid 403 Forbidden on sites like Wikipedia
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    })
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def rate_limit(calls: int, period: float):
    """Decorator to limit function execution rate."""
    min_interval = period / float(calls)
    def decorator(func):
        last_called = [0.0]
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator
