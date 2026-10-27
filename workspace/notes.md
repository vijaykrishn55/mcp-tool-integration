
**The project mental model :**

1. Initialize: The client and server establish the MCP session through the handshake.
2. Discover: The client learns which resources, tools, and prompts are available.
3. Invoke: The client sends a standard MCP request, such as reading a resource or calling a tool.
4. Respond:  Python handler performs the operation and returns data or a structured error.
