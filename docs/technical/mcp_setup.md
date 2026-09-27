# IBM Bob & Langflow MCP Integration Guide

This guide details how to expose CustomsGuard flows as MCP tools in Langflow and connect them directly to IBM Bob.

## 1. Access Langflow Web UI

1. Open your web browser and navigate to `http://localhost:7860`.
2. Login credentials (configured in `.env`):
   - **Username**: `admin`
   - **Password**: `admin123`
3. Verify that the dashboard loads successfully.

## 2. Configure Model Providers in Langflow

1. Click the rocket icon / settings gear in the top-right corner of Langflow.
2. Navigate to **Settings** -> **Model Providers**.
3. Select your provider (e.g. OpenRouter or OpenAI).
4. Enter your API key and configure the provider settings.
5. In the flow canvas, the Agent node will now use the configured model.

## 3. Enable MCP on the CustomsGuard Flow

1. Inside your flow in Langflow, click the **MCP Server** button in the header.
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
    "lf-starter_project": {
      "command": "/home/rafif/.local/bin/uvx",
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
