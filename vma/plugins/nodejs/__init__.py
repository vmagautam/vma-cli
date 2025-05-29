import os
from vma.utils import run, log

def detect(path: str) -> bool:
    return os.path.exists(os.path.join(path, "package.json"))

def install(path: str, config: dict):
    log(f"[nodejs] npm install in {path}")
    run("npm install", cwd=path)

def build(path: str, config: dict):
    pkg = os.path.join(path, "package.json")
    if os.path.exists(pkg):
        import json
        with open(pkg) as f:
            data = json.load(f)
        if "build" in data.get("scripts", {}):
            log(f"[nodejs] npm run build in {path}")
            run("npm run build", cwd=path)

def start(path: str, config: dict):
    if os.path.exists(os.path.join(path, "ecosystem.config.js")):
        log(f"[nodejs] pm2 start ecosystem.config.js in {path}")
        run("pm2 start ecosystem.config.js", cwd=path)
    elif os.path.exists(os.path.join(path, "index.js")):
        log(f"[nodejs] pm2 start index.js in {path}")
        run("pm2 start index.js", cwd=path)
    else:
        log(f"[nodejs] No startable file found in {path}", level=1)

def stop(path: str, config: dict):
    log(f"[nodejs] pm2 stop all in {path}")
    run("pm2 stop all", cwd=path)

def logs(path: str, config: dict):
    log(f"[nodejs] pm2 logs in {path}")
    run("pm2 logs", cwd=path) 