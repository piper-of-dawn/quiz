import os
import platform
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def run(args):
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def main():
    app_url = os.environ.get("APP_URL")
    if not app_url:
        print("APP_URL must point to the deployed web app, for example https://quiz.example.com", file=sys.stderr)
        return 2
    (ROOT / "electron" / "app-url.json").write_text(
        '{\n  "url": "' + app_url.replace("\\", "\\\\").replace('"', '\\"') + '"\n}\n',
        encoding="utf-8",
    )

    npm = "npm.cmd" if platform.system() == "Windows" else "npm"
    if not (ROOT / "node_modules").exists():
        run([npm, "install"])

    system = platform.system()
    if system == "Linux":
        run([npm, "run", "build:linux"])
    elif system == "Darwin":
        run([npm, "run", "build:mac"])
    elif system == "Windows":
        run([npm, "run", "build:win"])
    else:
        print(f"Unsupported OS for Electron build: {system}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
