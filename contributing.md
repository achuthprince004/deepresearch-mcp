## Contributing

Contributions are welcome!

We are especially looking for contributors interested in:

* **AI IDE compatibility** (Cursor, VS Code, Windsurf, etc.)
* Currently, this MCP is limited to Groq as its LLM provider. We would love to expand **support to additional providers** such as Anthropic, OpenAI, and others, enabling broader compatibility and making the MCP accessible across a wider range of AI ecosystems.
* **Claude Desktop & Claude Code support** (query params handling, cold starts)
* Improving **connectivity on free hosting platforms** (Render free tier 15-minute sleep / cold start delays)
* **MCP specification compliance** and remote SSE reliability
* Research workflow optimization
* Better cold-start handling and keep-alive mechanisms
* Documentation improvements

> **Note**: The current deployment on Render Free tier has a known limitation — after 15 minutes of inactivity the service sleeps, causing 30–90 second delays on the next request. Contributions that help reduce or eliminate this issue (especially for AI IDEs) are highly appreciated.

Please read `CONTRIBUTING.md` before opening issues or pull requests.
