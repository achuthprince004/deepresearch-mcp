import argparse
import os
from dotenv import load_dotenv

from deepresearch.server import mcp

def main():
    # Load environment variables (e.g. host, port, API keys)
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="DeepResearch MCP Server")
    parser.add_argument("--http", action="store_true", help="Run server over HTTP/SSE instead of stdio")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)), help="Port to listen on for HTTP/SSE (default: 8000 or $PORT)")
    parser.add_argument("--host", type=str, default=os.environ.get("HOST", "0.0.0.0"), help="Host to bind to for HTTP/SSE (default: 0.0.0.0 or $HOST)")
    args = parser.parse_args()
    
    if args.http:
        print(f"Starting DeepResearch MCP over SSE on {args.host}:{args.port}...")
        mcp.run(transport='sse', host=args.host, port=args.port)
    else:
        mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
