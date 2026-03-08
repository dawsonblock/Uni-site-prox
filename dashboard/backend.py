from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import subprocess
import os
import psutil
from pathlib import Path
import yaml

app = FastAPI(title="USP Dashboard Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# State
proxy_process = None
USP_ROOT = Path(__file__).parent.parent.resolve()
API_MAPS_DIR = USP_ROOT / "api_maps"


@app.post("/api/proxy/stop")
async def stop_proxy():
    global proxy_process
    if proxy_process is not None and proxy_process.poll() is None:
        try:
            parent = psutil.Process(proxy_process.pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
            proxy_process = None
            return {"status": "stopped"}
        except psutil.NoSuchProcess:
            proxy_process = None
            pass
    return {"status": "not running"}


class DiscoverRequest(BaseModel):
    url: str
    site_name: str
    explore: bool = False


@app.post("/api/discover")
async def trigger_discover(req: DiscoverRequest):
    cmd = ["usp", "discover", req.url, "--site", req.site_name]
    if req.explore:
        cmd.append("--explore")

    try:
        # Run discovery sync for simplicity, capturing output
        result = subprocess.run(
            cmd, cwd=str(USP_ROOT), capture_output=True, text=True, check=True
        )
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Discovery failed: {e.stderr}")


@app.get("/api/specs")
async def list_specs():
    specs = []
    if API_MAPS_DIR.exists():
        for file in API_MAPS_DIR.glob("*.yaml"):
            try:
                with open(file, "r") as f:
                    content = yaml.safe_load(f)
                    specs.append(
                        {
                            "filename": file.name,
                            "site": content.get("site", "unknown"),
                            "base_url": content.get("base_url", "unknown"),
                            "operations": content.get("operations", {}),
                            "content": yaml.dump(content),
                        }
                    )
            except Exception:
                pass
    return {"specs": specs}


class SaveSpecRequest(BaseModel):
    content: str


@app.put("/api/specs/{filename}")
async def save_spec(filename: str, req: SaveSpecRequest):
    filepath = API_MAPS_DIR / filename
    if not filepath.exists() or ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid spec file")

    try:
        # Validate yaml parse
        yaml.safe_load(req.content)
        with open(filepath, "w") as f:
            f.write(req.content)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {str(e)}")


@app.delete("/api/specs/{filename}")
async def delete_spec(filename: str):
    filepath = API_MAPS_DIR / filename
    if not filepath.exists() or ".." in filename or "/" in filename:
        raise HTTPException(status_code=404, detail="Spec not found")
    try:
        filepath.unlink()
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/proxy/status")
async def proxy_status():
    global proxy_process
    is_running = False
    if proxy_process is not None:
        if proxy_process.poll() is None:
            is_running = True
        else:
            proxy_process = None
    return {"running": is_running}


@app.post("/api/proxy/start")
async def start_proxy():
    global proxy_process
    if proxy_process is not None and proxy_process.poll() is None:
        return {"status": "already running"}

    # Start proxy in background
    cmd = ["usp", "serve"]
    try:
        proxy_process = subprocess.Popen(
            cmd, cwd=str(USP_ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return {"status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Mount static frontend AFTER API routes
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
