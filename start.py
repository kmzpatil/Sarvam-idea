#!/usr/bin/env python3
"""Single-entrypoint launcher for Signal Fusion Board."""

import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "frontend"
DIST_DIR = FRONTEND_DIR / "dist"

def main():
    print("=" * 60)
    print("  SIGNAL FUSION BOARD (सिग्नल फ्यूजन बोर्ड) — Live Launcher")
    print("=" * 60)

    # 1. Check/Build frontend if needed
    if not (DIST_DIR / "index.html").exists():
        print("[1/2] Building React frontend...")
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        try:
            subprocess.run([npm_cmd, "run", "build"], cwd=FRONTEND_DIR, check=True)
            print("✓ Frontend built successfully.")
        except Exception as e:
            print(f"Warning: Could not build frontend automatically ({e}). Serving backend API only.")
    else:
        print("[1/2] Compiled frontend bundle found at frontend/dist.")

    # 2. Launch FastAPI
    print("[2/2] Starting FastAPI Crisis Intelligence Server on http://127.0.0.1:8000 ...")
    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()
