from fastmcp import FastMCP, Context
import os
import contextlib
from dotenv import load_dotenv

import mcp.server.sse
from starlette.requests import Request

load_dotenv()

from contextvars import ContextVar

# 1. Use ContextVar to implicitly track keys across async calls
current_groq_key: ContextVar[str] = ContextVar('groq_key', default='')
current_tavily_key: ContextVar[str] = ContextVar('tavily_key', default='')

# 2. Override the SSE connection handler to extract and set keys into context
original_connect_sse = mcp.server.sse.SseServerTransport.connect_sse

@contextlib.asynccontextmanager
async def custom_connect_sse(self, scope, receive, send):
    req = Request(scope, receive)
    groq_key = req.query_params.get("groq_key", req.query_params.get("GROQ_API_KEY", ""))
    tavily_key = req.query_params.get("tavily_key", req.query_params.get("TAVILY_API_KEY", ""))
    
    # Store in current context. Since FastMCP routes all tool executions for this connection 
    # from tasks spawned within this context manager, the ContextVars automatically propagate!
    current_groq_key.set(groq_key)
    current_tavily_key.set(tavily_key)
    
    async with original_connect_sse(self, scope, receive, send) as streams:
        yield streams

mcp.server.sse.SseServerTransport.connect_sse = custom_connect_sse

# 3. Simple getter functions that pull from ContextVar
def get_groq_key(ctx=None):
    return current_groq_key.get() or os.getenv("GROQ_API_KEY", "")

def get_tavily_key(ctx=None):
    return current_tavily_key.get() or os.getenv("TAVILY_API_KEY", "")

from deepresearch.tools import (
    plan_research,
    search_web,
    scrape_page,
    summarize_text,
    analyze_sources,
    generate_final_report,
    save_research
)
from deepresearch.research_workflow import run_deep_research

# Instantiate FastMCP server
mcp = FastMCP("DeepResearch")

# Register tools using @mcp.tool()

@mcp.tool()
def plan_research_tool(topic: str, ctx: Context = None) -> list:
    """
    Parses a broad research topic and breaks it down into 5 targeted, highly-specific sub-questions.
    Always use this FIRST to figure out exactly what searches to perform for deep research.
    """
    return plan_research(topic, groq_key_fn=lambda: get_groq_key(ctx))

@mcp.tool()
def search_web_tool(query: str, num_results: int = 8, ctx: Context = None) -> list:
    """
    Executes a web search for a specific query and returns URLs, titles, and snippets.
    Call this AFTER planning to find relevant sources for each sub-question.
    """
    return search_web(query, num_results, tavily_key_fn=lambda: get_tavily_key(ctx))

@mcp.tool()
def scrape_page_tool(url: str, ctx: Context = None) -> str:
    """
    Downloads and extracts clean readable text from a single webpage URL.
    Call this on the best URLs returned by search_web_tool.
    """
    return scrape_page(url)

@mcp.tool()
def summarize_text_tool(text: str, focus_area: str = None, ctx: Context = None) -> str:
    """Summarize long text content."""
    return summarize_text(text, focus_area)

@mcp.tool()
def analyze_sources_tool(topic: str, sources: list, ctx: Context = None) -> str:
    """
    Cross-references and extracts facts, data, and contradictions from a list of scraped sources.
    Expects a list of dictionaries containing {"url": "...", "content": "..."}.
    Call this AFTER scraping all necessary pages.
    """
    return analyze_sources(topic, sources, groq_key_fn=lambda: get_groq_key(ctx))

@mcp.tool()
def generate_final_report_tool(topic: str, analysis: str, sub_questions: list, sources: list, ctx: Context = None) -> str:
    """
    Formats the raw analysis, sub_questions, and sources into a clean Markdown report.
    Call this toward the end of the research pipeline to compose the final artifact.
    """
    return generate_final_report({
        "topic": topic,
        "analysis": analysis,
        "sub_questions": sub_questions,
        "sources": sources
    })

@mcp.tool()
def save_research_tool(topic: str, report: str, ctx: Context = None) -> dict:
    """
    Saves the finalized Markdown report to the local disk.
    Always call this at the very end of your workflow to persist the data.
    """
    return save_research(topic, report)

@mcp.tool()
def run_deep_research_tool(topic: str, ctx: Context = None) -> str:
    """
    Executes a fully autonomous end-to-end deep research workflow locally.
    It plans, searches, scrapes, analyzes, and saves a report automatically.
    Returns the FULL markdown report content back to you.
    """
    return run_deep_research(topic, groq_key_fn=lambda: get_groq_key(ctx), tavily_key_fn=lambda: get_tavily_key(ctx))
