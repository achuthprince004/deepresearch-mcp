# Deep Research MCP

A Model Context Protocol (MCP) server for deep internet research.

## Installation

1. Clone this repository to your local machine.
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```
3. Install the specific dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up the environment variables:
   ```bash
   cp .env.example .env
   ```

## Running the Server

### Stdio Mode (Cursor/VSCode)
This is the default mode used by MCP clients if explicitly configured via a config file. See the provided `mcp.json.example` for details on how to configure your cursor or VSCode settings to point to this MCP integration.

### HTTP/SSE Mode
To run the server over HTTP using Server-Sent Events (SSE):

```bash
python run.py --http
```
The server will run at the `PORT` and `HOST` configured within your `.env` file (Default: http://127.0.0.1:8000).

### Remote Access (with ngrok)
If you are running the HTTP/SSE server locally but need to expose it securely to an external service, you can use `ngrok`.

1. Install and authenticate `ngrok`.
2. Start the MCP server: `python run.py --http`
3. Expose the port through ngrok (assuming port 8000):
   ```bash
   ngrok http 8000
   ```
4. Update your remote application to point to the secure `https` URL provided by ngrok.
