# IBM Bob & Langflow MCP Integration Guide

This guide details how to expose CustomsGuard flows as MCP tools in Langflow and connect them directly to IBM Bob.

## 1. Access Langflow Web UI

1. Open your web browser and navigate to `http://localhost:7860`.
2. Login credentials (configured in `.env`):
   - **Username**: `admin`
   - **Password**: `admin123`
3. Verify that the dashboard loads successfully.

## 2. Configure Model Provider in Langflow (Ollama Qwen 2.5 3B)

For a 100% on-premise, air-gapped setup without external API keys, configure Langflow to use Ollama:

1. Ensure Ollama is running on the host machine listening on `0.0.0.0:11434` with `qwen2.5:3b` pulled.
2. Open Langflow at `http://localhost:7860` and open the flow canvas.
3. In the Agent node, set the model provider to **Ollama**.
4. Set the Base URL to `http://host.docker.internal:11434`.
5. Set the Model Name to `qwen2.5:3b`.
6. Alternatively, if using a cloud provider, configure API keys under **Settings** -> **Model Providers**.

## 3. Enable MCP on the CustomsGuard Flow

1. Inside your flow in Langflow (imported from [`langflow/CustomsGuard.json`](../../langflow/CustomsGuard.json)), click the **MCP Server** button in the header.
2. Switch to the **JSON** tab.
3. Click **Generate API Key** and copy the generated JSON block.
4. **Mandatory Hackathon Flag**:
   Ensure that the `args` array contains the `--with` and `mcp<2.0.0` flags.

## 4. Configure IBM Bob

1. Launch the **IBM Bob Desktop Application**.
2. Click the gear icon (**Settings**).
3. Navigate to the **MCP** tab.
4. Click the **+** button to add an MCP server.
5. Paste the JSON configuration block:

```json
{
  "mcpServers": {
    "lf-ibmsb": {
      "command": "uvx",
      "args": [
        "--with",
        "mcp<2.0.0",
        "mcp-proxy",
        "--transport",
        "streamablehttp",
        "--headers",
        "x-api-key",
        "YOUR_API_KEY",
        "http://localhost:7860/api/v1/mcp/project/PROJECT_ID/streamable"
      ]
    }
  }
}
```

6. Click **Save**.
7. Confirm that the `customsguard` tool appears in IBM Bob's active tools list.

## 5. Verify via Bob Shell (CLI)

You can also run non-interactive verification directly using the Bob CLI.
Ensure your `BOB_API_KEY` is exported in your environment, or provide it inline:

```bash
BOB_API_KEY="your_api_key_here" bob run --trust "Audit shipment SHP-2026-0042 using customsguard tool"
```
