# HOPX MCP Server

Model Context Protocol (MCP) server for [HOPX](https://hopx.ai). Enables AI assistants to execute code in isolated cloud containers.

**MCP Name:** `io.github.hopx-ai/hopx-mcp`

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.14+-blue.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-1.21+-green.svg)](https://modelcontextprotocol.io)

## Installation

```bash
uvx hopx-mcp
```

Get your API key at [hopx.ai](https://hopx.ai).

---

## Capabilities

- Execute Python, JavaScript, Bash, and Go in isolated containers
- Data analysis with pandas, numpy, matplotlib (pre-installed)
- File operations and system commands
- Background processes and long-running tasks

Containers auto-destroy after use.

---

## Configuration

### Get API Key

Sign up at [hopx.ai](https://hopx.ai).

### Configure IDE

Add MCP server configuration to your IDE:

<details>
<summary><b>Claude Desktop</b></summary>

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "hopx-sandbox": {
      "command": "uvx",
      "args": ["hopx-mcp"],
      "env": {
        "HOPX_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Restart Claude Desktop after configuration.

</details>

<details>
<summary><b>Cursor</b></summary>

Add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "hopx-sandbox": {
      "command": "uvx",
      "args": ["hopx-mcp"],
      "env": {
        "HOPX_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

</details>

<details>
<summary><b>VS Code</b></summary>

Add to `.vscode/mcp.json`:

```json
{
  "mcpServers": {
    "hopx-sandbox": {
      "command": "uvx",
      "args": ["hopx-mcp"],
      "env": {
        "HOPX_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

</details>

<details>
<summary><b>Other IDEs</b></summary>

Configuration format varies by IDE. Add these parameters:
- Command: `uvx`
- Args: `["hopx-mcp"]`
- Environment: `HOPX_API_KEY=your-api-key-here`

</details>

---

## Usage

### Quick Execution

```python
execute_code_isolated(
    code='print("Hello, World!")',
    language='python',
    timeout=30
)
```

**Returns:**
```python
{
    'stdout': 'Hello, World!\n',
    'exit_code': 0,
    'execution_time': 0.123,
    'sandbox_id': '1762778786mxaco6r2'
}
```

### Persistent Sandbox

For multiple operations in the same environment:

```python
# Create sandbox
sandbox = create_sandbox(
    template_id='code-interpreter',
    timeout_seconds=3600
)

sandbox_id = sandbox['id']

# Run operations
execute_code(sandbox_id, 'import pandas as pd')
execute_code(sandbox_id, 'df = pd.read_csv("data.csv")')
file_write(sandbox_id, '/workspace/output.txt', 'results')
content = file_read(sandbox_id, '/workspace/output.txt')

# Cleanup
delete_sandbox(sandbox_id)
```

---

## Available Tools

**Sandbox Management:**
- `create_sandbox()` - Create sandbox
- `list_sandboxes()` - List sandboxes
- `delete_sandbox()` - Terminate sandbox

**Code Execution:**
- `execute_code_isolated()` - One-shot execution (recommended)
- `execute_code()` - Execute in existing sandbox
- `execute_code_background()` - Long-running tasks
- `execute_code_async()` - Webhook callbacks for 30+ min tasks

**File Operations:**
- `file_read()`, `file_write()`, `file_list()`
- `file_exists()`, `file_remove()`, `file_mkdir()`

**Commands:**
- `run_command()` - Execute shell commands
- `run_command_background()` - Background processes

**Environment:**
- `env_get()`, `env_set()`, `env_clear()`

---

## Supported Languages

- **Python 3.11+** - pandas, numpy, matplotlib, scipy, scikit-learn, requests
- **JavaScript/Node.js 20** - Standard libraries
- **Bash** - Unix utilities, git, curl, wget
- **Go** - Compilation support

---

## Features

- Sandbox creation: ~200ms
- Container startup: ~0.1s
- Auto-cleanup: 600s (configurable)
- Internet access: Enabled by default
- Isolation: Complete per execution
- Authentication: JWT-based

---

## Environment Variables

**Required:**
```bash
HOPX_API_KEY=your-api-key
```

**Optional:**
```bash
HOPX_BASE_URL=https://api.hopx.dev  # default
```

---

## Troubleshooting

### "401 Unauthorized"

API key not set or invalid.

**Solution:**
```bash
echo $HOPX_API_KEY  # Verify key is set
```

### "Template not found"

Invalid template name.

**Solution:**
```python
templates = list_templates(limit=20)  # Browse available templates
```

### Slow First Execution

Container initializes in ~3 seconds after creation.

**Cause:** VM authentication setup
**Solution:** Subsequent operations are immediate

---

## Limitations

- Synchronous execution: Max 300 seconds
- Sandbox lifetime: Default 10 minutes (configurable)
- Template-specific language support

---

## Security

**Protected:**
- Local system isolated from container execution
- Containers isolated from each other
- Auto-cleanup prevents resource leaks
- JWT authentication per sandbox

**Considerations:**
- Containers have internet access by default
- Code executed in HOPX cloud
- Follow your security policies for sensitive data

---

## Support

- Documentation: [docs.hopx.ai](https://docs.hopx.ai)
- Issues: [GitHub](https://github.com/hopx-ai/mcp/issues)
- Email: support@hopx.ai

---

## License

MIT License. See [LICENSE](LICENSE) for details.

HOPX Terms of Service: [hopx.ai/terms](https://hopx.ai/terms)

---

## Technical Details

Built with:
- [hopx-ai SDK](https://github.com/hopx-ai/hopx-python-sdk) v0.2.7
- [FastMCP](https://github.com/jlowin/fastmcp) framework
- [Model Context Protocol](https://modelcontextprotocol.io)

---

[Website](https://hopx.ai) | [Documentation](https://docs.hopx.ai) | [GitHub](https://github.com/hopx-ai/mcp)
