"""
run_platform.py — One-Click Concurrent Platform Launcher.
Starts both the FastAPI REST Backend (Port 8000) and Modern Frontend (Port 3000).
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "frontend"


def main():
    print("=" * 80)
    print("🚀 Starting Udyam Saathi (उद्यम साथी) — Full Platform Launcher")
    print("=" * 80)
    print(f"Project Directory: {ROOT_DIR}")
    print(f"Frontend Directory: {FRONTEND_DIR}")
    print("\n1. Starting FastAPI REST Backend on http://127.0.0.1:8000 ...")

    backend_env = os.environ.copy()
    backend_env["PYTHONPATH"] = str(ROOT_DIR) + os.pathsep + str(ROOT_DIR / "backend")
    backend_env["PYTHONIOENCODING"] = "utf-8"

    backend_cmd = [
        sys.executable, "-m", "uvicorn", "backend.app.main:app",
        "--host", "127.0.0.1", "--port", "8000", "--reload"
    ]

    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=str(ROOT_DIR),
        env=backend_env,
    )

    print("2. Starting React + Vite Frontend Web Server on http://127.0.0.1:3000 ...")
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    frontend_cmd = [npm_cmd, "run", "dev"]

    try:
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=str(FRONTEND_DIR),
            shell=True if sys.platform == "win32" else False,
        )
    except Exception:
        frontend_cmd_fallback = [
            sys.executable, "-m", "http.server", "3000",
            "--directory", str(FRONTEND_DIR / "dist" if (FRONTEND_DIR / "dist").exists() else FRONTEND_DIR),
        ]
        frontend_proc = subprocess.Popen(
            frontend_cmd_fallback,
            cwd=str(ROOT_DIR),
        )

    time.sleep(2.0)

    print("\n" + "=" * 80)
    print("✨ PLATFORM READY AND RUNNING!")
    print("=" * 80)
    print("🌐 Frontend Web App:     http://127.0.0.1:3000")
    print("🔌 FastAPI REST API:     http://127.0.0.1:8000")
    print("📚 Interactive API Docs: http://127.0.0.1:8000/docs")
    print("❤️ System Health Check:  http://127.0.0.1:8000/api/v2/health")
    print("\nPress Ctrl+C to terminate all services.")
    print("=" * 80)

    try:
        # Open web browser automatically
        webbrowser.open("http://127.0.0.1:3000")
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping services...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Udyam Saathi platform stopped cleanly.")


if __name__ == "__main__":
    main()
