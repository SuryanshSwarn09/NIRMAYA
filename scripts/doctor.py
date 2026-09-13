#!/usr/bin/env python3
"""NIRMAYA Environment & Dependency Diagnostic Health-Check (Doctor).

Validates toolchains, virtual environments, node modules, and configurations.
"""

import sys
import os
import shutil
import subprocess
from pathlib import Path

# ANSI color codes
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner():
    print(f"\n{BOLD}{BLUE}================================================================{RESET}")
    print(f"{BOLD}{BLUE}       NIRMAYA System Diagnostic & Pre-Flight Validator         {RESET}")
    print(f"{BOLD}{BLUE}================================================================{RESET}\n")


def check_python() -> bool:
    print(f"[{BOLD}Python Environment{RESET}]")
    version = sys.version_info
    print(f"  Version: {version.major}.{version.minor}.{version.micro}")
    if version.major == 3 and version.minor >= 11:
        print(f"  Status:  {GREEN}PASS (>= 3.11 compatible){RESET}")
        return True
    else:
        print(f"  Status:  {RED}FAIL (Requires Python >= 3.11){RESET}")
        return False


def check_node() -> bool:
    print(f"\n[{BOLD}Node.js & NPM Toolchain{RESET}]")
    node_path = shutil.which("node")
    if not node_path:
        print(f"  Node.js: {RED}NOT FOUND in PATH{RESET}")
        return False

    try:
        res = subprocess.run(["node", "-v"], capture_output=True, text=True, check=True)
        node_ver = res.stdout.strip()
        print(f"  Node.js: {node_ver} ({GREEN}PASS{RESET})")
        return True
    except Exception as e:
        print(f"  Node.js: {RED}Error checking version: {e}{RESET}")
        return False


def check_backend_env(root: Path) -> bool:
    print(f"\n[{BOLD}Backend Dependencies & Venv{RESET}]")
    backend_dir = root / "backend"
    venv_dir = backend_dir / ".venv"

    if not venv_dir.exists():
        print(f"  Venv:    {YELLOW}NOT FOUND at {venv_dir}{RESET}")
        print(f"  Action:  Run `py -3.12 -m venv backend/.venv` and install requirements.")
        return False

    print(f"  Venv:    {GREEN}FOUND ({venv_dir}){RESET}")

    # Check key packages
    packages = ["fastapi", "pydantic", "sqlalchemy", "alembic", "asyncpg", "pytest", "httpx"]
    missing = []
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"  Package: {pkg.ljust(12)} -> {GREEN}INSTALLED{RESET}")
        except ImportError:
            # Check if installed inside venv
            print(f"  Package: {pkg.ljust(12)} -> {YELLOW}CHECK VENV{RESET}")

    return True


def check_frontend_env(root: Path) -> bool:
    print(f"\n[{BOLD}Frontend Dependencies & Next.js{RESET}]")
    frontend_dir = root / "frontend"
    node_modules = frontend_dir / "node_modules"

    if node_modules.exists():
        print(f"  Modules: {GREEN}FOUND ({node_modules}){RESET}")
        return True
    else:
        print(f"  Modules: {YELLOW}MISSING ({node_modules}){RESET}")
        print(f"  Action:  Run `cd frontend && npm install`")
        return False


def check_config_files(root: Path):
    print(f"\n[{BOLD}Configuration & Secrets Check{RESET}]")
    configs = [
        ("Backend .env.example", root / "backend" / ".env.example"),
        ("Frontend .env.example", root / "frontend" / ".env.example"),
        ("Alembic Config", root / "backend" / "alembic.ini"),
        ("GitBook Docs YAML", root / "gitbook-docs.yaml"),
        ("GitBook Summary", root / "docs" / "SUMMARY.md"),
    ]

    for name, path in configs:
        if path.exists():
            print(f"  {name.ljust(25)} -> {GREEN}PRESENT{RESET}")
        else:
            print(f"  {name.ljust(25)} -> {RED}MISSING{RESET}")


def main():
    print_banner()
    root = Path(__file__).resolve().parent.parent

    p_ok = check_python()
    n_ok = check_node()
    b_ok = check_backend_env(root)
    f_ok = check_frontend_env(root)
    check_config_files(root)

    print(f"\n{BOLD}----------------------------------------------------------------{RESET}")
    if p_ok and n_ok and f_ok:
        print(f"{GREEN}{BOLD}[OK] NIRMAYA Pre-Flight Check PASSED! Ready for development.{RESET}\n")
        sys.exit(0)
    else:
        print(f"{YELLOW}{BOLD}⚠ Warning: Some items require attention. Review output above.{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
