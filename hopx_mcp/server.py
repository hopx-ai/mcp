import os
import time
from typing import Any, Dict, Optional

import httpx
from mcp.server.fastmcp import FastMCP

# --- Config (env) ---
BASE_URL = os.getenv("HOPX_BASE_URL", "https://api.hopx.dev")
API_KEY = os.getenv("HOPX_API_KEY")  # sent as X-API-Key
BEARER = os.getenv("HOPX_BEARER_TOKEN")  # optional fallback

# --- HTTP client ---
_client = httpx.Client(base_url=BASE_URL, timeout=30.0)


def _auth_headers() -> Dict[str, str]:
    h = {"Accept": "application/json"}
    if API_KEY:
        h["X-API-Key"] = API_KEY
    if BEARER:
        h["Authorization"] = f"Bearer {BEARER}"
    return h


def _handle(resp: httpx.Response) -> Any:
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        # Return structured error to the host instead of throwing
        err_body = None
        try:
            err_body = e.response.json()
        except Exception:
            err_body = {"text": e.response.text}
        return {
            "status_code": e.response.status_code,
            "error": str(e),
            "body": err_body,
        }
    # success
    try:
        return resp.json()
    except Exception:
        return {"text": resp.text}


mcp = FastMCP(
    "hopx",
    instructions="""HOPX Sandbox API provides fast isolated code execution in ephemeral cloud containers.

PRIMARY USE: execute_code_isolated() - One-shot code execution (recommended for most tasks)
Creates sandbox, executes code, returns output, auto-destroys. Fast startup (~0.1ms), supports Python/JavaScript/Bash/Go.

WHEN TO USE WHAT:
• Quick execution (data analysis, testing, scripts): execute_code_isolated()
• Multi-step workflows (install deps → run code → check files): create_sandbox() then use execute_code(), file_*, run_command()
• Long tasks (5-30min): execute_code_background()
• Very long tasks (30min+): execute_code_async() with webhook callback

IMPORTANT:
- All VM operations require auth_token from sandbox["auth_token"]
- list_templates() returns many templates - use limit parameter to control response size
- Sandboxes auto-destroy based on timeout_seconds parameter
- Execute tools support request-specific env vars (preferred over global env_set)

TYPICAL WORKFLOWS:
1. One-shot: execute_code_isolated(code="...", language="python")
2. Persistent: create_sandbox(template_id="<id>") → extract vm_url + auth_token → execute_code(vm_url, code, auth_token=auth_token)
3. Long-running: create_sandbox() → execute_code_async(..., callback_url="https://...")

See individual tool descriptions for detailed parameters and examples.""",
)


# ---------- System ----------
@mcp.tool()
def health() -> dict:
    """GET /health — public health check."""
    r = _client.get("/health", headers=_auth_headers())
    return _handle(r)


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
    params: dict[str, Any] = {"limit": limit}
    if status:
        params["status"] = status
    if region:
        params["region"] = region
    r = _client.get("/v1/sandboxes", params=params, headers=_auth_headers())
    return _handle(r)


@mcp.tool()
def create_sandbox(
    template_id: str,
    vcpu: Optional[int] = None,
    memory_mb: Optional[int] = None,
    region: Optional[str] = None,
    disk_gb: Optional[int] = None,
    timeout_seconds: Optional[int] = None,
    internet_access: Optional[bool] = None,
) -> dict:
    """
    POST /v1/sandboxes — create a new sandbox.

    WORKFLOW: First use list_templates() to find available templates, then create a sandbox
    with the template's id. Templates provide default resources (vcpu, memory, disk) which
    can be overridden if needed.

    Args:
        template_id: Template ID to use (e.g., "628"). Get from list_templates() or get_template()
        vcpu: Number of virtual CPUs (optional, uses template default if not specified)
        memory_mb: Memory in megabytes (optional, uses template default if not specified)
        region: Deployment region, e.g., 'us-east', 'eu-west' (optional)
        disk_gb: Disk size in gigabytes (optional, uses template default if not specified)
        timeout_seconds: Auto-shutdown timeout in seconds (optional, e.g., 3600 for 1 hour)
        internet_access: Enable internet access (optional, default is typically true)

    Returns:
        Created sandbox object with id, status, connection details, and configuration

    Example flow:
        1. templates = list_templates(limit=20)
        2. template = templates["data"][0]  # Pick a template
        3. sandbox = create_sandbox(template_id=template["id"], region="eu-west", timeout_seconds=3600)
    """
    body: Dict[str, Any] = {"template_id": template_id}
    if vcpu is not None:
        body["vcpu"] = vcpu
    if memory_mb is not None:
        body["memory_mb"] = memory_mb
    if region is not None:
        body["region"] = region
    if disk_gb is not None:
        body["disk_gb"] = disk_gb
    if timeout_seconds is not None:
        body["timeout_seconds"] = timeout_seconds
    if internet_access is not None:
        body["internet_access"] = internet_access
    r = _client.post("/v1/sandboxes", json=body, headers=_auth_headers())
    return _handle(r)


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
    r = _client.get(f"/v1/sandboxes/{id}", headers=_auth_headers())
    return _handle(r)


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
    r = _client.delete(f"/v1/sandboxes/{id}", headers=_auth_headers())
    return _handle(r)


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
    body: Dict[str, Any] = {"timeout_seconds": timeout_seconds}
    r = _client.put(f"/v1/sandboxes/{id}/timeout", json=body, headers=_auth_headers())
    return _handle(r)


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
    r = _client.post(f"/v1/sandboxes/{id}/resume", headers=_auth_headers())
    return _handle(r)


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
    params: Dict[str, Any] = {"limit": limit}

    r = _client.get("/v1/templates", params=params, headers=_auth_headers())
    result = _handle(r)

    # Client-side field filtering (Google-style partial response)
    if fields and fields != "all" and isinstance(result, dict) and "data" in result:
        templates = result["data"]
        if isinstance(templates, list):
            field_list = [f.strip() for f in fields.split(",")]
            filtered = []
            for t in templates:
                filtered_template = {
                    field: t.get(field) for field in field_list if field in t
                }
                filtered.append(filtered_template)
            result["data"] = filtered
            result["_fields"] = fields
            result["_note"] = (
                f"Partial response with fields: {fields}. Use fields='all' for complete data."
            )

    return result


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
    r = _client.get(f"/v1/templates/{name}", headers=_auth_headers())
    return _handle(r)


# ---------- VM Agent Interactions ----------
# These tools interact with the VM Agent API running inside a sandbox


def _vm_request(
    vm_url: str, method: str, path: str, auth_token: Optional[str] = None, **kwargs
) -> Any:
    """Helper to make requests to a VM Agent.

    Args:
        vm_url: VM URL from sandbox connection
        method: HTTP method
        path: API path
        , auth_token: Optional auth token from sandbox creation response.
                    If provided, used as Bearer token in Authorization header.
                    If not provided, falls back to X-API-Secret with global API key.
    """
    # Ensure vm_url has a scheme
    if not vm_url.startswith("http"):
        vm_url = f"https://{vm_url}"

    # VM Agent authentication: prefer auth_token, fallback to API_KEY
    headers = kwargs.pop("headers", {})
    if auth_token:
        # Use sandbox-specific auth token (recommended)
        headers["Authorization"] = f"Bearer {auth_token}"
    elif API_KEY:
        # Fallback: try X-API-Secret with global API key
        headers["X-API-Secret"] = API_KEY
    if BEARER and not auth_token:
        headers["Authorization"] = f"Bearer {BEARER}"

    with httpx.Client(timeout=kwargs.pop("timeout", 60.0)) as vm_client:
        url = f"{vm_url}{path}"
        r = vm_client.request(method, url, headers=headers, **kwargs)
        return _handle(r)


@mcp.tool()
def ping_vm(vm_url: str, auth_token: Optional[str] = None) -> dict:
    """
    GET /ping — Quick VM liveness check.

    Fast health check to verify VM is responsive. Returns immediately.

    Args:
        vm_url: VM URL from sandbox connection details

    Returns:
        Simple pong response

    Example:
        # Quick check before executing code
        ping_vm(vm_url)  # Returns: "pong"
    """
    return _vm_request(vm_url, "GET", "/ping", auth_token=auth_token)


@mcp.tool()
def get_vm_info(vm_url: str, auth_token: Optional[str] = None) -> dict:
    """
    GET /info — Get VM agent information and capabilities.

    Retrieve VM agent version, features, supported languages, and available endpoints.
    Use this to discover what capabilities the VM supports.

    Args:
        vm_url: VM URL from sandbox connection details

    Returns:
        VM info with version, features, supported languages, and available endpoints
    """
    return _vm_request(vm_url, "GET", "/info", auth_token=auth_token)


@mcp.tool()
def execute_code(
    vm_url: str,
    code: str,
    language: str = "python",
    timeout: int = 30,
    env: Optional[Dict[str, str]] = None,
    working_dir: Optional[str] = None,
    auth_token: Optional[str] = None,
) -> dict:
    """
    POST /execute — Execute code inside a sandbox synchronously.

    Run code in a sandbox and wait for completion. This is the primary way to run
    code in sandboxes after creation.

    Args:
        vm_url: VM URL from sandbox connection details (e.g., "7777-vmid.region.vms.hopx.dev")
                Get this from create_sandbox() response as sandbox["direct_url"]
        code: Code to execute
        language: Language - 'python', 'javascript', 'bash', 'go' (default: python)
        timeout: Execution timeout in seconds, max 300 (default: 30)
        env: Optional execution-specific environment variables (overrides global env)
             Priority: Request env > Global env > Agent env
        working_dir: Optional working directory for execution (default: /tmp)
        auth_token: Optional auth token from sandbox["auth_token"].
                    Required for authenticated VM operations. Extract from create_sandbox() response.

    Returns:
        Execution result with stdout, stderr, exit_code, and execution_time

    WORKFLOW:
        1. sandbox = create_sandbox(template_id="73")
        2. vm_url = sandbox["direct_url"]  # Extract VM URL
        3. auth_token = sandbox["auth_token"]  # Extract auth token
        4. result = execute_code(vm_url=vm_url, code="print('Hello')", auth_token=auth_token)

    Example with auth token and env vars:
        sandbox = create_sandbox(template_id="73", timeout_seconds=600)
        result = execute_code(
            vm_url=sandbox["direct_url"],
            auth_token=sandbox["auth_token"],
            code="import os; print(os.getenv('API_KEY'))",
            language="python",
            env={"API_KEY": "secret-123", "DEBUG": "true"}
        )
    """
    body: Dict[str, Any] = {
        "code": code,
        "language": language,
        "timeout": timeout,
    }
    if env:
        body["env"] = env
    if working_dir:
        body["working_dir"] = working_dir
    return _vm_request(vm_url, "POST", "/execute", auth_token=auth_token, json=body)


@mcp.tool()
def execute_code_rich(
    vm_url: str,
    code: str,
    language: str = "python",
    timeout: int = 30,
    working_dir: str = "/tmp",
    env: Optional[Dict[str, str]] = None,
    capture_rich: bool = True,
    auth_token: Optional[str] = None,
) -> dict:
    """
        POST /execute/rich — Execute code with rich output capture.

        Execute code and automatically capture rich outputs like matplotlib plots (PNG),
        pandas DataFrames (HTML), and plotly charts (HTML). Perfect for data science workflows.

        Args:
            vm_url: VM URL from sandbox connection details
            code: Code to execute (should generate plots/dataframes)
            language: Language - typically 'python' for data science (default: python)
            timeout: Execution timeout in seconds (default: 30)
            working_dir: Working directory for execution (default: /tmp)
            env: Optional execution-specific environment variables
            capture_rich: Enable rich output capture (default: True)

        Returns:
            Execution result with stdout, stderr, exit_code, and rich_outputs array
            containing captured plots/dataframes with base64-encoded content

        Requirements: matplotlib, pandas, or plotly must be installed in the sandbox

        Example:
            result = execute_code_rich(
                vm_url=vm_url,
                code='''
    import matplotlib.pyplot as plt
    plt.plot([1, 2, 3], [1, 4, 9])
    plt.title("Data Visualization")
    plt.savefig("/tmp/plot.png")
    ''',
                language="python",
                env={"MPLBACKEND": "Agg"}
            )
            # result["rich_outputs"] contains the captured plot
    """
    body: Dict[str, Any] = {
        "code": code,
        "language": language,
        "timeout": timeout,
        "working_dir": working_dir,
        "capture_rich": capture_rich,
    }
    if env:
        body["env"] = env
    return _vm_request(
        vm_url, "POST", "/execute/rich", auth_token=auth_token, json=body
    )


@mcp.tool()
def execute_code_background(
    vm_url: str,
    code: str,
    language: str = "python",
    timeout: int = 300,
    env: Optional[Dict[str, str]] = None,
    working_dir: Optional[str] = None,
    auth_token: Optional[str] = None,
) -> dict:
    """
    POST /execute/background — Execute long-running code in background.

    Start code execution in background and return immediately. Use execute_list_processes()
    to check status and execute_kill_process() to terminate.

    Args:
        vm_url: VM URL from sandbox connection details
        code: Code to execute
        language: Language - 'python', 'javascript', 'bash', 'go'
        timeout: Max execution time in seconds (default: 300)
        env: Optional execution-specific environment variables
        working_dir: Optional working directory for execution

    Returns:
        Process info with process_id and status

    WORKFLOW:
        1. Start: proc = execute_code_background(vm_url, code="import time; time.sleep(60)")
        2. Check: status = execute_list_processes(vm_url)
        3. Kill: execute_kill_process(vm_url, proc["process_id"])
    """
    body: Dict[str, Any] = {
        "code": code,
        "language": language,
        "timeout": timeout,
    }
    if env:
        body["env"] = env
    if working_dir:
        body["working_dir"] = working_dir
    return _vm_request(
        vm_url, "POST", "/execute/background", auth_token=auth_token, json=body
    )


@mcp.tool()
def execute_code_async(
    vm_url: str,
    code: str,
    callback_url: str,
    language: str = "python",
    timeout: int = 3600,
    env: Optional[Dict[str, str]] = None,
    working_dir: Optional[str] = None,
    callback_headers: Optional[Dict[str, str]] = None,
    callback_signature_secret: Optional[str] = None,
    auth_token: Optional[str] = None,
) -> dict:
    """
    POST /execute/async — Execute code asynchronously with webhook callback.

    For VERY long-running code (>5 minutes). Server executes in background and POSTs
    results to your callback_url when done. Returns immediately with execution_id.

    Args:
        vm_url: VM URL from sandbox connection details
        code: Code to execute
        callback_url: URL to POST results to when execution completes (required)
        language: Language - 'python', 'javascript', 'bash', 'go' (default: python)
        timeout: Max execution time in seconds (default: 3600 = 1 hour)
        env: Optional execution-specific environment variables
        working_dir: Optional working directory for execution
        callback_headers: Optional custom headers to include in callback request
        callback_signature_secret: Optional secret to sign callback payload (HMAC-SHA256)

    Returns:
        202 Accepted with execution_id, status: "queued", callback_url

    Callback Behavior:
        - Server POSTs to callback_url with execution results
        - Headers include: X-HOPX-Signature (if secret provided), X-HOPX-Timestamp
        - Custom headers from callback_headers are included
        - Verify signature to ensure authenticity

    Use Cases:
        - ML model training (30+ minutes)
        - Large dataset processing
        - Video encoding/processing
        - Long-running simulations

    Example:
        # Start 30-minute ML training
        result = execute_code_async(
            vm_url=vm_url,
            code="train_model(); save_results()",
            callback_url="https://myapp.com/webhooks/ml-complete",
            env={"WANDB_API_KEY": "key", "HF_TOKEN": "token"},
            callback_headers={"Authorization": "Bearer my-secret"},
            callback_signature_secret="webhook-secret-123",
            timeout=1800
        )
        # Returns immediately: {"execution_id": "abc123", "status": "queued"}
        # 30 minutes later: POST to https://myapp.com/webhooks/ml-complete
    """
    body: Dict[str, Any] = {
        "code": code,
        "language": language,
        "callback_url": callback_url,
        "timeout": timeout,
    }
    if env:
        body["env"] = env
    if working_dir:
        body["working_dir"] = working_dir
    if callback_headers:
        body["callback_headers"] = callback_headers
    if callback_signature_secret:
        body["callback_signature_secret"] = callback_signature_secret

    return _vm_request(
        vm_url, "POST", "/execute/async", auth_token=auth_token, json=body
    )


@mcp.tool()
def execute_list_processes(
    vm_url: str, max_results: int = 100, auth_token: Optional[str] = None
) -> dict:
    """
    GET /execute/processes — List background processes.

    List all background execution processes with their status.

    Args:
        vm_url: VM URL from sandbox connection details
        max_results: Maximum number of processes to return (default: 100, prevents context overflow)
                     Set to -1 for unlimited (use with caution)

    Returns:
        List of running/completed processes with status, stdout, stderr
        If truncated, response includes "truncated": true

    Note: This only lists processes started via execute_code_background().
    For all system processes, use list_processes() instead.
    """
    result = _vm_request(vm_url, "GET", "/execute/processes", auth_token=auth_token)

    # Client-side truncation if response is too large
    if max_results > 0 and isinstance(result, dict) and "processes" in result:
        processes = result["processes"]
        if len(processes) > max_results:
            result["processes"] = processes[:max_results]
            result["truncated"] = True
            result["total_processes"] = len(processes)
            result["showing_processes"] = max_results

    return result


@mcp.tool()
def execute_kill_process(
    vm_url: str, process_id: str, auth_token: Optional[str] = None
) -> dict:
    """
    DELETE /execute/kill — Kill a background process.

    Terminate a running background process.

    Args:
        vm_url: VM URL from sandbox connection details
        process_id: Process ID from execute_code_background()

    Returns:
        Confirmation of process termination
    """
    return _vm_request(
        vm_url,
        "DELETE",
        "/execute/kill",
        auth_token=auth_token,
        params={"process_id": process_id},
    )


@mcp.tool()
def run_command(
    vm_url: str,
    command: str,
    timeout: int = 30,
    working_dir: str = "/workspace",
    env: Optional[Dict[str, str]] = None,
    auth_token: Optional[str] = None,
) -> dict:
    """
    POST /commands/run — Run a shell command in sandbox.

    Execute a shell command and wait for completion. Commands run in /bin/sh -c.

    Args:
        vm_url: VM URL from sandbox connection details
        command: Shell command to execute (e.g., "ls -la", "pip install requests")
        timeout: Command timeout in seconds (default: 30)
        working_dir: Working directory for command (default: /workspace)
        env: Optional execution-specific environment variables

    Returns:
        Command result with stdout, stderr, exit_code

    Example:
        # Install packages with env vars
        run_command(
            vm_url,
            "pip install numpy pandas",
            timeout=60,
            env={"PIP_INDEX_URL": "https://pypi.custom.com/simple"}
        )

        # Run tests with test env
        run_command(
            vm_url,
            "pytest tests/",
            working_dir="/workspace",
            env={"TEST_ENV": "true", "DATABASE_URL": "sqlite:///:memory:"}
        )
    """
    body: Dict[str, Any] = {
        "command": command,
        "timeout": timeout,
        "working_dir": working_dir,
    }
    if env:
        body["env"] = env
    return _vm_request(
        vm_url, "POST", "/commands/run", auth_token=auth_token, json=body
    )


@mcp.tool()
def run_command_background(
    vm_url: str,
    command: str,
    timeout: int = 300,
    working_dir: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    name: Optional[str] = None,
    auth_token: Optional[str] = None,
) -> dict:
    """
    POST /commands/background — Run shell command in background.

    Start a shell command in background and return immediately. Use execute_list_processes()
    to check status.

    Args:
        vm_url: VM URL from sandbox connection details
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
            vm_url,
            command="python -m http.server 8000",
            working_dir="/workspace",
            env={"PORT": "8000", "HOST": "0.0.0.0"},
            name="web-server"
        )
        # Check status later
        processes = execute_list_processes(vm_url)
    """
    body: Dict[str, Any] = {
        "command": command,
        "timeout": timeout,
    }
    if working_dir:
        body["working_dir"] = working_dir
    if env:
        body["env"] = env
    if name:
        body["name"] = name

    return _vm_request(
        vm_url, "POST", "/commands/background", auth_token=auth_token, json=body
    )


@mcp.tool()
def list_processes(
    vm_url: str, max_results: int = 200, auth_token: Optional[str] = None
) -> dict:
    """
    GET /processes — List all system processes.

    List all running processes in the sandbox with PID, command, and user info.

    Args:
        vm_url: VM URL from sandbox connection details
        max_results: Maximum number of processes to return (default: 200, prevents context overflow)
                     Set to -1 for unlimited (use with caution)

    Returns:
        Array of process objects with pid, command, user
        If truncated, response includes "truncated": true

    Example:
        processes = list_processes(vm_url)
        for proc in processes["processes"]:
            print(f"PID {proc['pid']}: {proc['command']}")

    Warning: System process lists can be very large. Use max_results to limit output.
    """
    result = _vm_request(vm_url, "GET", "/processes", auth_token=auth_token)

    # Client-side truncation if response is too large
    if max_results > 0 and isinstance(result, dict):
        # Handle both direct array and nested structure
        processes = result if isinstance(result, list) else result.get("processes", [])

        if isinstance(processes, list) and len(processes) > max_results:
            truncated_processes = processes[:max_results]
            return {
                "processes": truncated_processes,
                "truncated": True,
                "total_processes": len(processes),
                "showing_processes": max_results,
            }

    return result


@mcp.tool()
def file_read(vm_url: str, path: str, auth_token: Optional[str] = None) -> dict:
    """
    GET /files/read — Read file contents from sandbox.

    Read a file's contents as text. Only allowed paths like /workspace and /tmp can be read.

    Args:
        vm_url: VM URL from sandbox connection details
        path: File path to read (e.g., "/workspace/script.py")

    Returns:
        File contents and metadata

    Example:
        content = file_read(vm_url, "/workspace/output.txt")
    """
    return _vm_request(
        vm_url, "GET", "/files/read", auth_token=auth_token, params={"path": path}
    )


@mcp.tool()
def file_write(
    vm_url: str, path: str, content: str, auth_token: Optional[str] = None
) -> dict:
    """
    POST /files/write — Write file to sandbox.

    Write content to a file (creates or overwrites). Only allowed paths can be written.

    Args:
        vm_url: VM URL from sandbox connection details
        path: Destination file path (e.g., "/workspace/script.py")
        content: File content to write

    Returns:
        File info with path and size

    WORKFLOW: Write code files before executing them
        1. file_write(vm_url, "/workspace/script.py", "print('Hello')")
        2. execute_code(vm_url, "exec(open('/workspace/script.py').read())")

    Example:
        file_write(
            vm_url,
            "/workspace/app.py",
            "import flask\\napp = flask.Flask(__name__)\\n..."
        )
    """
    body: Dict[str, Any] = {
        "path": path,
        "content": content,
    }
    return _vm_request(vm_url, "POST", "/files/write", auth_token=auth_token, json=body)


@mcp.tool()
def file_list(
    vm_url: str,
    path: str = "/workspace",
    max_results: int = 1000,
    auth_token: Optional[str] = None,
) -> dict:
    """
    GET /files/list — List directory contents in sandbox.

    List files and directories in a path.

    Args:
        vm_url: VM URL from sandbox connection details
        path: Directory path to list (default: /workspace)
        max_results: Maximum number of files to return (default: 1000, prevents context overflow)
                     Set to -1 for unlimited (use with caution)

    Returns:
        List of files and directories with metadata (name, size, modified time, is_dir)
        If truncated, response includes "truncated": true

    Example:
        files = file_list(vm_url, "/workspace")
        for file in files["files"]:
            print(f"{file['name']} - {file['size']} bytes")

    Warning: Large directories can produce very large responses. Use max_results to limit output.
    """
    result = _vm_request(
        vm_url, "GET", "/files/list", auth_token=auth_token, params={"path": path}
    )

    # Client-side truncation if response is too large
    if max_results > 0 and isinstance(result, dict) and "files" in result:
        files = result["files"]
        if len(files) > max_results:
            result["files"] = files[:max_results]
            result["truncated"] = True
            result["total_files"] = len(files)
            result["showing_files"] = max_results

    return result


@mcp.tool()
def file_exists(vm_url: str, path: str, auth_token: Optional[str] = None) -> dict:
    """
    GET /files/exists — Check if file or directory exists.

    Check if a file or directory exists before reading or writing. Useful to
    avoid errors and implement conditional logic.

    Args:
        vm_url: VM URL from sandbox connection details
        path: Path to check

    Returns:
        Object with 'exists' boolean and 'path' string

    Example:
        check = file_exists(vm_url, "/workspace/config.json")
        if check["exists"]:
            content = file_read(vm_url, "/workspace/config.json")
        else:
            file_write(vm_url, "/workspace/config.json", "{}")
    """
    return _vm_request(
        vm_url, "GET", "/files/exists", auth_token=auth_token, params={"path": path}
    )


@mcp.tool()
def file_remove(vm_url: str, path: str, auth_token: Optional[str] = None) -> dict:
    """
    DELETE /files/remove — Delete file or directory from sandbox.

    Remove a file or directory (recursive for directories).

    Args:
        vm_url: VM URL from sandbox connection details
        path: Path to delete

    Returns:
        Confirmation of deletion
    """
    return _vm_request(
        vm_url, "DELETE", "/files/remove", auth_token=auth_token, params={"path": path}
    )


@mcp.tool()
def file_mkdir(vm_url: str, path: str, auth_token: Optional[str] = None) -> dict:
    """
    POST /files/mkdir — Create directory in sandbox.

    Create a directory (creates parent directories if needed).

    Args:
        vm_url: VM URL from sandbox connection details
        path: Directory path to create (e.g., "/workspace/myproject/src")

    Returns:
        Directory info

    Example:
        file_mkdir(vm_url, "/workspace/project/src")
        file_write(vm_url, "/workspace/project/src/main.py", "print('Hello')")
    """
    body: Dict[str, Any] = {"path": path}
    return _vm_request(vm_url, "POST", "/files/mkdir", auth_token=auth_token, json=body)


@mcp.tool()
def get_system_metrics(vm_url: str, auth_token: Optional[str] = None) -> dict:
    """
    GET /system — Get sandbox system metrics.

    Retrieve CPU, memory, and disk usage metrics for the sandbox.

    Args:
        vm_url: VM URL from sandbox connection details

    Returns:
        System metrics including CPU usage, memory usage, disk usage, uptime

    Example:
        metrics = get_system_metrics(vm_url)
        print(f"CPU: {metrics['cpu_percent']}%")
        print(f"Memory: {metrics['memory_percent']}%")
    """
    return _vm_request(vm_url, "GET", "/system", auth_token=auth_token)


@mcp.tool()
def env_get(vm_url: str, auth_token: Optional[str] = None) -> dict:
    """
    GET /env — Get all global environment variables.

    Retrieve all environment variables set in the sandbox. Sensitive values
    (containing KEY, SECRET, PASSWORD, TOKEN) are masked for security.

    Args:
        vm_url: VM URL from sandbox connection details

    Returns:
        Environment variables dict with masked sensitive values

    Example:
        env_vars = env_get(vm_url)
        print(env_vars["env_vars"])  # {"DATABASE_URL": "postgres://...", "API_KEY": "***MASKED***"}
    """
    return _vm_request(vm_url, "GET", "/env", auth_token=auth_token)


@mcp.tool()
def env_set(
    vm_url: str,
    env_vars: Dict[str, str],
    merge: bool = True,
    auth_token: Optional[str] = None,
) -> dict:
    """
    PUT/PATCH /env — Set or merge environment variables.

    Set environment variables in the sandbox. Use merge=True to add/update without
    clearing existing vars, or merge=False to replace all vars.

    Args:
        vm_url: VM URL from sandbox connection details
        env_vars: Dictionary of environment variables to set
        merge: If True, merge with existing vars (PATCH). If False, replace all (PUT). Default: True

    Returns:
        Empty response on success

    WORKFLOW: Set env vars before running code that needs them
        1. env_set(vm_url, {"API_KEY": "sk-123", "DATABASE_URL": "postgres://..."})
        2. execute_code(vm_url, "import os; print(os.getenv('API_KEY'))")

    Example:
        # Merge new vars with existing
        env_set(vm_url, {"DEBUG": "true", "API_KEY": "sk-123"}, merge=True)

        # Replace all vars
        env_set(vm_url, {"ENVIRONMENT": "production"}, merge=False)
    """
    method = "PATCH" if merge else "PUT"
    body: Dict[str, Any] = {"env_vars": env_vars}
    return _vm_request(vm_url, method, "/env", auth_token=auth_token, json=body)


@mcp.tool()
def env_clear(vm_url: str, auth_token: Optional[str] = None) -> dict:
    """
    DELETE /env — Clear all global environment variables.

    Remove all environment variables from the sandbox.

    Args:
        vm_url: VM URL from sandbox connection details

    Returns:
        Empty response on success

    Example:
        env_clear(vm_url)  # All env vars removed
    """
    return _vm_request(vm_url, "DELETE", "/env", auth_token=auth_token)


@mcp.tool()
def cache_clear(vm_url: str, auth_token: Optional[str] = None) -> dict:
    """
    POST /cache/clear — Clear execution cache.

    Clear all cached execution results to free memory or force re-execution.

    Args:
        vm_url: VM URL from sandbox connection details

    Returns:
        Confirmation with success status

    Example:
        cache_clear(vm_url)  # Clear all cached results
    """
    return _vm_request(vm_url, "POST", "/cache/clear", auth_token=auth_token)


@mcp.tool()
def cache_stats(vm_url: str, auth_token: Optional[str] = None) -> dict:
    """
    GET /cache/stats — Get execution cache statistics.

    Get cache statistics including total cached items and hit rate.

    Args:
        vm_url: VM URL from sandbox connection details

    Returns:
        Cache stats with total_cached count and hit_rate percentage

    Example:
        stats = cache_stats(vm_url)
        print(f"Cache hit rate: {stats['hit_rate']}%")
        print(f"Total cached: {stats['total_cached']}")
    """
    return _vm_request(vm_url, "GET", "/cache/stats", auth_token=auth_token)


# ============================================================================
# ISOLATED CODE EXECUTION - PRIMARY CODE EXECUTION METHOD
# ============================================================================
# This is the RECOMMENDED way to execute code: fast, isolated, ephemeral sandboxes


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
        🚀 FAST ISOLATED CODE EXECUTION - Create ephemeral sandbox, execute code, return output.

        This is the PRIMARY method for executing code in isolated cloud containers.
        Creates a sandbox in ~0.1ms, executes your code, returns output, then auto-destroys.

        Perfect for:
        - Quick code execution (Python, JavaScript, Bash, Go)
        - Data analysis and visualization
        - Package testing
        - Code validation
        - Any isolated computation

        Args:
            code: Code to execute
            language: 'python', 'javascript', 'bash', or 'go' (default: python)
            timeout: Execution timeout in seconds (default: 30, max: 300)
            env: Optional environment variables for the execution
            template_name: Template name to use (default: "code-interpreter")
                           Use list_templates() to find other templates
            region: Optional region (e.g., 'us-east', 'eu-west')

        Returns:
            Execution result with:
            - stdout: Standard output from code execution
            - stderr: Standard error (if any)
            - exit_code: Exit code (0 = success)
            - execution_time: Time taken in seconds
            - sandbox_id: Sandbox ID (auto-destroys after timeout)

        Examples:
            # Python data analysis
            execute_code_isolated('''
    import pandas as pd
    data = {'a': [1,2,3], 'b': [4,5,6]}
    df = pd.DataFrame(data)
    print(df.describe())
            ''')

            # JavaScript computation
            execute_code_isolated(
                code="console.log([1,2,3].map(x => x * 2))",
                language="javascript"
            )

            # Bash commands
            execute_code_isolated(
                code="df -h && free -m",
                language="bash"
            )

        Workflow:
            1. Creates ephemeral sandbox (0.1ms startup)
            2. Executes code in isolated container
            3. Returns output
            4. Auto-destroys after timeout (default: 600s)

        Note: For persistent sandboxes with multiple operations, use create_sandbox()
        followed by execute_code() instead.
    """
    try:
        # Step 1: Resolve template name to ID
        template = get_template(template_name)
        if "error" in template or "status_code" in template:
            return {
                "error": "Failed to resolve template",
                "details": template,
                "stdout": "",
                "stderr": f"Template '{template_name}' not found or unavailable",
                "exit_code": 1,
            }

        template_id = template.get("id")
        if not template_id:
            return {
                "error": "Template ID missing",
                "details": template,
                "stdout": "",
                "stderr": f"Template '{template_name}' does not have an ID",
                "exit_code": 1,
            }

        # Step 2: Create ephemeral sandbox with resolved template
        sandbox = create_sandbox(
            template_id=template_id,
            region=region,
            timeout_seconds=600,  # Auto-destroy after 10 minutes
            internet_access=True,
        )

        if "error" in sandbox or "status_code" in sandbox:
            return {
                "error": "Failed to create sandbox",
                "details": sandbox,
                "stdout": "",
                "stderr": f"Sandbox creation failed: {sandbox.get('error', 'Unknown error')}",
                "exit_code": 1,
            }

        # Step 3: Extract credentials
        vm_url = sandbox.get("direct_url")
        auth_token = sandbox.get("auth_token")
        sandbox_id = sandbox.get("id")

        if not vm_url or not auth_token:
            return {
                "error": "Missing sandbox credentials",
                "details": sandbox,
                "stdout": "",
                "stderr": "Failed to extract vm_url or auth_token from sandbox",
                "exit_code": 1,
            }

        # Step 4: Wait for VM to be fully ready (auth initialization)
        # The VM needs a few seconds to fully initialize after creation
        time.sleep(3)

        # Step 5: Execute code in sandbox
        result = execute_code(
            vm_url=vm_url,
            code=code,
            language=language,
            timeout=timeout,
            env=env,
            auth_token=auth_token,
        )

        # Step 6: Enhance result with sandbox info
        if isinstance(result, dict):
            result["sandbox_id"] = sandbox_id
            result["_note"] = (
                f"Sandbox {sandbox_id} will auto-destroy after 10 minutes. Use delete_sandbox('{sandbox_id}') to clean up earlier."
            )

        return result

    except Exception as e:
        return {
            "error": "Code execution failed",
            "exception": str(e),
            "stdout": "",
            "stderr": f"Exception during execution: {str(e)}",
            "exit_code": 1,
        }


# ============================================================================
# MCP PROMPTS - Reusable templates for common workflows
# ============================================================================


@mcp.prompt()
def quick_code_execution():
    """
    🚀 Quick Code Execution Guide

    Use this template when you need to execute code in an isolated environment.
    """
    return """You have access to HOPX Sandbox API for isolated code execution.

PRIMARY METHOD: execute_code_isolated()
This creates an ephemeral sandbox (0.1ms startup), executes code, and returns output.

USE CASES:
✓ Data analysis with pandas/numpy
✓ Code testing and validation
✓ Package installation and testing
✓ Math/scientific computations
✓ Quick scripts (Python/JS/Bash/Go)

WORKFLOW:
result = execute_code_isolated(
    code="import pandas as pd; print(pd.DataFrame({'a': [1,2,3]}))",
    language="python",
    timeout=30,
    env={"API_KEY": "optional-key"}
)

LANGUAGES SUPPORTED:
• python (default) - Full Python 3.x with common packages
• javascript - Node.js runtime
• bash - Shell commands
• go - Go compilation and execution

FEATURES:
• Isolated containers (secure)
• Internet access enabled
• Auto-cleanup (10min timeout)
• Fast startup (~0.1ms)
• Concurrent execution supported

TIPS:
1. Use execute_code_isolated() for one-off code execution
2. Use create_sandbox() → execute_code() for multiple operations
3. Install packages: execute_code_isolated("pip install numpy pandas")
4. Capture output: All stdout/stderr captured in result

EXAMPLE - Data Analysis:
execute_code_isolated('''
import pandas as pd
import matplotlib.pyplot as plt

# Load and analyze data
data = {"year": [2020, 2021, 2022], "revenue": [100, 150, 200]}
df = pd.DataFrame(data)
print(df.describe())
print(f"Growth: {df['revenue'].pct_change().mean()*100:.1f}%")
''')

EXAMPLE - API Testing:
execute_code_isolated('''
import requests
response = requests.get("https://api.github.com")
print(f"Status: {response.status_code}")
print(response.json().keys())
''', env={"GITHUB_TOKEN": "ghp_xxx"})

Remember: Sandboxes auto-destroy after 10 minutes. For long-running tasks,
use create_sandbox() directly and manage lifecycle manually.
"""


# ---- Optional: generic passthrough for future endpoints ----
@mcp.tool()
def call_api(
    method: str,
    path: str,
    query: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
    auth_token: Optional[str] = None,
) -> dict:
    """
    Generic caller for HOPX API. Example: method='GET', path='/v1/sandboxes', query={'limit':10}

    NOTE: For VM Agent calls, use the specific execute_*, run_command, file_* tools instead.
    """
    m = method.upper()
    r = _client.request(m, path, params=query, json=body, headers=_auth_headers())
    return _handle(r)


def main():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
