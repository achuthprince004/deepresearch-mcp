# Deep Research MCP

A powerful Model Context Protocol (MCP) server that enables AI agents to perform structured, multi-step internet research and generate comprehensive reports automatically.

Deep Research MCP equips **Claude web only** with advanced research capabilities including query planning, web search, content extraction, source analysis, and report generation.

Link for endpoint generation: https://deepresearch-mcp.vercel.app/

> [!IMPORTANT]
>
> **Current Status**
>
> Deep Research MCP is available as a **Remote MCP server** and is designed to provide advanced research capabilities through the Model Context Protocol.
>
> The server supports end-to-end research workflows, including planning, web search, content extraction, source analysis, and report generation.
>
> The project is actively maintained and continues to evolve with new research features, improved performance, and enhanced reliability.
>
> Since this instance is deployed on **Render Free tier**, the first connection or tool call after 15 minutes of inactivity may take **30–90 seconds** (cold start).  The same applies for the first connection in claude web connectors too.
>
> Subsequent calls during an active session are much faster.  
>
> This delay is normal for free hosting and mainly affects Claude when starting a new research task after a pause.

## Features

* Deep multi-step internet research
* Research planning and task decomposition
* Multi-provider web search

  * Tavily
  * SerpAPI
  * Google Search
  * DuckDuckGo
* Intelligent webpage scraping and extraction
* LLM-powered source analysis using Groq
* Automatic Markdown report generation
* Research history and report storage
* Remote MCP deployment support
* Open-source and extensible architecture

## MCP Capabilities

Deep Research MCP provides a complete research workflow through MCP tools and resources:

* Generate structured research plans
* Execute iterative web searches
* Extract and analyze webpage content
* Gather and compare information from multiple sources
* Synthesize findings into comprehensive reports
* Store and retrieve research history
* Generate Markdown-based research outputs

The server is designed to help AI agents perform deeper, more reliable research by combining search, extraction, analysis, and reporting into a unified workflow.

## Architecture

Deep Research MCP follows a modular architecture that includes:

* Search providers for information discovery
* Content extraction and scraping components
* LLM-powered analysis and synthesis
* Report generation and storage
* MCP tools and resources for agent interaction

This architecture makes it easy to extend the server with additional search providers, analysis capabilities, and research workflows.
