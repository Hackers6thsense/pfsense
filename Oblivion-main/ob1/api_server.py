import threading
import time
import json
import os
import sys
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks, Request, HTTPException, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ob1 import scenario_runner
import asyncio

app = FastAPI(title="Oblivion Red-Team API")

# --- Token security setup ---
API_TOKEN = os.getenv("OBLIVION_API_TOKEN", "changeme")
if API_TOKEN == "changeme":
    print("[!] WARNING: Using default API token! Set OBLIVION_API_TOKEN to secure the API.", file=sys.stderr)

SECURITY = HTTPBearer(auto_error=False)

def get_current(cred: HTTPAuthorizationCredentials = Depends(SECURITY)):
    if not cred or cred.scheme.lower() != "bearer" or cred.credentials != API_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API token")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_obl = None

def init_oblivion_instance(oblivion):
    global _obl
    _obl = oblivion

def get_oblivion():
    global _obl
    if _obl is None:
        raise RuntimeError("Oblivion instance not set")
    return _obl

def _current_status(oblivion):
    return {
        "engagement_id": getattr(oblivion.policy.engagement, "engagement_id", "unknown"),
        "intelligence": getattr(oblivion, "intelligence", None),
        "location": getattr(oblivion, "current_location", None),
        "active_threads": sum(1 for t in oblivion.active_threads if t.is_alive()),
        "hosts_count": len(oblivion.assets.get_summary().get("hosts", [])),
        "services_count": len(oblivion.assets.get_summary().get("services", [])),
        "playbook": oblivion.attack_playbook,
        "dry_run": getattr(oblivion, "dry_run", False),
    }

@app.get("/status")
def get_status(oblivion=Depends(get_oblivion), _:str=Depends(get_current)):
    return _current_status(oblivion)

@app.get("/assets")
def get_assets(oblivion=Depends(get_oblivion), _:str=Depends(get_current)):
    return oblivion.assets.get_summary()

@app.post("/attack")
def launch_attack(data: dict, oblivion=Depends(get_oblivion), _:str=Depends(get_current)):
    technique_id = data.get("technique_id")
    params = data.get("params", {})
    if not technique_id:
        return JSONResponse({"launched": False, "error": "Missing technique_id"}, status_code=400)
    try:
        res = oblivion.simulate_attack_strategy(technique_id, **params)
        return {"launched": res is not False}
    except Exception as e:
        return JSONResponse({"launched": False, "error": str(e)}, status_code=500)

@app.post("/scenario")
def launch_scenario(data: dict, oblivion=Depends(get_oblivion), _:str=Depends(get_current)):
    steps = data.get("steps")
    if not isinstance(steps, list):
        return JSONResponse({"error": "Missing or invalid steps"}, status_code=400)
    def run_bg():
        scenario_runner.run_scenario(oblivion, None, steps=steps)
    thread = threading.Thread(target=run_bg, daemon=True)
    thread.start()
    return {"launched": True, "thread_id": id(thread)}

@app.post("/stop")
def stop_attacks(oblivion=Depends(get_oblivion), _:str=Depends(get_current)):
    oblivion.stop_all_attacks()
    return {"stopped": True}

@app.websocket("/logs")
async def logs_ws(websocket: WebSocket):
    # Check token query param
    token = websocket.query_params.get("token")
    if token != API_TOKEN:
        await websocket.close(code=4401)
        return
    await websocket.accept()
    obl = get_oblivion()
    log_path = getattr(obl.log_file, "name", None)
    if not log_path:
        await websocket.close()
        return
    last_size = 0
    try:
        while True:
            with open(log_path, "r", encoding="utf-8") as f:
                f.seek(last_size)
                lines = f.readlines()
                if lines:
                    for line in lines:
                        await websocket.send_text(line.rstrip())
                last_size = f.tell()
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return
    except Exception:
        await websocket.close()

@app.websocket("/ws/status")
async def ws_status(websocket: WebSocket):
    # Check token query param
    token = websocket.query_params.get("token")
    if token != API_TOKEN:
        await websocket.close(code=4401)
        return
    await websocket.accept()
    obl = get_oblivion()
    try:
        while True:
            status = _current_status(obl)
            await websocket.send_text(json.dumps(status))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return
    except Exception:
        await websocket.close()

@app.get("/dashboard")
def dashboard_html():
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Oblivion Dashboard</title>
        <meta charset="utf-8">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #181c20; color: #eee; margin: 0; padding: 0;}
        .container { max-width: 900px; margin: 0 auto; padding: 2rem; }
        h1, #topbar { text-align: center; color: #4fd; margin-bottom: 1rem;}
        table { width: 100%; border-collapse: collapse; margin-bottom: 1.5rem;}
        th, td { border: 1px solid #444; padding: 0.5rem 0.7rem; text-align: left; }
        th { background: #222; color: #6df; }
        .section { margin-bottom: 2rem; }
        #logtail { background: #111; color: #fc0; font-size: 0.98em; padding: 1rem; height: 300px; overflow-y: auto; border: 1px solid #333; }
        #dryrun { color: #fd4; font-weight: bold; font-size: 1.15em; padding: 0.3em 0;}
        #topbar { margin-bottom: 1em; }
        #stopbtn { background: #ff3c3c; color: white; border: none; border-radius: 4px; font-size: 1.1em; padding: 0.5em 1.2em; cursor: pointer; margin-right: 1em; }
        #stopbtn:active { background: #b00; }
        #footer { text-align: center; padding: 2em 0 0 0; color: #aaa; font-size: 0.97em;}
        </style>
    </head>
    <body>
    <div class="container">
        <div id="topbar">
            <button id="stopbtn">Stop All Attacks</button>
            <span id="dryrun"></span>
        </div>
        <h1>Oblivion Real-Time Dashboard</h1>
        <div class="section">
            <h2>Engagement Status</h2>
            <table>
                <tbody>
                    <tr><th>Engagement ID</th><td id="engagement_id">—</td></tr>
                    <tr><th>Intelligence</th><td id="intelligence">—</td></tr>
                    <tr><th>Location</th><td id="location">—</td></tr>
                    <tr><th>Active Threads</th><td id="active_threads">—</td></tr>
                    <tr><th>Hosts</th><td id="hosts_count">—</td></tr>
                    <tr><th>Services</th><td id="services_count">—</td></tr>
                </tbody>
            </table>
        </div>
        <div class="section">
            <h2>Playbook</h2>
            <table id="playbook">
                <thead>
                    <tr><th>Technique</th><th>Success</th><th>Failure</th><th>Attempts</th></tr>
                </thead>
                <tbody id="playbook_body">
                </tbody>
            </table>
            <canvas id="chart" width="420" height="210"></canvas>
        </div>
        <div class="section">
            <h2>Live Log Tail</h2>
            <pre id="logtail"></pre>
        </div>
        <div id="footer">
            <span>Keyboard shortcuts: <b>s</b> = stop all, <b>q</b> = quit (focus window first)</span>
        </div>
    </div>
    <script>
    // Helper to get token from ?token=... or prompt if not present
    function getToken() {
        const url = new URL(window.location.href);
        let token = url.searchParams.get('token');
        if (!token) {
            token = prompt("API Token:");
            if (token) {
                url.searchParams.set('token', token);
                window.location.href = url.toString();
                return null; // Will reload
            }
        }
        return token;
    }
    const apiToken = getToken();
    // Keyboard shortcuts (s, q) for Stop All, Quit
    document.addEventListener('keydown', function(event) {
        if (event.key === 's' || event.key === 'S') {
            stopAllAttacks();
        }
        if (event.key === 'q' || event.key === 'Q') {
            window.close();
        }
    });
    // Stop button handler
    function stopAllAttacks() {
        fetch('/stop', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + apiToken
            }
        }).then(r => r.json()).then(res => {
            if(res.stopped) alert('Attacks stopped.');
        });
    }
    if (apiToken) {
        document.getElementById('stopbtn').onclick = stopAllAttacks;
        const wsProto = (location.protocol === "https:" ? "wss://" : "ws://") + location.host;
        const wsStatus = new WebSocket(wsProto + "/ws/status?token=" + encodeURIComponent(apiToken));
        // Chart.js setup
        let chart = null;
        function updateChart(success, failure) {
            let ctx = document.getElementById('chart').getContext('2d');
            if (chart) chart.destroy();
            chart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: ['Success', 'Failure'],
                    datasets: [{
                        data: [success, failure],
                        backgroundColor: ['#42fd8c', '#fd4242'],
                    }]
                },
                options: {
                    plugins: {
                        legend: {
                            labels: { color: '#eee', font: { size: 15 } }
                        }
                    }
                }
            });
        }
        wsStatus.onmessage = function(event) {
            let s = JSON.parse(event.data);
            document.getElementById("engagement_id").innerText = s.engagement_id;
            document.getElementById("intelligence").innerText = s.intelligence;
            document.getElementById("location").innerText = s.location;
            document.getElementById("active_threads").innerText = s.active_threads;
            document.getElementById("hosts_count").innerText = s.hosts_count;
            document.getElementById("services_count").innerText = s.services_count;
            // Playbook
            let tbody = document.getElementById("playbook_body");
            tbody.innerHTML = "";
            let pb = s.playbook || {};
            let succ = 0, fail = 0;
            for (let k in pb) {
                let row = document.createElement("tr");
                let sc = pb[k].success||0, fl = pb[k].failure||0;
                row.innerHTML = `<td>${k}</td><td>${sc}</td><td>${fl}</td><td>${pb[k].attempts||0}</td>`;
                tbody.appendChild(row);
                succ += sc; fail += fl;
            }
            updateChart(succ, fail);
            // Dry-run banner
            document.getElementById("dryrun").innerText = s.dry_run ? "DRY-RUN is enabled: all attacks are simulated only." : "";
        };
        // Log tail
        const logLines = [];
        function updateLogTail() {
            let pre = document.getElementById("logtail");
            pre.innerText = logLines.slice(-50).join("\\n");
            pre.scrollTop = pre.scrollHeight;
        }
        const wsLog = new WebSocket(wsProto + "/logs?token=" + encodeURIComponent(apiToken));
        wsLog.onmessage = function(event) {
            logLines.push(event.data);
            updateLogTail();
        };
    }
    </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

# (Optional) static files mount for future assets
app.mount("/static", StaticFiles(directory="static", html=True), name="static")