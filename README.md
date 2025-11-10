# HOPX MCP Server

**Give your AI assistant superpowers with secure, isolated code execution.**

The official [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server for [HOPX](https://hopx.ai). Enable Claude and other AI assistants to execute code in blazing-fast (~0.1ms startup), isolated cloud containers.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.14+-blue.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-1.21+-green.svg)](https://modelcontextprotocol.io)

## Quick Installation

Install HOPX MCP Server with one click in your favorite IDE:

### Cursor

[![Install in Cursor](https://img.shields.io/badge/Install%20in-Cursor-000?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTIgMkw0IDIwaDhsMTAtMThoLThaTTEyIDJsMTAgMThoLTh6IiBmaWxsPSIjZmZmIi8+PC9zdmc+)](cursor://anysphere.cursor-deeplink/mcp/install?name=HOPX%20Sandbox&config=eyJjb21tYW5kIjogInV2eCIsICJhcmdzIjogWyItLWZyb20iLCAiZ2l0K2h0dHBzOi8vZ2l0aHViLmNvbS9ob3B4LWFpL21jcCIsICJob3B4LW1jcCJdLCAiZW52IjogeyJIT1BYX0FQSV9LRVkiOiAiIn19)

Click to install in Cursor. You'll need to add your HOPX API key after installation.

### VS Code

[![Install in VS Code](https://img.shields.io/badge/Install%20in-VS%20Code-007ACC?style=for-the-badge&logo=visualstudiocode&logoColor=white)](vscode:mcp/install?%7B%22name%22%3A%20%22HOPX%20Sandbox%22%2C%20%22command%22%3A%20%22uvx%22%2C%20%22args%22%3A%20%5B%22--from%22%2C%20%22git%2Bhttps%3A//github.com/hopx-ai/mcp%22%2C%20%22hopx-mcp%22%5D%7D)

Click to install in VS Code with MCP support.

### Visual Studio

[![Install in Visual Studio](https://img.shields.io/badge/Install%20in-Visual%20Studio-5C2D91?style=for-the-badge&logo=visualstudio&logoColor=white)](vsweb+mcp:/install?%7B%22name%22%3A%20%22HOPX%20Sandbox%22%2C%20%22type%22%3A%20%22stdio%22%2C%20%22command%22%3A%20%22uvx%22%2C%20%22args%22%3A%20%5B%22--from%22%2C%20%22git%2Bhttps%3A//github.com/hopx-ai/mcp%22%2C%20%22hopx-mcp%22%5D%7D)

Click to install in Visual Studio with MCP support.

### Claude Desktop

[![Install in Claude Desktop](https://img.shields.io/badge/Install%20in-Claude%20Desktop-111?style=for-the-badge&logo=anthropic&logoColor=white)](https://modelcontextprotocol.io/docs/tools/bundles)

For Claude Desktop, download the `.mcpb` bundle (see [Publishing .mcpb Bundle](#publishing-mcpb-bundle) section) or configure manually below.

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

## Installation Methods

### Option 1: Direct from GitHub (Recommended)

Use `uvx` to run directly from the GitHub repository:

```bash
uvx --from git+https://github.com/hopx-ai/mcp hopx-mcp
```

### Option 2: After Publishing to PyPI

Once published to PyPI, you can install with:

```bash
uvx hopx-mcp
```

### Option 3: Local Development

Clone and install for local development:

```bash
git clone https://github.com/hopx-ai/mcp.git
cd mcp
uv sync
export HOPX_API_KEY="your-api-key-here"
```

---

## Configuration

### Get Your API Key

Sign up at [hopx.dev](https://hopx.dev) to get your API key.

### Configure Your IDE

Choose your IDE below for detailed configuration instructions:

<details>
<summary><b>Cursor</b></summary>

Add to `.cursor/mcp.json` in your project or workspace:

```json
{
  "mcpServers": {
    "hopx-sandbox": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/hopx-ai/mcp",
        "hopx-mcp"
      ],
      "env": {
        "HOPX_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

After publishing to PyPI, simplify to:

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

**Installation Button Config:**
- The one-click install button uses this base64-encoded config:
  ```json
  {"command":"uvx","args":["--from","git+https://github.com/hopx-ai/mcp","hopx-mcp"],"env":{"HOPX_API_KEY":""}}
  ```
- Base64: `eyJjb21tYW5kIjogInV2eCIsICJhcmdzIjogWyItLWZyb20iLCAiZ2l0K2h0dHBzOi8vZ2l0aHViLmNvbS9ob3B4LWFpL21jcCIsICJob3B4LW1jcCJdLCAiZW52IjogeyJIT1BYX0FQSV9LRVkiOiAiIn19`

</details>

<details>
<summary><b>VS Code</b></summary>

Add to `.vscode/mcp.json` in your workspace:

```json
{
  "mcpServers": {
    "hopx-sandbox": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/hopx-ai/mcp",
        "hopx-mcp"
      ],
      "env": {
        "HOPX_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

After publishing to PyPI:

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

**Installation Button Config:**
- The one-click install button uses this URL-encoded config:
  ```json
  {"name":"HOPX Sandbox","command":"uvx","args":["--from","git+https://github.com/hopx-ai/mcp","hopx-mcp"]}
  ```
- URL Encoded: `%7B%22name%22%3A%20%22HOPX%20Sandbox%22%2C%20%22command%22%3A%20%22uvx%22%2C%20%22args%22%3A%20%5B%22--from%22%2C%20%22git%2Bhttps%3A//github.com/hopx-ai/mcp%22%2C%20%22hopx-mcp%22%5D%7D`

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
      "args": [
        "--from",
        "git+https://github.com/hopx-ai/mcp",
        "hopx-mcp"
      ],
      "env": {
        "HOPX_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

After publishing to PyPI:

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

**Installation Button Config:**
- The one-click install button uses this URL-encoded config with type:
  ```json
  {"name":"HOPX Sandbox","type":"stdio","command":"uvx","args":["--from","git+https://github.com/hopx-ai/mcp","hopx-mcp"]}
  ```
- URL Encoded: `%7B%22name%22%3A%20%22HOPX%20Sandbox%22%2C%20%22type%22%3A%20%22stdio%22%2C%20%22command%22%3A%20%22uvx%22%2C%20%22args%22%3A%20%5B%22--from%22%2C%20%22git%2Bhttps%3A//github.com/hopx-ai/mcp%22%2C%20%22hopx-mcp%22%5D%7D`

</details>

<details>
<summary><b>Claude Desktop</b></summary>

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS or `%APPDATA%\Claude\claude_desktop_config.json` on Windows:

```json
{
  "mcpServers": {
    "hopx-sandbox": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/hopx-ai/mcp",
        "hopx-mcp"
      ],
      "env": {
        "HOPX_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

After publishing to PyPI:

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
<summary><b>Cline (VS Code Extension)</b></summary>

Add to your VS Code settings or Cline configuration:

```json
{
  "cline.mcpServers": {
    "hopx-sandbox": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/hopx-ai/mcp",
        "hopx-mcp"
      ],
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
      "args": [
        "--from",
        "git+https://github.com/hopx-ai/mcp",
        "hopx-mcp"
      ],
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
      "args": [
        "--from",
        "git+https://github.com/hopx-ai/mcp",
        "hopx-mcp"
      ],
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
        "args": [
          "--from",
          "git+https://github.com/hopx-ai/mcp",
          "hopx-mcp"
        ],
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
      "args": [
        "--from",
        "git+https://github.com/hopx-ai/mcp",
        "hopx-mcp"
      ],
      "env": {
        "HOPX_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

</details>

---

## Publishing .mcpb Bundle

The `.mcpb` (MCP Bundle) format allows one-click installation in Claude Desktop and other MCP clients. To create and publish your bundle:

### Creating the Bundle

1. **Create the bundle structure:**
   ```bash
   mkdir hopx-mcp-bundle
   cd hopx-mcp-bundle
   ```

2. **Create `manifest.json`:**
   ```json
   {
     "name": "HOPX Sandbox",
     "version": "0.1.0",
     "description": "Execute code in isolated cloud containers",
     "author": "HOPX",
     "homepage": "https://hopx.dev",
     "repository": "https://github.com/hopx-ai/mcp",
     "license": "MIT",
     "config": {
       "command": "uvx",
       "args": ["--from", "git+https://github.com/hopx-ai/mcp", "hopx-mcp"],
       "env": {
         "HOPX_API_KEY": ""
       }
     },
     "requiredEnv": ["HOPX_API_KEY"]
   }
   ```

3. **Create the bundle:**
   ```bash
   zip -r hopx-mcp.mcpb manifest.json
   ```

### Publishing the Bundle

1. **Upload to GitHub Releases:**
   - Create a new release on your GitHub repository
   - Attach the `hopx-mcp.mcpb` file
   - Users can download and double-click to install

2. **Direct download link:**
   ```markdown
   [Download HOPX MCP Bundle](https://github.com/hopx-ai/mcp/releases/latest/download/hopx-mcp.mcpb)
   ```

3. **Installation instructions for users:**
   - Download the `.mcpb` file
   - Double-click the file (on supported platforms)
   - Or: Open Claude Desktop → Settings → MCP Servers → Install from Bundle
   - Enter your HOPX API key when prompted

### After Publishing to PyPI

Update the bundle to use the simpler PyPI installation:

```json
{
  "config": {
    "command": "uvx",
    "args": ["hopx-mcp"],
    "env": {
      "HOPX_API_KEY": ""
    }
  }
}
```

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
- Sandbox creation in ~0.1ms
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

Get your API key at [hopx.dev](https://hopx.dev)

### Optional

```bash
HOPX_BASE_URL=https://api.hopx.dev  # default
HOPX_BEARER_TOKEN=alternative-auth  # if using bearer token
```

---

## Testing

We've included a comprehensive test suite:

```bash
export HOPX_API_KEY="your-api-key"
cd bns-mcp
uv run python test_execute_isolated.py
```

**Tests include:**
- ✅ Python data analysis (pandas + numpy)
- ✅ JavaScript array processing
- ✅ Bash system commands
- ✅ Environment variable injection

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

### Installation Button Not Working

**Cause:** IDE doesn't support deep link protocol or MCP not installed.

**Solution:**
1. Ensure your IDE supports MCP (see [modelcontextprotocol.io](https://modelcontextprotocol.io))
2. Install MCP support if needed
3. Use manual configuration instead (see Configuration section)

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

- **Documentation:** [docs.hopx.dev](https://docs.hopx.dev)
- **API Reference:** [api.hopx.dev](https://api.hopx.dev)
- **Issues:** [GitHub Issues](https://github.com/hopx-ai/mcp/issues)
- **Email:** support@hopx.dev
- **Discord:** [Join our community](https://discord.gg/hopx)

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/hopx-ai/mcp.git
cd mcp

# Install dependencies
uv sync

# Set up environment
export HOPX_API_KEY="your-api-key"

# Run tests
uv run python test_execute_isolated.py

# Run the server locally
uv run python hopx_mcp/server.py
```

---

## License

This MCP server is provided under the MIT License. See [LICENSE](LICENSE) for details.

See the [HOPX Terms of Service](https://hopx.dev/terms) for API usage terms.

---

## Built With

- [FastMCP](https://github.com/jlowin/fastmcp) - Python framework for MCP servers
- [Model Context Protocol](https://modelcontextprotocol.io) - Protocol for AI-tool integration
- [HOPX Sandbox API](https://hopx.dev) - Cloud container platform
- [uvx](https://docs.astral.sh/uv/) - Fast Python package installer and runner

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

---

## Acknowledgments

Special thanks to:
- The Anthropic team for creating the Model Context Protocol
- The FastMCP community for their excellent framework
- All our contributors and early adopters

---

Made with ❤️ by [HOPX](https://hopx.dev)

[Website](https://hopx.dev) | [Documentation](https://docs.hopx.dev) | [API Reference](https://api.hopx.dev) | [GitHub](https://github.com/hopx-ai/mcp)
