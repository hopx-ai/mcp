# HOPX MCP Server

**Give your AI assistant superpowers with secure, isolated code execution.**

The official [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server for [HOPX](https://hopx.ai). Enable Claude and other AI assistants to execute code in blazing-fast (0.1s startup), isolated cloud containers.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.14+-blue.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-1.21+-green.svg)](https://modelcontextprotocol.io)

## Installation

```bash
uvx hopx-mcp
```

Get your API key at [hopx.ai](https://hopx.ai) and configure your IDE below.

---

## What This Enables

With this MCP server, your AI assistant can:

- ✅ **Execute Python, JavaScript, Bash, and Go** in isolated containers
- ✅ **Analyze data** with pandas, numpy, matplotlib (pre-installed)
- ✅ **Test code snippets** before you use them in production
- ✅ **Process data** securely without touching your local system
- ✅ **Run system commands** safely in isolated environments
- ✅ **Install packages** and test integrations on-the-fly

All executions happen in **secure, ephemeral cloud containers** that auto-destroy after use. Your local system stays clean and protected.

---

## Configuration

### Get Your API Key

Sign up at [hopx.ai](https://hopx.ai) to get your free API key.

### Configure Your IDE

After installing with `uvx hopx-mcp`, configure your IDE by adding the MCP server configuration:

Choose your IDE below for detailed configuration instructions:

<details>
<summary><b>Cursor</b></summary>

Add to `.cursor/mcp.json` in your project or workspace:

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

Replace `your-api-key-here` with your actual API key from [hopx.ai](https://hopx.ai).

</details>

<details>
<summary><b>VS Code</b></summary>

Add to `.vscode/mcp.json` in your workspace:

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

Replace `your-api-key-here` with your actual API key from [hopx.ai](https://hopx.ai).

</details>

<details>
<summary><b>Visual Studio</b></summary>

Add to `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "hopx-sandbox": {
      "type": "stdio",
      "command": "uvx",
      "args": ["hopx-mcp"],
      "env": {
        "HOPX_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Replace `your-api-key-here` with your actual API key from [hopx.ai](https://hopx.ai).

</details>

<details>
<summary><b>Claude Desktop</b></summary>

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS or `%APPDATA%\Claude\claude_desktop_config.json` on Windows:

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

Replace `your-api-key-here` with your actual API key from [hopx.ai](https://hopx.ai), then restart Claude Desktop.

</details>

<details>
<summary><b>Cline (VS Code Extension)</b></summary>

Add to your VS Code settings or Cline configuration:

```json
{
  "cline.mcpServers": {
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
<summary><b>Continue.dev</b></summary>

Add to `~/.continue/config.json`:

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
<summary><b>Windsurf</b></summary>

Add to `.windsurf/mcp.json` in your project:

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
<summary><b>Zed</b></summary>

Add to your Zed settings or MCP configuration:

```json
{
  "mcp": {
    "servers": {
      "hopx-sandbox": {
        "command": "uvx",
        "args": ["hopx-mcp"],
        "env": {
          "HOPX_API_KEY": "your-api-key-here"
        }
      }
    }
  }
}
```

</details>

<details>
<summary><b>Codex</b></summary>

Add to your Codex MCP configuration file:

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

---

## Usage Examples

Your AI assistant can now execute code directly. Here's what it looks like:

### Python Data Analysis

**You:** "Analyze this sales data: [100, 150, 200, 180, 220]"

**Claude:** *Uses `execute_code_isolated()` to run:*

```python
import pandas as pd
import numpy as np

sales = [100, 150, 200, 180, 220]
df = pd.DataFrame({'sales': sales})

print(f"Mean: ${df['sales'].mean():.2f}")
print(f"Median: ${df['sales'].median():.2f}")
print(f"Growth: {((sales[-1] - sales[0]) / sales[0] * 100):.1f}%")
```

**Output:**
```
Mean: $170.00
Median: $180.00
Growth: 120.0%
```

### JavaScript Computation

**You:** "Calculate fibonacci numbers up to 100"

**Claude:** *Executes:*

```javascript
function fibonacci(max) {
  const fib = [0, 1];
  while (true) {
    const next = fib[fib.length - 1] + fib[fib.length - 2];
    if (next > max) break;
    fib.push(next);
  }
  return fib;
}

console.log(fibonacci(100));
```

**Output:**
```
[0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
```

### Bash System Info

**You:** "What's the system architecture and available disk space?"

**Claude:** *Runs:*

```bash
echo "System: $(uname -s)"
echo "Architecture: $(uname -m)"
echo "Disk:"
df -h / | tail -1
```

**Output:**
```
System: Linux
Architecture: x86_64
Disk:
/dev/root        20G  1.9G   17G  10% /
```

---

## Features

### 🚀 Blazing Fast
- Sandbox creation in ~0.1s
- Pre-warmed containers ready to execute
- Global edge network for low latency

### 🔒 Secure by Default
- Complete isolation per execution
- No shared state between runs
- JWT-based authentication
- Auto-cleanup after timeout

### 🌐 Multi-Language Support
- **Python 3.11+** with pandas, numpy, matplotlib, scikit-learn
- **JavaScript/Node.js 20** with standard libraries
- **Bash** with common Unix utilities
- **Go** with compilation support

### ⚡ Pre-installed Packages

**Python:**
- Data Science: pandas, numpy, matplotlib, scipy, scikit-learn
- Web: requests, httpx, beautifulsoup4
- Jupyter: ipykernel, jupyter-client

**JavaScript:**
- Node.js 20.x runtime
- iJavaScript kernel for notebooks

**System:**
- git, curl, wget, vim, nano
- Build tools: gcc, g++, make
- Python package managers: pip, uv

### 🎯 Smart Defaults
- Internet access enabled
- 600-second auto-destroy (configurable)
- Request-specific environment variables
- Automatic error handling

---

## API Reference

### Primary Tool: `execute_code_isolated()`

The recommended way to execute code. Creates a sandbox, runs your code, returns output, and auto-destroys.

```python
result = execute_code_isolated(
    code='print("Hello, World!")',
    language='python',          # 'python', 'javascript', 'bash', 'go'
    timeout=30,                 # max 300 seconds
    env={'API_KEY': 'secret'},  # optional env vars
    template_name='code-interpreter',  # template to use
    region='us-east'            # optional: 'us-east', 'eu-west'
)
```

**Returns:**
```python
{
    'stdout': 'Hello, World!\n',
    'stderr': '',
    'exit_code': 0,
    'execution_time': 0.123,
    'sandbox_id': '1762778786mxaco6r2',
    '_note': 'Sandbox will auto-destroy after 10 minutes'
}
```

### Advanced: Persistent Sandboxes

For multi-step workflows where you need to maintain state:

```python
# 1. Create a long-lived sandbox
sandbox = create_sandbox(
    template_id='20',  # or get ID from get_template('code-interpreter')
    timeout_seconds=3600,
    internet_access=True
)

# 2. Extract connection details
vm_url = sandbox['direct_url']
auth_token = sandbox['auth_token']

# 3. Run multiple commands
execute_code(vm_url, 'import pandas as pd', auth_token=auth_token)
execute_code(vm_url, 'df = pd.read_csv("data.csv")', auth_token=auth_token)
result = execute_code(vm_url, 'print(df.head())', auth_token=auth_token)

# 4. File operations
file_write(vm_url, '/workspace/output.txt', 'results', auth_token=auth_token)
content = file_read(vm_url, '/workspace/output.txt', auth_token=auth_token)

# 5. Clean up when done
delete_sandbox(sandbox['id'])
```

### All Available Tools

The MCP server exposes 30+ tools for complete control:

**Sandbox Management:**
- `create_sandbox()` - Create a new sandbox
- `list_sandboxes()` - List all your sandboxes
- `get_sandbox()` - Get sandbox details
- `delete_sandbox()` - Terminate a sandbox
- `update_sandbox_timeout()` - Extend runtime

**Code Execution:**
- `execute_code_isolated()` - ⭐ Primary method (one-shot)
- `execute_code()` - Execute in existing sandbox
- `execute_code_rich()` - Capture matplotlib plots, DataFrames
- `execute_code_background()` - Long-running tasks (5-30 min)
- `execute_code_async()` - Very long tasks with webhooks (30+ min)

**File Operations:**
- `file_read()`, `file_write()`, `file_list()`
- `file_exists()`, `file_remove()`, `file_mkdir()`

**Process Management:**
- `list_processes()` - All system processes
- `execute_list_processes()` - Background executions
- `execute_kill_process()` - Terminate process

**Environment & System:**
- `env_set()`, `env_get()`, `env_clear()` - Manage env vars
- `get_system_metrics()` - CPU, memory, disk usage
- `run_command()` - Execute shell commands

**Templates:**
- `list_templates()` - Browse available templates
- `get_template()` - Get template details

---

## Architecture

```
┌─────────────┐
│   Claude    │  Your AI Assistant
│  (MCP Host) │
└──────┬──────┘
       │ MCP Protocol
       │
┌──────▼──────┐
│  HOPX MCP   │  This Server
│   Server    │  (FastMCP)
└──────┬──────┘
       │ HTTPS/REST
       │
┌──────▼──────┐
│ HOPX Cloud  │  Isolated Containers
│  Sandboxes  │  • Python, JS, Bash, Go
└─────────────┘  • Auto-cleanup
                 • Global Edge Network
```

---

## Environment Variables

### Required

```bash
HOPX_API_KEY=your-api-key
```

Get your API key at [hopx.ai](https://hopx.ai)

### Optional

```bash
HOPX_BASE_URL=https://api.hopx.dev  # default
HOPX_BEARER_TOKEN=alternative-auth  # if using bearer token
```

---

## Troubleshooting

### "401 Unauthorized" Error

**Cause:** API key not set or invalid.

**Solution:**
```bash
# Verify your API key is set
echo $HOPX_API_KEY

# Or check your IDE config file
# See Configuration section for your IDE
```

### "Template not found" Error

**Cause:** Invalid template name.

**Solution:** Use the default `code-interpreter` template or list available templates:
```python
templates = list_templates(category='development', language='python')
```

### Slow First Execution

**Cause:** Cold start - container is being created.

**Why it happens:** The first execution needs to:
1. Create the container (~0.1ms)
2. Wait for VM auth init (~3 seconds)
3. Execute your code

**Solution:** Subsequent executions in the same sandbox are instant. For frequently-used environments, consider creating a persistent sandbox.

### Execution Timeout

**Cause:** Code took longer than the timeout limit.

**Solution:** Increase timeout or use background execution:
```python
# Increase timeout
execute_code_isolated(code='...', timeout=300)  # max 300s

# Or use background for long tasks
proc = execute_code_background(vm_url, code='...', timeout=1800)
```

---

## Limitations

- **VM Initialization:** ~3 second wait after sandbox creation for auth
- **Execution Timeout:** Maximum 300 seconds per synchronous execution
- **Sandbox Lifetime:** Default 10 minutes (configurable up to hours)
- **Template-Specific:** Some templates optimized for specific languages

---

## Security

### What's Protected

✅ **Your local system** - All code runs in isolated cloud containers
✅ **Container isolation** - Each execution in a separate container
✅ **Network isolation** - Containers can't access each other
✅ **Automatic cleanup** - Resources destroyed after timeout
✅ **JWT authentication** - Secure token-based auth per sandbox

### What You Should Know

⚠️ **Internet access** - Containers can access the internet by default
⚠️ **Code visibility** - Your code is sent to HOPX cloud for execution
⚠️ **Data handling** - Follow your security policies for sensitive data

For sensitive workloads, contact us about private cloud deployments.

---

## Support

- **Documentation:** [docs.hopx.ai](https://docs.hopx.ai)
- **API Reference:** [api.hopx.dev](https://api.hopx.dev)
- **Issues:** [GitHub Issues](https://github.com/hopx-ai/mcp/issues)
- **Email:** support@hopx.ai
- **Discord:** [Join our community](https://discord.gg/hopx)

---

## License

This MCP server is provided under the MIT License. See [LICENSE](LICENSE) for details.

See the [HOPX Terms of Service](https://hopx.ai/terms) for API usage terms.

---

## Built With

- [FastMCP](https://github.com/jlowin/fastmcp) - Python framework for MCP servers
- [Model Context Protocol](https://modelcontextprotocol.io) - Protocol for AI-tool integration
- [HOPX Sandbox API](https://hopx.ai) - Cloud container platform
- [uvx](https://docs.astral.sh/uv/) - Fast Python package installer and runner

---

Made with ❤️ by [HOPX](https://hopx.ai)

[Website](https://hopx.ai) | [Documentation](https://docs.hopx.ai) | [API Reference](https://api.hopx.dev) | [GitHub](https://github.com/hopx-ai/mcp)
