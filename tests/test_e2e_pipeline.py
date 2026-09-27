import json
import os
import subprocess
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_INVOICES_PATH = os.path.join(BASE_DIR, "data", "seed", "sample_invoices.json")
ENV_PATH = os.path.join(BASE_DIR, ".env")


def get_bob_api_key():
    """Retrieve BOB_API_KEY from environment or .env file."""
    api_key = os.environ.get("BOB_API_KEY")
    if api_key and not api_key.startswith("your_"):
        return api_key
    if os.path.isfile(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("BOB_API_KEY="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val and not val.startswith("your_"):
                        return val
    return None





def test_bob_shell_orchestrator_cli_e2e():
    """Level 2 Conversational Orchestrator E2E Verification:
    Executes IBM Bob Shell non-interactively (`bob run --trust --format json`),
    verifying that Bob agent invokes the `customsguard` MCP tool on Langflow,
    and returns structured compliance findings.
    """
    bob_api_key = get_bob_api_key()
    if not bob_api_key:
        pytest.skip(
            "BOB_API_KEY is not set in environment or .env file. "
            "Set BOB_API_KEY to execute live IBM Bob Shell orchestrator CLI tests."
        )

    # Construct execution environment with Node and PNPM in PATH
    env = os.environ.copy()
    env["BOB_API_KEY"] = bob_api_key
    nvm_node_path = "/home/rafif/.nvm/versions/node/v24.21.0/bin"
    pnpm_path = "/home/rafif/.local/share/pnpm/bin"
    env["PATH"] = f"{nvm_node_path}:{pnpm_path}:{env.get('PATH', '')}"

    cmd = [
        "bob",
        "run",
        "--trust",
        "--max-turns", "4",
        "--format", "json",
        "Audit shipment SHP-2026-0042 using customsguard tool and state the compliance verdict."
    ]

    try:
        proc = subprocess.run(
            cmd,
            cwd=BASE_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=60
        )
    except FileNotFoundError:
        pytest.skip("bob command line tool is not installed on system PATH.")
    except subprocess.TimeoutExpired:
        pytest.fail("bob run execution timed out after 60 seconds.")

    assert proc.returncode == 0, f"bob run exited with error code {proc.returncode}: {proc.stderr}"

    # Parse newline-delimited JSON (NDJSON) output from bob run
    bob_result = None
    for line in proc.stdout.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
            if isinstance(parsed, dict):
                if parsed.get("type") == "result":
                    bob_result = parsed
                    break
                elif bob_result is None:
                    bob_result = parsed
        except json.JSONDecodeError:
            continue

    if not bob_result:
        pytest.fail(f"Failed to find valid JSON result in bob output: {proc.stdout}")

    assert bob_result.get("status") == "success"
    stats = bob_result.get("stats", {})
    assert stats.get("tool_calls", 0) >= 1, "Expected Bob to make at least 1 MCP tool call."

    last_msg = bob_result.get("last_message", "")
    assert any(token in last_msg for token in ["SHP-2026-0042", "NON_COMPLIANT", "8517", "detention"])
