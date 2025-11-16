import os
import time
from typing import Any, Dict, Optional, Literal

from hopx_ai import (
    Sandbox,
    CodeExecutionError,
    FileNotFoundError as HopxFileNotFoundError,
    CommandExecutionError,
    NotFoundError as SandboxNotFoundError,
)
from mcp.server.fastmcp import FastMCP

# Desktop automation feature flag
ENABLE_DESKTOP_AUTOMATION = os.getenv("HOPX_ENABLE_DESKTOP", "false").lower() == "true"

mcp = FastMCP(
    "hopx",
    instructions="""HOPX Sandbox API provides fast isolated code execution in ephemeral cloud containers.

PRIMARY USE: execute_code() with mode parameter - Unified code execution API

EXECUTION MODES:
• isolated - One-shot execution (recommended for most tasks) - Creates sandbox, executes, returns output, auto-destroys
• persistent - Execute in existing sandbox
• rich - Execute with rich output capture (matplotlib plots, DataFrames)
• background - Non-blocking execution via SDK

WHEN TO USE WHAT:
• Quick execution (data analysis, testing, scripts): execute_code(code="...", mode="isolated")
• Multi-step workflows (install deps → run code → check files): create_sandbox() then execute_code(sandbox_id=id, code="...")
• Long tasks: execute_code(sandbox_id=id, code="...", mode="background")

IMPORTANT:
- Isolated mode creates NEW sandbox - don't pass sandbox_id
- Other modes require sandbox_id from create_sandbox()
- list_templates() returns many templates - use limit parameter to control response size
- Sandboxes auto-destroy based on timeout_seconds parameter
- Execute tools support request-specific env vars (preferred over global env_set)

TYPICAL WORKFLOWS:
1. One-shot: execute_code(code="...", mode="isolated", language="python")
2. Persistent: create_sandbox(template_id="<id>") → extract id → execute_code(sandbox_id=id, code="...")
3. Long-running: create_sandbox() → execute_code(sandbox_id=id, mode="background")

See individual tool descriptions for detailed parameters and examples.""",
)


# ---------- System ----------
@mcp.tool()
def health() -> dict:
    """GET /health — public health check.

    Returns:
        Health status of the HOPX API
    """
    try:
        result = Sandbox.health_check()
        # health_check returns a dict or None
        if result:
            return result
        return {"status": "ok"}
    except Exception as e:
        return {
            "error": "Health check failed",
            "exception": str(e),
        }


# ---------- Sandboxes ----------
@mcp.tool()
def list_sandboxes(
    limit: int = 100,
    status: Optional[str] = None,  # running|stopped|paused|creating
    region: Optional[str] = None,
) -> dict:
    """
    GET /v1/sandboxes — list all sandboxes.

    Returns a list of sandboxes with their current status, configuration, and metadata.
    Use this to find existing sandboxes before creating new ones or to check sandbox states.

    Args:
        limit: Maximum number of sandboxes to return (default: 100)
        status: Filter by status: 'running', 'stopped', 'paused', or 'creating'
        region: Filter by region (e.g., 'us-east', 'eu-west')

    Returns:
        List of sandbox objects with id, status, template info, and resource details
    """
    try:
        sandboxes = Sandbox.list(status=status, region=region, limit=limit)
        # Sandbox.list() returns List[Sandbox], need to get_info() for full details
        return {
            "data": [s.get_info().model_dump() for s in sandboxes],
            "count": len(sandboxes),
        }
    except Exception as e:
        import traceback

        return {
            "error": "Failed to list sandboxes",
            "exception": str(e),
            "exception_type": type(e).__name__,
            "traceback": traceback.format_exc(),
        }


@mcp.tool()
def create_sandbox(
    template_id: str,
    region: Optional[str] = None,
    timeout_seconds: Optional[int] = None,
    internet_access: Optional[bool] = None,
    env_vars: Optional[Dict[str, str]] = None,
) -> dict:
    """
    POST /v1/sandboxes — create a new sandbox.

    WORKFLOW: First use list_templates() to find available templates, then create a sandbox
    with the template's id or name.

    Args:
        template_id: Template ID or name to use. Can be a template name (e.g., "code-interpreter")
                     or template ID (e.g., "628"). Get from list_templates() or get_template()
        region: Deployment region, e.g., 'us-east', 'eu-west' (optional)
        timeout_seconds: Auto-shutdown timeout in seconds (optional, e.g., 3600 for 1 hour)
        internet_access: Enable internet access (optional, default is typically true)
        env_vars: Initial environment variables for the sandbox (optional)

    Returns:
        Created sandbox object with id, status, connection details, and configuration.
        The 'id' field is the sandbox_id needed for all other operations.

    Example flow:
        1. templates = list_templates(limit=20)
        2. template = templates["data"][0]  # Pick a template
        3. sandbox = create_sandbox(template_id=template["name"], region="eu-west", timeout_seconds=3600)
        4. sandbox_id = sandbox["id"]  # Use this for execute_code(), file_read(), etc.

    Note: The SDK does not support custom vcpu, memory_mb, or disk_gb parameters.
          Templates define these resources.
    """
    try:
        # SDK's create() accepts either 'template' (name) or 'template_id' (ID)
        # Try to use template parameter if template_id looks like a name
        # Otherwise use template_id parameter
        if template_id.isdigit():
            # Numeric ID - use template_id parameter
            sandbox = Sandbox.create(
                template_id=template_id,
                region=region,
                timeout_seconds=timeout_seconds,
                internet_access=internet_access,
                env_vars=env_vars,
            )
        else:
            # Template name - use template parameter
            sandbox = Sandbox.create(
                template=template_id,
                region=region,
                timeout_seconds=timeout_seconds,
                internet_access=internet_access,
                env_vars=env_vars,
            )

        # Get sandbox info to return
        info = sandbox.get_info()
        return {
            "id": sandbox.sandbox_id,
            "status": info.status,
            "template_id": info.template_id,
            "template_name": info.template_name,
            "region": info.region,
            "created_at": info.created_at,
            "timeout_seconds": info.timeout_seconds,
        }
    except Exception as e:
        return {
            "error": "Failed to create sandbox",
            "exception": str(e),
            "details": {
                "template_id": template_id,
                "error_type": type(e).__name__
            }
        }


@mcp.tool()
def get_sandbox(id: str) -> dict:
    """
    GET /v1/sandboxes/{id} — get detailed sandbox information.

    Retrieve current status, resource usage, connection info, and metadata for a specific sandbox.
    Use this after creating a sandbox to get connection details or to check current state.

    Args:
        id: Sandbox ID (returned from create_sandbox or list_sandboxes)

    Returns:
        Sandbox object with status, connection details, resource info, and timestamps
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=id)
        info = sandbox.get_info()
        result = info.model_dump()
        # Rename sandbox_id to id for API compatibility
        result["id"] = result.pop("sandbox_id")
        return result
    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "id": id,
        }
    except Exception as e:
        return {
            "error": "Failed to get sandbox",
            "exception": str(e),
        }


@mcp.tool()
def delete_sandbox(id: str) -> dict:
    """
    DELETE /v1/sandboxes/{id} — permanently delete a sandbox.

    Use this to clean up sandboxes when they're no longer needed. This action is irreversible.

    Args:
        id: Sandbox ID to delete

    Returns:
        Confirmation of deletion
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=id)
        sandbox.kill()
        return {"status": "deleted", "id": id}
    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "sandbox_id": id,
        }
    except Exception as e:
        return {
            "error": "Failed to delete sandbox",
            "exception": str(e),
        }


@mcp.tool()
def update_sandbox_timeout(id: str, timeout_seconds: int) -> dict:
    """
    PUT /v1/sandboxes/{id}/timeout — extend or modify sandbox timeout.

    Use this to extend the runtime of a sandbox before it auto-shuts down, or to set
    a new timeout value. Useful when you need more time to complete work in a sandbox.

    Args:
        id: Sandbox ID
        timeout_seconds: New timeout in seconds (e.g., 3600 for 1 hour, 7200 for 2 hours)

    Returns:
        Updated sandbox object with new timeout

    Example:
        # Extend timeout by 1 hour
        update_sandbox_timeout(id="abc123", timeout_seconds=3600)
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=id)
        sandbox.set_timeout(timeout_seconds)
        return {"id": id, "timeout_seconds": timeout_seconds, "status": "updated"}
    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "sandbox_id": id,
        }
    except Exception as e:
        return {
            "error": "Failed to update timeout",
            "exception": str(e),
        }


@mcp.tool()
def resume_sandbox(id: str) -> dict:
    """
    POST /v1/sandboxes/{id}/resume — resume a paused sandbox.

    Resumes a sandbox that was previously paused, restoring it to running state.

    Args:
        id: Sandbox ID to resume

    Returns:
        Updated sandbox object with new status
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=id)
        sandbox.resume()
        info = sandbox.get_info()
        return info.model_dump()
    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "sandbox_id": id,
        }
    except Exception as e:
        return {
            "error": "Failed to resume sandbox",
            "exception": str(e),
        }


# ---------- Templates ----------
@mcp.tool()
def list_templates(
    limit: int = 10,
    fields: Optional[str] = "id,name,description,category,language",
) -> dict:
    """
    GET /v1/templates — list available sandbox templates.

    Templates are pre-configured environments (e.g., Python, Node.js, Ubuntu) that define
    the base system and default resources for sandboxes. Always list templates first to
    discover available options before creating a sandbox.

    Args:
        limit: Maximum number of templates to return (default: 10, prevents context overflow)
        fields: Comma-separated list of fields to return (default: "id,name,description,category,language")
                Use "all" to get all fields. Available: id, name, display_name, description, category,
                language, default_resources, is_active, status, build_id, created_at, updated_at

    Returns:
        List of template objects. By default, only essential fields are returned to prevent
        context overflow. Specify fields="all" for complete template data.

    WORKFLOW: Use this before create_sandbox() to discover template IDs and their defaults.
    Example:
        1. templates = list_templates(limit=20)
        2. Pick a template from the list
        3. sandbox = create_sandbox(template_id=template["id"])

        # For full details on specific template:
        templates = list_templates(limit=5, fields="all")

    NOTE: The API does not support filtering by category or language. You will need to
    filter the results client-side after receiving them if needed.

    Default fields return ~10KB per 10 templates vs ~250KB with all fields (25x smaller).
    """
    try:
        # SDK's list_templates() doesn't accept limit parameter
        # We get all templates and apply limit client-side
        templates = Sandbox.list_templates()

        # Convert to dict format
        data = [t.model_dump() for t in templates]

        # Apply limit client-side
        if limit > 0:
            data = data[:limit]

        # Client-side field filtering
        if fields and fields != "all":
            field_list = [f.strip() for f in fields.split(",")]
            data = [{k: v for k, v in t.items() if k in field_list} for t in data]

        return {
            "data": data,
            "count": len(data),
            "_fields": fields if fields != "all" else None,
            "_note": (
                f"Partial response with fields: {fields}. Use fields='all' for complete data."
                if fields and fields != "all"
                else None
            ),
        }
    except Exception as e:
        return {
            "error": "Failed to list templates",
            "exception": str(e),
        }


@mcp.tool()
def get_template(name: str) -> dict:
    """
    GET /v1/templates/{name} — get detailed template information.

    Retrieve detailed information about a specific template including its default
    configuration, supported regions, and resource specifications.

    Args:
        name: Template name (from list_templates response)

    Returns:
        Template object with id, full configuration, available regions, and defaults

    WORKFLOW: Use after list_templates() to get detailed info about a specific template
    before creating a sandbox.
    """
    try:
        template = Sandbox.get_template(name=name)
        return template.model_dump()
    except Exception as e:
        return {
            "error": "Failed to get template",
            "template_name": name,
            "exception": str(e),
        }


# ---------- Helper Functions for Unified execute_code ----------

def _validate_execute_code_parameters(
    mode: str,
    sandbox_id: Optional[str],
    timeout: int,
    language: str,
) -> Optional[dict]:
    """Validate execute_code parameters based on mode.

    Args:
        mode: Execution mode
        sandbox_id: Sandbox ID (required for non-isolated modes)
        timeout: Execution timeout
        language: Programming language

    Returns:
        Error dict if validation fails, None if valid
    """
    # Mode validation
    valid_modes = ["isolated", "persistent", "rich", "background"]
    if mode not in valid_modes:
        return {
            "error": "Invalid mode",
            "message": f"Mode must be one of: {', '.join(valid_modes)}",
            "provided": mode,
        }

    # Non-isolated modes require sandbox_id
    if mode in ["persistent", "rich", "background"] and sandbox_id is None:
        return {
            "error": "Missing sandbox_id",
            "message": f"Mode '{mode}' requires sandbox_id. Create sandbox first with create_sandbox() or use mode='isolated'.",
            "mode": mode,
        }

    # Language validation
    valid_languages = ["python", "javascript", "bash", "go"]
    if language not in valid_languages:
        return {
            "error": "Invalid language",
            "message": f"Language must be one of: {', '.join(valid_languages)}",
            "provided": language,
        }

    # Timeout validation
    if timeout <= 0:
        return {
            "error": "Invalid timeout",
            "message": "Timeout must be positive",
            "provided": timeout,
        }

    if mode in ["persistent", "rich"] and timeout > 300:
        return {
            "error": "Timeout too large",
            "message": "Persistent/rich mode timeout cannot exceed 300 seconds",
            "provided": timeout,
            "mode": mode,
        }

    return None


def _handle_execute_error(exception: Exception, mode: str) -> dict:
    """Handle execution errors with consistent error response format.

    Args:
        exception: The exception that occurred
        mode: Execution mode for context

    Returns:
        Standardized error dict
    """
    import traceback

    if isinstance(exception, SandboxNotFoundError):
        return {
            "error": "Sandbox not found",
            "exception": str(exception),
            "exception_type": "SandboxNotFoundError",
            "traceback": traceback.format_exc(),
            "mode": mode,
            "stdout": "",
            "stderr": "Sandbox not found",
            "exit_code": 1,
        }
    elif isinstance(exception, CodeExecutionError):
        return {
            "error": "Code execution failed",
            "exception": str(exception),
            "exception_type": "CodeExecutionError",
            "traceback": traceback.format_exc(),
            "mode": mode,
            "stdout": "",
            "stderr": str(exception),
            "exit_code": 1,
        }
    else:
        return {
            "error": "Unexpected error during code execution",
            "exception": str(exception),
            "exception_type": type(exception).__name__,
            "traceback": traceback.format_exc(),
            "mode": mode,
            "stdout": "",
            "stderr": f"Exception: {str(exception)}",
            "exit_code": 1,
        }


def _execute_persistent(
    sandbox_id: str,
    code: str,
    language: str,
    timeout: int,
    env: Optional[Dict[str, str]],
    working_dir: Optional[str],
) -> dict:
    """Execute code in existing sandbox (persistent mode).

    Args:
        sandbox_id: Sandbox ID
        code: Code to execute
        language: Programming language
        timeout: Execution timeout
        env: Environment variables
        working_dir: Working directory

    Returns:
        Execution result dict
    """
    sandbox = Sandbox.connect(sandbox_id=sandbox_id)
    result = sandbox.run_code(
        code=code,
        language=language,
        timeout=timeout,
        env=env or {},
        working_dir=working_dir,
    )

    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": result.exit_code,
        "execution_time": result.execution_time,
        "success": result.success,
        "mode": "persistent",
        "sandbox_id": sandbox_id,
    }


def _execute_isolated(
    code: str,
    language: str,
    timeout: int,
    env: Optional[Dict[str, str]],
    template_name: str,
    region: Optional[str],
    sandbox_id: Optional[str] = None,
) -> dict:
    """Execute code in ephemeral sandbox (isolated mode).

    Args:
        code: Code to execute
        language: Programming language
        timeout: Execution timeout
        env: Environment variables
        template_name: Template name to use
        region: Deployment region
        sandbox_id: Optional sandbox ID (if provided, uses existing sandbox)

    Returns:
        Execution result dict
    """
    if sandbox_id:
        # Use existing sandbox (user provided sandbox_id)
        sandbox = Sandbox.connect(sandbox_id=sandbox_id)
        result = sandbox.run_code(
            code=code,
            language=language,
            timeout=timeout,
            env=env or {},
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.exit_code,
            "execution_time": result.execution_time,
            "success": result.success,
            "mode": "isolated",
            "sandbox_id": sandbox_id,
            "_note": f"Executed in existing sandbox {sandbox_id} (isolated mode with sandbox_id)",
        }
    else:
        # Create new ephemeral sandbox with auto-cleanup
        with Sandbox.create(
            template=template_name,
            region=region,
            timeout_seconds=600,  # Auto-destroy after 10 minutes
            internet_access=True,
        ) as sandbox:
            result = sandbox.run_code(
                code=code,
                language=language,
                timeout=timeout,
                env=env or {},
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code,
                "execution_time": result.execution_time,
                "success": result.success,
                "mode": "isolated",
                "sandbox_id": sandbox.sandbox_id,
                "_note": f"Sandbox {sandbox.sandbox_id} will auto-destroy after 10 minutes. Use delete_sandbox('{sandbox.sandbox_id}') to clean up earlier.",
            }


def _execute_background(
    sandbox_id: str,
    code: str,
    language: str,
    timeout: int,
    env: Optional[Dict[str, str]],
    working_dir: Optional[str],
    name: Optional[str],
) -> dict:
    """Execute code in background (background mode).

    Args:
        sandbox_id: Sandbox ID
        code: Code to execute
        language: Programming language
        timeout: Execution timeout
        env: Environment variables
        working_dir: Working directory
        name: Process name

    Returns:
        Process info dict
    """
    sandbox = Sandbox.connect(sandbox_id=sandbox_id)
    result = sandbox.run_code_background(
        code=code,
        language=language,
        timeout=timeout,
        env=env,
        working_dir=working_dir,
        name=name,
    )

    # Add mode to result
    result["mode"] = "background"
    result["sandbox_id"] = sandbox_id
    return result


def _execute_rich(
    sandbox_id: str,
    code: str,
    language: str,
    timeout: int,
    env: Optional[Dict[str, str]],
    working_dir: str,
) -> dict:
    """Execute code with rich output capture (rich mode).

    Args:
        sandbox_id: Sandbox ID
        code: Code to execute
        language: Programming language
        timeout: Execution timeout
        env: Environment variables
        working_dir: Working directory

    Returns:
        Execution result dict with rich outputs
    """
    sandbox = Sandbox.connect(sandbox_id=sandbox_id)
    result = sandbox.run_code(
        code=code,
        language=language,
        timeout=timeout,
        env=env or {},
        working_dir=working_dir,
    )

    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": result.exit_code,
        "execution_time": result.execution_time,
        "success": result.success,
        "mode": "rich",
        "sandbox_id": sandbox_id,
        "rich_outputs": (
            [output.model_dump() for output in result.rich_outputs]
            if result.rich_outputs
            else []
        ),
    }


# ---------- VM Agent Interactions ----------


@mcp.tool()
def ping_vm(sandbox_id: str) -> dict:
    """
    Quick VM liveness check.

    Fast health check to verify VM is responsive. Returns immediately.

    Args:
        sandbox_id: Sandbox ID from create_sandbox() response

    Returns:
        Agent info with version and status

    Example:
        # Quick check before executing code
        ping_vm(sandbox_id)  # Returns agent info
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=sandbox_id)
        info = sandbox.get_agent_info()  # Returns dict
        return {
            "status": "ok",
            "agent_version": info.get("agent_version"),
            "agent": info.get("agent"),
            "features": info.get("features"),
            "uptime": info.get("uptime")
        }
    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "sandbox_id": sandbox_id,
        }
    except Exception as e:
        return {
            "error": "Failed to ping VM",
            "exception": str(e),
        }


@mcp.tool()
def get_vm_info(sandbox_id: str) -> dict:
    """
    GET /info — Get VM agent information and capabilities.

    Retrieve VM agent version, features, supported languages, and available endpoints.
    Use this to discover what capabilities the VM supports.

    Args:
        sandbox_id: Sandbox ID from create_sandbox() response

    Returns:
        VM info with version, features, supported languages, and available endpoints
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=sandbox_id)
        info = sandbox.get_agent_info()  # Returns dict, not Pydantic model
        return info  # Already a dict, no need for model_dump()
    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "sandbox_id": sandbox_id,
        }
    except Exception as e:
        return {
            "error": "Failed to get VM info",
            "exception": str(e),
        }


@mcp.tool()
def get_preview_url(sandbox_id: str, port: int) -> dict:
    """
    Get public preview URL for a service running in the sandbox.

    Returns the publicly accessible URL for any service running on a specific port
    inside the sandbox. This enables AI agents to deploy web services, APIs, or
    applications and get URLs to share with users or use for testing.

    IMPORTANT: The service must be running and listening on 0.0.0.0 (not localhost)
    for the preview URL to be accessible.

    Use Cases:
    - Deploy web applications and get public URLs
    - Start API servers and test endpoints
    - Run development servers (React, Next.js, Flask, FastAPI)
    - Share interactive demos with users
    - Test webhooks and callbacks

    Args:
        sandbox_id: Sandbox ID from create_sandbox()
        port: Port number where service is listening (e.g., 8080, 3000, 5000)

    Returns:
        dict with preview_url and port number

    Example 1 - Python HTTP Server:
        # Create sandbox
        sandbox = create_sandbox(template_id="code-interpreter")

        # Start HTTP server on port 8080
        execute_code(
            sandbox_id=sandbox["id"],
            code='''
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<h1>Hello from Hopx!</h1>')

HTTPServer(('0.0.0.0', 8080), Handler).serve_forever()
''',
            mode="background",
            language="python"
        )

        # Get preview URL
        url_info = get_preview_url(sandbox_id=sandbox["id"], port=8080)
        print(f"Access at: {url_info['preview_url']}")
        # Returns: {"preview_url": "https://8080-sandbox123.eu-1001.vms.hopx.dev/", "port": 8080}

    Example 2 - Node.js Express Server:
        execute_code(
            sandbox_id=sandbox_id,
            code='''
const express = require('express');
const app = express();
app.get('/', (req, res) => res.send('Hello!'));
app.listen(3000, '0.0.0.0');
''',
            mode="background",
            language="javascript"
        )

        url_info = get_preview_url(sandbox_id=sandbox_id, port=3000)
        # Returns: {"preview_url": "https://3000-sandbox123.eu-1001.vms.hopx.dev/", "port": 3000}

    Example 3 - FastAPI Application:
        # Write FastAPI app
        file_write(sandbox_id, "/workspace/app.py", '''
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI in Hopx!"}

@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id, "name": f"Item {item_id}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
''')

        # Install FastAPI and run
        execute_code(sandbox_id, code="pip install fastapi uvicorn", mode="persistent")
        execute_code(sandbox_id, code="python /workspace/app.py", mode="background")

        url_info = get_preview_url(sandbox_id, port=8000)
        # Access API at: https://8000-sandbox123.eu-1001.vms.hopx.dev/docs

    Notes:
    - Services must bind to 0.0.0.0, not 127.0.0.1 or localhost
    - Preview URLs are publicly accessible (no authentication)
    - URLs remain valid while sandbox is running
    - URLs automatically invalidate when sandbox is deleted
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=sandbox_id)
        preview_url = sandbox.get_preview_url(port)

        return {
            "preview_url": preview_url,
            "port": port,
            "sandbox_id": sandbox_id,
        }
    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "sandbox_id": sandbox_id,
        }
    except Exception as e:
        import traceback

        return {
            "error": "Failed to get preview URL",
            "exception": str(e),
            "exception_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "sandbox_id": sandbox_id,
            "port": port,
        }


@mcp.tool()
def get_agent_url(sandbox_id: str) -> dict:
    """
    Get the agent URL for the sandbox.

    Returns the internal agent URL (default port 7777) used for API communication
    with the sandbox. This is primarily for debugging and advanced use cases.

    For web services, use get_preview_url() instead.

    Args:
        sandbox_id: Sandbox ID from create_sandbox()

    Returns:
        dict with agent_url and sandbox_id

    Example:
        url_info = get_agent_url(sandbox_id="abc123")
        # Returns: {"agent_url": "https://7777-sandbox123.eu-1001.vms.hopx.dev/", "sandbox_id": "abc123"}
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=sandbox_id)
        agent_url = sandbox.agent_url

        return {
            "agent_url": agent_url,
            "sandbox_id": sandbox_id,
        }
    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "sandbox_id": sandbox_id,
        }
    except Exception as e:
        import traceback

        return {
            "error": "Failed to get agent URL",
            "exception": str(e),
            "exception_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "sandbox_id": sandbox_id,
        }


# ---------- Unified Code Execution API ----------


@mcp.tool()
def execute_code(
    code: str,
    mode: Literal["isolated", "persistent", "rich", "background"] = "isolated",
    sandbox_id: Optional[str] = None,
    language: str = "python",
    timeout: int = 30,
    env: Optional[Dict[str, str]] = None,
    working_dir: Optional[str] = None,
    name: Optional[str] = None,
    template_name: str = "code-interpreter",
    region: Optional[str] = None,
) -> dict:
    """
    Unified code execution API with 4 execution modes.

    Execute code in HOPX sandboxes using different execution strategies based on your needs.
    This unified API replaces separate functions with a single mode-based interface.

    EXECUTION MODES:

    1. ISOLATED (default) - One-shot ephemeral execution
       - Creates NEW sandbox, executes code, returns output, auto-destroys
       - Perfect for: Quick scripts, data analysis, testing, isolated computations
       - Parameters: code, language, timeout, env, template_name, region
       - Do NOT provide sandbox_id - it creates a new sandbox automatically
       - Example: execute_code(code="print('hello')", mode="isolated")

    2. PERSISTENT - Execute in existing sandbox
       - Runs code in pre-created sandbox with persistent state
       - Perfect for: Multi-step workflows, stateful operations, file persistence
       - Required: sandbox_id (from create_sandbox)
       - Parameters: sandbox_id, code, language, timeout, env, working_dir
       - Example: execute_code(sandbox_id="abc", code="x=1", mode="persistent")

    3. RICH - Execute with rich output capture
       - Captures matplotlib plots (PNG), pandas DataFrames (HTML), plotly charts
       - Perfect for: Data science, visualization, interactive analysis
       - Required: sandbox_id
       - Parameters: sandbox_id, code, language, timeout, env, working_dir
       - Example: execute_code(sandbox_id="abc", code="plt.plot([1,2,3])", mode="rich")

    4. BACKGROUND - Non-blocking execution via SDK
       - Starts execution in background, returns immediately with process_id
       - Perfect for: Long-running tasks, parallel processing, async workflows
       - Required: sandbox_id
       - Parameters: sandbox_id, code, language, timeout, env, working_dir, name
       - Check status: execute_list_processes(sandbox_id)
       - Example: execute_code(sandbox_id="abc", code="train_model()", mode="background")

    Args:
        code: Code to execute (required)
        mode: Execution mode - 'isolated', 'persistent', 'rich', 'background'
              Default: 'isolated'
        sandbox_id: Sandbox ID (required for all modes except 'isolated')
                    Do NOT provide for 'isolated' mode - it creates a new sandbox
        language: Programming language - 'python', 'javascript', 'bash', 'go'
                  Default: 'python'
        timeout: Execution timeout in seconds (default: 30, max varies by mode)
        env: Optional environment variables for execution
        working_dir: Working directory for execution (persistent/rich/background only)
        name: Process name for identification (background mode only)
        template_name: Template to use (isolated mode only, default: "code-interpreter")
        region: Deployment region (isolated mode only)

    Returns:
        Execution result dict with mode-specific fields:
        - All modes: stdout, stderr, exit_code, mode
        - isolated/persistent/rich: execution_time, success
        - rich: rich_outputs array with plots/dataframes
        - background: process_id, status

    Examples:

        # 1. ISOLATED - Quick one-shot execution
        result = execute_code(
            code="import pandas as pd; print(pd.DataFrame({'a': [1,2,3]}))",
            mode="isolated",
            language="python"
        )
        # Creates sandbox, executes, returns output, auto-destroys

        # 2. PERSISTENT - Multi-step workflow
        sandbox = create_sandbox(template_id="code-interpreter")
        execute_code(sandbox_id=sandbox["id"], code="pip install requests", mode="persistent")
        execute_code(sandbox_id=sandbox["id"], code="import requests; ...", mode="persistent")
        delete_sandbox(sandbox["id"])

        # 3. RICH - Data visualization
        result = execute_code(
            sandbox_id=sandbox_id,
            code="import matplotlib.pyplot as plt; plt.plot([1,2,3]); plt.savefig('/tmp/plot.png')",
            mode="rich"
        )
        # result["rich_outputs"] contains captured plots

        # 4. BACKGROUND - Long-running task
        proc = execute_code(
            sandbox_id=sandbox_id,
            code="import time; time.sleep(300); print('done')",
            mode="background",
            timeout=600,
            name="long-task"
        )
        # Check status: execute_list_processes(sandbox_id)

    Migration Guide (for deprecated functions):
        - execute_code_isolated() → execute_code(code=..., mode="isolated")
        - execute_code(sandbox_id, code) → execute_code(sandbox_id=..., code=..., mode="persistent")
        - execute_code_rich() → execute_code(sandbox_id=..., code=..., mode="rich")
        - execute_code_background() → execute_code(sandbox_id=..., code=..., mode="background")

    Note: Old functions still work but are deprecated. Use unified execute_code() for new code.
    """
    # Validate parameters
    validation_error = _validate_execute_code_parameters(
        mode=mode,
        sandbox_id=sandbox_id,
        timeout=timeout,
        language=language,
    )
    if validation_error:
        return validation_error

    # Execute based on mode
    try:
        if mode == "isolated":
            return _execute_isolated(
                code=code,
                language=language,
                timeout=timeout,
                env=env,
                template_name=template_name,
                region=region,
                sandbox_id=sandbox_id,
            )
        elif mode == "persistent":
            return _execute_persistent(
                sandbox_id=sandbox_id,
                code=code,
                language=language,
                timeout=timeout,
                env=env,
                working_dir=working_dir,
            )
        elif mode == "rich":
            return _execute_rich(
                sandbox_id=sandbox_id,
                code=code,
                language=language,
                timeout=timeout,
                env=env,
                working_dir=working_dir or "/tmp",
            )
        elif mode == "background":
            return _execute_background(
                sandbox_id=sandbox_id,
                code=code,
                language=language,
                timeout=timeout,
                env=env,
                working_dir=working_dir,
                name=name,
            )
    except Exception as e:
        return _handle_execute_error(e, mode)


# ---------- Deprecated Execute Code Functions (Backward Compatibility) ----------
# These functions are kept for backward compatibility but are deprecated.
# Use the unified execute_code() function with mode parameter instead.


@mcp.tool()
def execute_code_persistent(
    sandbox_id: str,
    code: str,
    language: str = "python",
    timeout: int = 30,
    env: Optional[Dict[str, str]] = None,
    working_dir: Optional[str] = None,
) -> dict:
    """
    DEPRECATED: Use execute_code(sandbox_id=..., code=..., mode="persistent") instead.

    Execute code inside a sandbox synchronously.

    This function is kept for backward compatibility. New code should use:
    execute_code(sandbox_id=sandbox_id, code=code, mode="persistent", ...)

    Args:
        sandbox_id: Sandbox ID from create_sandbox() response
        code: Code to execute
        language: Language - 'python', 'javascript', 'bash', 'go' (default: python)
        timeout: Execution timeout in seconds, max 300 (default: 30)
        env: Optional execution-specific environment variables
        working_dir: Optional working directory for execution (default: /tmp)

    Returns:
        Execution result with stdout, stderr, exit_code, execution_time, and success status
    """
    return execute_code(
        sandbox_id=sandbox_id,
        code=code,
        language=language,
        timeout=timeout,
        env=env,
        working_dir=working_dir,
        mode="persistent",
    )


@mcp.tool()
def execute_code_rich(
    sandbox_id: str,
    code: str,
    language: str = "python",
    timeout: int = 30,
    working_dir: str = "/tmp",
    env: Optional[Dict[str, str]] = None,
    capture_rich: bool = True,
) -> dict:
    """
    DEPRECATED: Use execute_code(sandbox_id=..., code=..., mode="rich") instead.

    Execute code with rich output capture (matplotlib plots, DataFrames).

    This function is kept for backward compatibility. New code should use:
    execute_code(sandbox_id=sandbox_id, code=code, mode="rich", ...)

    Args:
        sandbox_id: Sandbox ID from create_sandbox() response
        code: Code to execute (should generate plots/dataframes)
        language: Language - typically 'python' for data science (default: python)
        timeout: Execution timeout in seconds (default: 30)
        working_dir: Working directory for execution (default: /tmp)
        env: Optional execution-specific environment variables
        capture_rich: Enable rich output capture (default: True, ignored)

    Returns:
        Execution result with stdout, stderr, exit_code, execution_time, and rich_outputs array
    """
    return execute_code(
        sandbox_id=sandbox_id,
        code=code,
        language=language,
        timeout=timeout,
        env=env,
        working_dir=working_dir,
        mode="rich",
    )


@mcp.tool()
def execute_code_background(
    sandbox_id: str,
    code: str,
    language: str = "python",
    timeout: int = 300,
    env: Optional[Dict[str, str]] = None,
    working_dir: Optional[str] = None,
    name: Optional[str] = None,
) -> dict:
    """
    DEPRECATED: Use execute_code(sandbox_id=..., code=..., mode="background") instead.

    Execute long-running code in background.

    This function is kept for backward compatibility. New code should use:
    execute_code(sandbox_id=sandbox_id, code=code, mode="background", ...)

    Args:
        sandbox_id: Sandbox ID from create_sandbox() response
        code: Code to execute
        language: Language - 'python', 'javascript', 'bash', 'go'
        timeout: Max execution time in seconds (default: 300)
        env: Optional execution-specific environment variables
        working_dir: Optional working directory for execution
        name: Optional process name for easier identification

    Returns:
        Process info with process_id and status
    """
    return execute_code(
        sandbox_id=sandbox_id,
        code=code,
        language=language,
        timeout=timeout,
        env=env,
        working_dir=working_dir,
        name=name,
        mode="background",
    )


@mcp.tool()
def execute_code_isolated(
    code: str,
    language: str = "python",
    timeout: int = 30,
    env: Optional[Dict[str, str]] = None,
    template_name: str = "code-interpreter",
    region: Optional[str] = None,
) -> dict:
    """
    DEPRECATED: Use execute_code(code=..., mode="isolated") instead.

    Fast isolated code execution - Create ephemeral sandbox, execute code, return output.

    This function is kept for backward compatibility. New code should use:
    execute_code(code=code, mode="isolated", ...)

    Args:
        code: Code to execute
        language: 'python', 'javascript', 'bash', or 'go' (default: python)
        timeout: Execution timeout in seconds (default: 30, max: 300)
        env: Optional environment variables for the execution
        template_name: Template name to use (default: "code-interpreter")
        region: Optional region (e.g., 'us-east', 'eu-west')

    Returns:
        Execution result with stdout, stderr, exit_code, execution_time, sandbox_id
    """
    return execute_code(
        code=code,
        language=language,
        timeout=timeout,
        env=env,
        template_name=template_name,
        region=region,
        mode="isolated",
    )


@mcp.tool()
def execute_list_processes(sandbox_id: str, max_results: int = 100) -> dict:
    """
    GET /execute/processes — List background processes.

    List all background execution processes with their status.

    Args:
        sandbox_id: Sandbox ID from create_sandbox() response
        max_results: Maximum number of processes to return (default: 100, prevents context overflow)
                     Set to -1 for unlimited (use with caution)

    Returns:
        List of running/completed processes with status, stdout, stderr
        If truncated, response includes "truncated": true

    Note: This only lists processes started via execute_code_background().
    For all system processes, use list_processes() instead.
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=sandbox_id)
        processes = sandbox.list_processes()

        # Client-side truncation
        truncated = len(processes) > max_results if max_results > 0 else False
        if truncated:
            processes = processes[:max_results]

        return {
            "processes": processes,
            "count": len(processes),
            "truncated": truncated,
            "total_processes": len(processes) if not truncated else None,
        }
    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "sandbox_id": sandbox_id,
        }
    except Exception as e:
        return {
            "error": "Failed to list processes",
            "exception": str(e),
        }


@mcp.tool()
def execute_kill_process(sandbox_id: str, process_id: str) -> dict:
    """
    DELETE /execute/kill — Kill a background process.

    Terminate a running background process.

    Args:
        sandbox_id: Sandbox ID from create_sandbox() response
        process_id: Process ID from execute_code_background()

    Returns:
        Confirmation of process termination
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=sandbox_id)
        sandbox.kill_process(process_id)
        return {"status": "killed", "process_id": process_id}
    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "sandbox_id": sandbox_id,
        }
    except Exception as e:
        return {
            "error": "Failed to kill process",
            "exception": str(e),
        }


@mcp.tool()
def run_command(
    sandbox_id: str,
    command: str,
    timeout: int = 30,
    working_dir: str = "/workspace",
    env: Optional[Dict[str, str]] = None,
) -> dict:
    """
    POST /commands/run — Run a shell command in sandbox.

    Execute a shell command and wait for completion. Commands run in /bin/sh -c.

    Args:
        sandbox_id: Sandbox ID from create_sandbox() response
        command: Shell command to execute (e.g., "ls -la", "pip install requests")
        timeout: Command timeout in seconds (default: 30)
        working_dir: Working directory for command (default: /workspace)
        env: Optional execution-specific environment variables

    Returns:
        Command result with stdout, stderr, exit_code

    Example:
        # Install packages with env vars
        run_command(
            sandbox_id=sandbox_id,
            command="pip install numpy pandas",
            timeout=60,
            env={"PIP_INDEX_URL": "https://pypi.custom.com/simple"}
        )

        # Run tests with test env
        run_command(
            sandbox_id=sandbox_id,
            command="pytest tests/",
            working_dir="/workspace",
            env={"TEST_ENV": "true", "DATABASE_URL": "sqlite:///:memory:"}
        )
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=sandbox_id)
        result = sandbox.commands.run(
            command=command,
            timeout=timeout,
            working_dir=working_dir,
            env=env,
            background=False,
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.exit_code,
        }
    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "sandbox_id": sandbox_id,
            "stdout": "",
            "stderr": "Sandbox not found",
            "exit_code": 1,
        }
    except CommandExecutionError as e:
        return {
            "error": "Command execution failed",
            "exception": str(e),
            "stdout": "",
            "stderr": str(e),
            "exit_code": 1,
        }
    except Exception as e:
        return {
            "error": "Unexpected error during command execution",
            "exception": str(e),
            "stdout": "",
            "stderr": f"Exception: {str(e)}",
            "exit_code": 1,
        }


@mcp.tool()
def run_command_background(
    sandbox_id: str,
    command: str,
    timeout: int = 300,
    working_dir: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    name: Optional[str] = None,
) -> dict:
    """
    POST /commands/background — Run shell command in background.

    Start a shell command in background and return immediately. Use execute_list_processes()
    to check status.

    Args:
        sandbox_id: Sandbox ID from create_sandbox() response
        command: Shell command to execute
        timeout: Max execution time in seconds (default: 300)
        working_dir: Optional working directory for command
        env: Optional execution-specific environment variables
        name: Optional process name for easier identification

    Returns:
        Process info with process_id and status

    Example:
        # Start long-running server with env vars
        proc = run_command_background(
            sandbox_id=sandbox_id,
            command="python -m http.server 8000",
            working_dir="/workspace",
            env={"PORT": "8000", "HOST": "0.0.0.0"},
            name="web-server"
        )
        # Check status later
        processes = execute_list_processes(sandbox_id=sandbox_id)
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=sandbox_id)

        # SDK 0.2.7+ now handles background commands correctly
        result = sandbox.commands.run(
            command=command,
            timeout=timeout,
            working_dir=working_dir or "/workspace",
            env=env,
            background=True,
        )

        # Parse the process_id from stdout (format: "Background process started: cmd_xxx")
        if result.stdout and "cmd_" in result.stdout:
            process_id = result.stdout.split("cmd_")[-1].strip()
            process_id = f"cmd_{process_id}"
            return {
                "process_id": process_id,
                "status": "running",
                "message": result.stdout,
            }
        else:
            # Fallback if format changes
            return {
                "message": result.stdout or "Background command started",
                "status": "running",
                "exit_code": result.exit_code,
            }

    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "sandbox_id": sandbox_id,
        }
    except CommandExecutionError as e:
        import traceback

        return {
            "error": "Command execution failed",
            "exception": str(e),
            "exception_type": "CommandExecutionError",
            "traceback": traceback.format_exc(),
        }
    except Exception as e:
        import traceback

        return {
            "error": "Failed to run command in background",
            "exception": str(e),
            "exception_type": type(e).__name__,
            "traceback": traceback.format_exc(),
        }


@mcp.tool()
def list_processes(sandbox_id: str, max_results: int = 200) -> dict:
    """
    GET /processes — List all system processes.

    List all running processes in the sandbox with PID, command, and user info.

    Args:
        sandbox_id: Sandbox ID from create_sandbox() response
        max_results: Maximum number of processes to return (default: 200, prevents context overflow)
                     Set to -1 for unlimited (use with caution)

    Returns:
        Array of process objects with pid, command, user
        If truncated, response includes "truncated": true

    Example:
        processes = list_processes(sandbox_id=sandbox_id)
        for proc in processes["processes"]:
            print(f"PID {proc['pid']}: {proc['command']}")

    Warning: System process lists can be very large. Use max_results to limit output.
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=sandbox_id)
        processes = sandbox.list_system_processes()

        # Client-side truncation
        truncated = len(processes) > max_results if max_results > 0 else False
        if truncated:
            processes = processes[:max_results]

        return {
            "processes": processes,
            "count": len(processes),
            "truncated": truncated,
            "total_processes": len(processes) if not truncated else None,
        }
    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "sandbox_id": sandbox_id,
        }
    except Exception as e:
        return {
            "error": "Failed to list processes",
            "exception": str(e),
        }


@mcp.tool()
def file_read(sandbox_id: str, path: str) -> dict:
    """
    GET /files/read — Read file contents from sandbox.

    Read a file's contents as text. Only allowed paths like /workspace and /tmp can be read.

    Args:
        sandbox_id: Sandbox ID from create_sandbox() response
        path: File path to read (e.g., "/workspace/script.py")

    Returns:
        File contents and metadata

    Example:
        content = file_read(sandbox_id=sandbox_id, path="/workspace/output.txt")
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=sandbox_id)
        content = sandbox.files.read(path)
        return {"path": path, "content": content}
    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "sandbox_id": sandbox_id,
        }
    except HopxFileNotFoundError:
        return {
            "error": "File not found",
            "path": path,
        }
    except Exception as e:
        return {
            "error": "Failed to read file",
            "exception": str(e),
        }


@mcp.tool()
def file_write(sandbox_id: str, path: str, content: str) -> dict:
    """
    POST /files/write — Write file to sandbox.

    Write content to a file (creates or overwrites). Only allowed paths can be written.

    Args:
        sandbox_id: Sandbox ID from create_sandbox() response
        path: Destination file path (e.g., "/workspace/script.py")
        content: File content to write

    Returns:
        File info with path and size

    WORKFLOW: Write code files before executing them
        1. file_write(sandbox_id=id, path="/workspace/script.py", content="print('Hello')")
        2. execute_code(sandbox_id=id, code="exec(open('/workspace/script.py').read())")

    Example:
        file_write(
            sandbox_id=sandbox_id,
            path="/workspace/app.py",
            content="import flask\\napp = flask.Flask(__name__)\\n..."
        )
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=sandbox_id)
        sandbox.files.write(path, content)
        return {"path": path, "size": len(content)}
    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "sandbox_id": sandbox_id,
        }
    except Exception as e:
        return {
            "error": "Failed to write file",
            "exception": str(e),
        }


@mcp.tool()
def file_list(
    sandbox_id: str,
    path: str = "/workspace",
    max_results: int = 1000,
) -> dict:
    """
    GET /files/list — List directory contents in sandbox.

    List files and directories in a path.

    Args:
        sandbox_id: Sandbox ID from create_sandbox() response
        path: Directory path to list (default: /workspace)
        max_results: Maximum number of files to return (default: 1000, prevents context overflow)
                     Set to -1 for unlimited (use with caution)

    Returns:
        List of files and directories with metadata (name, size, modified time, is_dir)
        If truncated, response includes "truncated": true

    Example:
        files = file_list(sandbox_id=sandbox_id, path="/workspace")
        for file in files["files"]:
            print(f"{file['name']} - {file['size']} bytes")

    Warning: Large directories can produce very large responses. Use max_results to limit output.
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=sandbox_id)
        files = sandbox.files.list(path)

        # Convert FileInfo objects to dicts
        file_dicts = [f.model_dump() for f in files]

        # Client-side truncation
        truncated = len(file_dicts) > max_results if max_results > 0 else False
        if truncated:
            file_dicts = file_dicts[:max_results]

        return {
            "path": path,
            "files": file_dicts,
            "count": len(file_dicts),
            "truncated": truncated,
            "total_files": len(file_dicts) if not truncated else None,
        }
    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "sandbox_id": sandbox_id,
        }
    except Exception as e:
        return {
            "error": "Failed to list files",
            "exception": str(e),
        }


@mcp.tool()
def file_exists(sandbox_id: str, path: str) -> dict:
    """
    GET /files/exists — Check if file or directory exists.

    Check if a file or directory exists before reading or writing. Useful to
    avoid errors and implement conditional logic.

    Args:
        sandbox_id: Sandbox ID from create_sandbox() response
        path: Path to check

    Returns:
        Object with 'exists' boolean and 'path' string

    Example:
        check = file_exists(sandbox_id=sandbox_id, path="/workspace/config.json")
        if check["exists"]:
            content = file_read(sandbox_id=sandbox_id, path="/workspace/config.json")
        else:
            file_write(sandbox_id=sandbox_id, path="/workspace/config.json", content="{}")
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=sandbox_id)
        exists = sandbox.files.exists(path)
        return {"path": path, "exists": exists}
    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "sandbox_id": sandbox_id,
        }
    except Exception as e:
        return {
            "error": "Failed to check file existence",
            "exception": str(e),
        }


@mcp.tool()
def file_remove(sandbox_id: str, path: str) -> dict:
    """
    DELETE /files/remove — Delete file or directory from sandbox.

    Remove a file or directory (recursive for directories).

    Args:
        sandbox_id: Sandbox ID from create_sandbox() response
        path: Path to delete

    Returns:
        Confirmation of deletion
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=sandbox_id)
        sandbox.files.remove(path)
        return {"status": "removed", "path": path}
    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "sandbox_id": sandbox_id,
        }
    except HopxFileNotFoundError:
        return {
            "error": "File not found",
            "path": path,
        }
    except Exception as e:
        return {
            "error": "Failed to remove file",
            "exception": str(e),
        }


@mcp.tool()
def file_mkdir(sandbox_id: str, path: str) -> dict:
    """
    POST /files/mkdir — Create directory in sandbox.

    Create a directory (creates parent directories if needed).

    Args:
        sandbox_id: Sandbox ID from create_sandbox() response
        path: Directory path to create (e.g., "/workspace/myproject/src")

    Returns:
        Directory info

    Example:
        file_mkdir(sandbox_id=sandbox_id, path="/workspace/project/src")
        file_write(sandbox_id=sandbox_id, path="/workspace/project/src/main.py", content="print('Hello')")
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=sandbox_id)
        sandbox.files.mkdir(path)
        return {"status": "created", "path": path}
    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "sandbox_id": sandbox_id,
        }
    except Exception as e:
        return {
            "error": "Failed to create directory",
            "exception": str(e),
        }


@mcp.tool()
def get_system_metrics(sandbox_id: str) -> dict:
    """
    GET /system — Get sandbox system metrics.

    Retrieve CPU, memory, and disk usage metrics for the sandbox.

    Args:
        sandbox_id: Sandbox ID from create_sandbox() response

    Returns:
        System metrics including CPU usage, memory usage, disk usage, uptime

    Example:
        metrics = get_system_metrics(sandbox_id=sandbox_id)
        print(f"CPU: {metrics['cpu_percent']}%")
        print(f"Memory: {metrics['memory_percent']}%")
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=sandbox_id)
        metrics = sandbox.get_metrics_snapshot()
        return metrics
    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "sandbox_id": sandbox_id,
        }
    except Exception as e:
        return {
            "error": "Failed to get system metrics",
            "exception": str(e),
        }


@mcp.tool()
def env_get(sandbox_id: str) -> dict:
    """
    GET /env — Get all global environment variables.

    Retrieve all environment variables set in the sandbox. Sensitive values
    (containing KEY, SECRET, PASSWORD, TOKEN) are masked for security.

    Args:
        sandbox_id: Sandbox ID from create_sandbox() response

    Returns:
        Environment variables dict with masked sensitive values

    Example:
        env_vars = env_get(sandbox_id=sandbox_id)
        print(env_vars["env_vars"])  # {"DATABASE_URL": "postgres://...", "API_KEY": "***MASKED***"}
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=sandbox_id)
        env_vars = sandbox.env.get_all()
        return {"env_vars": env_vars}
    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "sandbox_id": sandbox_id,
        }
    except Exception as e:
        return {
            "error": "Failed to get environment variables",
            "exception": str(e),
        }


@mcp.tool()
def env_set(
    sandbox_id: str,
    env_vars: Dict[str, str],
    merge: bool = True,
) -> dict:
    """
    PUT/PATCH /env — Set or merge environment variables.

    Set environment variables in the sandbox. Use merge=True to add/update without
    clearing existing vars, or merge=False to replace all vars.

    Args:
        sandbox_id: Sandbox ID from create_sandbox() response
        env_vars: Dictionary of environment variables to set
        merge: If True, merge with existing vars (PATCH). If False, replace all (PUT). Default: True

    Returns:
        Empty response on success

    WORKFLOW: Set env vars before running code that needs them
        1. env_set(sandbox_id=id, env_vars={"API_KEY": "sk-123", "DATABASE_URL": "postgres://..."})
        2. execute_code(sandbox_id=id, code="import os; print(os.getenv('API_KEY'))")

    Example:
        # Merge new vars with existing
        env_set(sandbox_id=sandbox_id, env_vars={"DEBUG": "true", "API_KEY": "sk-123"}, merge=True)

        # Replace all vars
        env_set(sandbox_id=sandbox_id, env_vars={"ENVIRONMENT": "production"}, merge=False)
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=sandbox_id)
        if merge:
            sandbox.env.update(env_vars)
        else:
            sandbox.env.set_all(env_vars)
        return {
            "status": "success",
            "message": f"Successfully set {len(env_vars)} environment variable(s)",
            "variables_set": list(env_vars.keys()),
            "merge_mode": merge,
        }
    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "sandbox_id": sandbox_id,
        }
    except Exception as e:
        return {
            "error": "Failed to set environment variables",
            "exception": str(e),
        }


@mcp.tool()
def env_clear(sandbox_id: str) -> dict:
    """
    DELETE /env — Clear all global environment variables.

    Remove all environment variables from the sandbox.

    Args:
        sandbox_id: Sandbox ID from create_sandbox() response

    Returns:
        Empty response on success

    Example:
        env_clear(sandbox_id=sandbox_id)  # All env vars removed
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=sandbox_id)
        sandbox.env.set_all({})  # Clear all env vars
        return {"status": "cleared"}
    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "sandbox_id": sandbox_id,
        }
    except Exception as e:
        return {
            "error": "Failed to clear environment variables",
            "exception": str(e),
        }


@mcp.tool()
def cache_clear(sandbox_id: str) -> dict:
    """
    POST /cache/clear — Clear execution cache.

    Clear all cached execution results to free memory or force re-execution.

    Args:
        sandbox_id: Sandbox ID from create_sandbox() response

    Returns:
        Confirmation with success status

    Example:
        cache_clear(sandbox_id=sandbox_id)  # Clear all cached results
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=sandbox_id)
        sandbox.cache.clear()
        return {"status": "success"}
    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "sandbox_id": sandbox_id,
        }
    except Exception as e:
        return {
            "error": "Failed to clear cache",
            "exception": str(e),
        }


@mcp.tool()
def cache_stats(sandbox_id: str) -> dict:
    """
    GET /cache/stats — Get execution cache statistics.

    Get cache statistics including total cached items and hit rate.

    Args:
        sandbox_id: Sandbox ID from create_sandbox() response

    Returns:
        Cache stats with total_cached count and hit_rate percentage

    Example:
        stats = cache_stats(sandbox_id=sandbox_id)
        print(f"Cache hit rate: {stats['hit_rate']}%")
        print(f"Total cached: {stats['total_cached']}")
    """
    try:
        sandbox = Sandbox.connect(sandbox_id=sandbox_id)
        stats = sandbox.cache.stats()
        return stats
    except SandboxNotFoundError:
        return {
            "error": "Sandbox not found",
            "sandbox_id": sandbox_id,
        }
    except Exception as e:
        return {
            "error": "Failed to get cache stats",
            "exception": str(e),
        }


# ============================================================================
# MCP PROMPTS - Reusable templates for common workflows
# ============================================================================


@mcp.prompt()
def quick_code_execution():
    """
    Quick Code Execution Guide

    Use this template when you need to execute code in an isolated environment.
    """
    return """You have access to HOPX Sandbox API for isolated code execution.

PRIMARY METHOD: execute_code() with mode parameter

EXECUTION MODES:
- isolated: One-shot execution (recommended for most tasks) - Creates sandbox, executes, auto-destroys
- persistent: Execute in existing sandbox
- rich: Execute with rich output capture (matplotlib plots, DataFrames)
- background: Non-blocking execution via SDK

USE CASES:
✓ Data analysis with pandas/numpy
✓ Code testing and validation
✓ Package installation and testing
✓ Math/scientific computations
✓ Quick scripts (Python/JS/Bash/Go)

WORKFLOW - One-shot execution:
result = execute_code(
    code="import pandas as pd; print(pd.DataFrame({'a': [1,2,3]}))",
    mode="isolated",
    language="python",
    timeout=30,
    env={"API_KEY": "optional-key"}
)

WORKFLOW - Multi-step with persistent sandbox:
sandbox = create_sandbox(template_id="code-interpreter")
execute_code(sandbox_id=sandbox["id"], code="pip install requests", mode="persistent")
execute_code(sandbox_id=sandbox["id"], code="import requests; ...", mode="persistent")
delete_sandbox(sandbox["id"])

LANGUAGES SUPPORTED:
• python (default) - Full Python 3.x with common packages
• javascript - Node.js runtime
• bash - Shell commands
• go - Go compilation and execution

FEATURES:
• Isolated containers (secure)
• Internet access enabled
• Auto-cleanup (10min timeout for isolated mode)
• Fast startup (~0.1ms)
• Concurrent execution supported

TIPS:
1. Use mode="isolated" for one-off code execution
2. Use create_sandbox() → mode="persistent" for multiple operations
3. Install packages: execute_code(code="pip install numpy pandas", mode="isolated")
4. Capture output: All stdout/stderr captured in result

EXAMPLE - Data Analysis:
execute_code(code='''
import pandas as pd
import matplotlib.pyplot as plt

# Load and analyze data
data = {"year": [2020, 2021, 2022], "revenue": [100, 150, 200]}
df = pd.DataFrame(data)
print(df.describe())
print(f"Growth: {df['revenue'].pct_change().mean()*100:.1f}%")
''', mode="isolated")

EXAMPLE - API Testing:
execute_code(
    code='''
import requests
response = requests.get("https://api.github.com")
print(f"Status: {response.status_code}")
print(response.json().keys())
''',
    mode="isolated",
    env={"GITHUB_TOKEN": "ghp_xxx"}
)

Remember: Isolated mode sandboxes auto-destroy after 10 minutes. For long-running tasks,
use create_sandbox() with mode="background" and manage lifecycle manually.
"""


def main():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
