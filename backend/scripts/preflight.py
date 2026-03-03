"""
Deployment preflight checks for NeGD backend.

Usage:
  cd backend
  ..\.venv\Scripts\python.exe scripts\preflight.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import httpx
from fastapi.testclient import TestClient
from dotenv import load_dotenv


def _print_result(ok: bool, label: str, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    suffix = f" - {detail}" if detail else ""
    print(f"[{status}] {label}{suffix}")


def _required_env() -> list[str]:
    return [
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "GROQ_API_KEY",
        "EMBEDDING_MODEL",
        "EMBEDDING_DIMENSION",
    ]


def check_env() -> bool:
    ok = True
    for key in _required_env():
        present = bool(os.getenv(key))
        _print_result(present, f"env:{key}")
        ok = ok and present
    return ok


def check_supabase(base_url: str, key: str) -> bool:
    ok = True
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    with httpx.Client(timeout=12.0) as client:
        try:
            table = client.get(f"{base_url}/rest/v1/reports", params={"select": "id", "limit": 1}, headers=headers)
            table_ok = table.status_code == 200
            _print_result(table_ok, "supabase:reports-table", f"HTTP {table.status_code}")
            ok = ok and table_ok
        except Exception as exc:  # noqa: BLE001
            _print_result(False, "supabase:reports-table", str(exc))
            ok = False

        try:
            dim = int(os.getenv("EMBEDDING_DIMENSION", "384"))
            payload: dict[str, Any] = {
                "query_embedding": [0.0] * dim,
                "filter_state": None,
                "filter_month": None,
                "filter_section": None,
                "match_count": 1,
            }
            rpc = client.post(f"{base_url}/rest/v1/rpc/match_chunks", json=payload, headers=headers)
            rpc_ok = rpc.status_code == 200
            _print_result(rpc_ok, "supabase:match_chunks-rpc", f"HTTP {rpc.status_code}")
            ok = ok and rpc_ok
        except Exception as exc:  # noqa: BLE001
            _print_result(False, "supabase:match_chunks-rpc", str(exc))
            ok = False
    return ok


def check_groq(api_key: str) -> bool:
    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
        ok = res.status_code == 200
        _print_result(ok, "groq:models", f"HTTP {res.status_code}")
        return ok
    except Exception as exc:  # noqa: BLE001
        _print_result(False, "groq:models", str(exc))
        return False


def check_local_api() -> bool:
    try:
        backend_dir = Path(__file__).resolve().parents[1]
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from app.main import app

        client = TestClient(app)
        health = client.get("/health")
        status = client.get("/api/system/status")
        health_ok = health.status_code == 200
        status_ok = status.status_code == 200
        _print_result(health_ok, "api:/health", f"HTTP {health.status_code}")
        _print_result(status_ok, "api:/api/system/status", f"HTTP {status.status_code}")
        return health_ok and status_ok
    except Exception as exc:  # noqa: BLE001
        _print_result(False, "api:import-or-self-check", str(exc))
        return False


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    load_dotenv(repo_root / ".env")

    print("NeGD Backend Preflight\n")
    env_ok = check_env()

    supabase_ok = False
    groq_ok = False
    if env_ok:
        supabase_ok = check_supabase(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
        groq_ok = check_groq(os.environ["GROQ_API_KEY"])

    api_ok = check_local_api()
    all_ok = env_ok and supabase_ok and groq_ok and api_ok

    print("\nSummary:")
    _print_result(all_ok, "overall")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
