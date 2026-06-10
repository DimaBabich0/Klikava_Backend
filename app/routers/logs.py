from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from pathlib import Path
import re
from datetime import datetime
from typing import Optional, List

from app.database import get_db
from app.services.access_manager import AccessManager
from app.services.logger import setup_logger
from app.api.responses.response_rest import ResponseRest

router = APIRouter(tags=["logs"])
response = ResponseRest()
logger = setup_logger(__name__)

LOGS_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Request Logs</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
    <style>
        body { background-color: #f0f2f5; font-family: 'Segoe UI', sans-serif; }

        .sidebar {
            min-height: 100vh;
            background: #1a1d23;
            width: 260px;
            flex-shrink: 0;
            display: flex;
            flex-direction: column;
        }
        .sidebar-brand {
            padding: 1.5rem 1.25rem 1rem;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }
        .sidebar-brand h5 { color: #fff; font-weight: 700; margin: 0; font-size: 1rem; }
        .sidebar-brand p  { color: rgba(255,255,255,0.4); font-size: 0.75rem; margin: 0.25rem 0 0; }

        .sidebar-section-title {
            color: rgba(255,255,255,0.35);
            font-size: 0.65rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            padding: 1rem 1.25rem 0.4rem;
        }

        .file-list { list-style: none; padding: 0 0.5rem; margin: 0; overflow-y: auto; flex: 1; }
        .file-list li a {
            display: flex; align-items: center; gap: 0.6rem;
            padding: 0.5rem 0.75rem; border-radius: 6px;
            color: rgba(255,255,255,0.65); text-decoration: none;
            font-size: 0.85rem; transition: background 0.15s, color 0.15s;
        }
        .file-list li a:hover  { background: rgba(255,255,255,0.07); color: #fff; }
        .file-list li a.active { background: #4f6ef7; color: #fff; font-weight: 600; }
        .file-list li a .badge-dot {
            width: 6px; height: 6px; border-radius: 50%;
            background: rgba(255,255,255,0.25); flex-shrink: 0;
        }
        .file-list li a.active .badge-dot { background: rgba(255,255,255,0.7); }

        .main-content { flex: 1; overflow: hidden; display: flex; flex-direction: column; }

        .topbar {
            background: #fff; border-bottom: 1px solid #e5e7eb;
            padding: 0.875rem 1.5rem; display: flex; align-items: center; gap: 1rem; flex-shrink: 0;
        }
        .topbar h4    { margin: 0; font-size: 1rem; font-weight: 700; color: #111; }
        .topbar .selected-date {
            font-size: 0.8rem; color: #6b7280;
            background: #f3f4f6; padding: 0.2rem 0.6rem; border-radius: 20px;
        }

        .stat-card { background: #fff; border-radius: 10px; padding: 1rem 1.25rem; border: 1px solid #e5e7eb; }
        .stat-card .stat-value { font-size: 1.6rem; font-weight: 800; color: #111; line-height: 1; }
        .stat-card .stat-label { font-size: 0.75rem; color: #9ca3af; margin-top: 0.3rem; text-transform: uppercase; letter-spacing: 0.05em; }
        .stat-card .stat-icon  { width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1rem; flex-shrink: 0; }

        .filters-bar { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 1rem 1.25rem; }

        .table-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; overflow: hidden; flex: 1; }

        .table thead th {
            background: #f9fafb; font-size: 0.72rem; font-weight: 700;
            text-transform: uppercase; letter-spacing: 0.06em; color: #6b7280;
            border-bottom: 1px solid #e5e7eb; padding: 0.75rem 1rem; white-space: nowrap;
        }
        .table tbody td { padding: 0.65rem 1rem; font-size: 0.85rem; color: #374151; vertical-align: middle; border-bottom: 1px solid #f3f4f6; }
        .table tbody tr:last-child td { border-bottom: none; }
        .table tbody tr:hover td { background: #f9fafb; }

        .badge-method { font-size: 0.7rem; font-weight: 700; padding: 0.25em 0.55em; border-radius: 4px; letter-spacing: 0.03em; }
        .method-get    { background: #dbeafe; color: #1d4ed8; }
        .method-post   { background: #fef3c7; color: #92400e; }
        .method-put    { background: #ede9fe; color: #5b21b6; }
        .method-delete { background: #fee2e2; color: #991b1b; }
        .method-patch  { background: #d1fae5; color: #065f46; }

        .badge-status { font-size: 0.75rem; font-weight: 600; padding: 0.25em 0.6em; border-radius: 4px; }
        .status-2xx { background: #d1fae5; color: #065f46; }
        .status-3xx { background: #dbeafe; color: #1d4ed8; }
        .status-4xx { background: #fef3c7; color: #92400e; }
        .status-5xx { background: #fee2e2; color: #991b1b; }

        .time-slow   { color: #dc2626; font-weight: 600; }
        .time-normal { color: #16a34a; }

        .no-data-state    { padding: 3rem; text-align: center; color: #9ca3af; }
        .spinner-overlay  { padding: 3rem; text-align: center; }

        ::-webkit-scrollbar { width: 5px; height: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.15); border-radius: 10px; }
    </style>
</head>
<body>
<div class="d-flex" style="min-height:100vh;">

    <!-- Sidebar -->
    <aside class="sidebar">
        <div class="sidebar-brand">
            <h5><i class="bi bi-journal-text me-2"></i>Request Logs</h5>
            <p>Marketplace API</p>
        </div>
        <div class="sidebar-section-title">Log Files</div>
        <ul class="file-list" id="fileList">
            <li><a href="#"><i class="bi bi-hourglass-split me-1"></i> Loading...</a></li>
        </ul>
    </aside>

    <!-- Main -->
    <div class="main-content">
        <div class="topbar">
            <h4><i class="bi bi-activity me-2 text-primary"></i>Dashboard</h4>
            <span class="selected-date" id="selectedDateLabel">No file selected</span>
            <div class="ms-auto">
                <button class="btn btn-sm btn-outline-secondary" onclick="loadFileLogs()">
                    <i class="bi bi-arrow-clockwise me-1"></i>Refresh
                </button>
            </div>
        </div>

        <div class="p-3 d-flex flex-column gap-3" style="overflow-y:auto; flex:1;">

            <!-- Stats -->
            <div class="row g-3">
                <div class="col-6 col-xl-3">
                    <div class="stat-card d-flex align-items-center gap-3">
                        <div class="stat-icon bg-primary bg-opacity-10 text-primary"><i class="bi bi-arrow-left-right"></i></div>
                        <div><div class="stat-value" id="statTotal">—</div><div class="stat-label">Requests</div></div>
                    </div>
                </div>
                <div class="col-6 col-xl-3">
                    <div class="stat-card d-flex align-items-center gap-3">
                        <div class="stat-icon bg-success bg-opacity-10 text-success"><i class="bi bi-speedometer2"></i></div>
                        <div><div class="stat-value" id="statAvg">—</div><div class="stat-label">Avg Time</div></div>
                    </div>
                </div>
                <div class="col-6 col-xl-3">
                    <div class="stat-card d-flex align-items-center gap-3">
                        <div class="stat-icon bg-warning bg-opacity-10 text-warning"><i class="bi bi-stopwatch"></i></div>
                        <div><div class="stat-value" id="statMax">—</div><div class="stat-label">Max Time</div></div>
                    </div>
                </div>
                <div class="col-6 col-xl-3">
                    <div class="stat-card d-flex align-items-center gap-3">
                        <div class="stat-icon bg-danger bg-opacity-10 text-danger"><i class="bi bi-exclamation-triangle"></i></div>
                        <div><div class="stat-value" id="statErrors">—</div><div class="stat-label">Errors</div></div>
                    </div>
                </div>
            </div>

            <!-- Filters -->
            <div class="filters-bar">
                <div class="row g-2 align-items-end">
                    <div class="col-6 col-md-2">
                        <label class="form-label fw-semibold" style="font-size:.8rem;">Status</label>
                        <select class="form-select form-select-sm" id="statusFilter">
                            <option value="">All</option>
                            <option value="2">2xx</option>
                            <option value="3">3xx</option>
                            <option value="4">4xx</option>
                            <option value="5">5xx</option>
                        </select>
                    </div>
                    <div class="col-6 col-md-2">
                        <label class="form-label fw-semibold" style="font-size:.8rem;">Method</label>
                        <select class="form-select form-select-sm" id="methodFilter">
                            <option value="">All</option>
                            <option>GET</option><option>POST</option>
                            <option>PUT</option><option>DELETE</option><option>PATCH</option>
                        </select>
                    </div>
                    <div class="col-12 col-md-3">
                        <label class="form-label fw-semibold" style="font-size:.8rem;">Path</label>
                        <input type="text" class="form-control form-control-sm" id="pathFilter" placeholder="/api/...">
                    </div>
                    <div class="col-6 col-md-2">
                        <label class="form-label fw-semibold" style="font-size:.8rem;">Min Time (s)</label>
                        <input type="number" class="form-control form-control-sm" id="timeFilter" min="0" step="0.1" placeholder="0">
                    </div>
                    <div class="col-6 col-md-1">
                        <label class="form-label fw-semibold" style="font-size:.8rem;">Limit</label>
                        <input type="number" class="form-control form-control-sm" id="limitFilter" value="100" min="1" max="500">
                    </div>
                    <div class="col-12 col-md-2 d-flex gap-2">
                        <button class="btn btn-sm btn-primary w-100" onclick="applyFilters()">
                            <i class="bi bi-funnel me-1"></i>Apply
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="resetFilters()">
                            <i class="bi bi-x-lg"></i>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Table -->
            <div class="table-card">
                <div id="spinnerContainer" class="spinner-overlay" style="display:none;">
                    <div class="spinner-border text-primary" role="status"></div>
                    <p class="mt-2 text-muted small">Loading logs...</p>
                </div>
                <div id="noDataState" class="no-data-state">
                    <i class="bi bi-folder2-open" style="font-size:2rem;"></i>
                    <p class="mt-2 mb-0">Select a log file from the sidebar</p>
                </div>
                <div id="tableWrapper" style="display:none; overflow-x:auto;">
                    <table class="table table-hover mb-0">
                        <thead>
                            <tr>
                                <th>Timestamp</th><th>Client</th><th>Method</th>
                                <th>Path</th><th>Status</th><th>Time (ms)</th>
                            </tr>
                        </thead>
                        <tbody id="logsTableBody"></tbody>
                    </table>
                </div>
            </div>

        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script>
    let logCache  = { entries: [], stats: {} };
    let selectedDate = null;

    async function loadFileList() {
        try {
            const data = await fetch('/logs/api/files').then(r => r.json());
            const list = document.getElementById('fileList');
            list.innerHTML = '';

            if (!data.files || !data.files.length) {
                list.innerHTML = '<li><span class="px-3 text-secondary small">No log files found</span></li>';
                return;
            }

            data.files.forEach((file, idx) => {
                const li = document.createElement('li');
                const a  = document.createElement('a');
                a.href = '#';
                a.dataset.date = file.date;
                a.innerHTML = `
                    <span class="badge-dot"></span>
                    <span class="flex-grow-1">${file.label}</span>
                    ${file.is_today ? '<span class="badge bg-primary bg-opacity-25 text-primary" style="font-size:.65rem;">today</span>' : ''}
                `;
                a.addEventListener('click', e => {
                    e.preventDefault();
                    document.querySelectorAll('.file-list a').forEach(el => el.classList.remove('active'));
                    a.classList.add('active');
                    selectedDate = file.date;
                    document.getElementById('selectedDateLabel').textContent = file.label;
                    loadFileLogs();
                });
                li.appendChild(a);
                list.appendChild(li);

                if (file.is_today || (idx === 0 && !data.files.some(f => f.is_today))) {
                    a.click();
                }
            });
        } catch (err) { console.error('Failed to load file list', err); }
    }

    async function loadFileLogs() {
        if (!selectedDate) return;
        document.getElementById('spinnerContainer').style.display = 'block';
        document.getElementById('tableWrapper').style.display     = 'none';
        document.getElementById('noDataState').style.display      = 'none';

        const limit = document.getElementById('limitFilter').value || 100;
        try {
            const data = await fetch(`/logs/api/data?date=${selectedDate}&limit=${limit}`).then(r => r.json());
            logCache.entries = data.entries || [];
            logCache.stats   = data.stats   || {};
            renderStats();
            renderLogs(logCache.entries);
        } catch (err) { console.error('Error loading logs:', err); }
        finally { document.getElementById('spinnerContainer').style.display = 'none'; }
    }

    function applyFilters() {
        const sF = document.getElementById('statusFilter').value;
        const mF = document.getElementById('methodFilter').value;
        const pF = document.getElementById('pathFilter').value.toLowerCase();
        const tF = parseFloat(document.getElementById('timeFilter').value) || 0;

        renderLogs(logCache.entries.filter(e => {
            if (sF && !e.status.toString().startsWith(sF)) return false;
            if (mF && e.method !== mF) return false;
            if (pF && !e.path.toLowerCase().includes(pF)) return false;
            if (e.time < tF) return false;
            return true;
        }));
    }

    function resetFilters() {
        ['statusFilter','methodFilter','pathFilter','timeFilter'].forEach(id => document.getElementById(id).value = '');
        document.getElementById('limitFilter').value = '100';
        renderLogs(logCache.entries);
    }

    function renderStats() {
        const s = logCache.stats;
        document.getElementById('statTotal').textContent  = s.total_requests || 0;
        document.getElementById('statAvg').textContent    = ((s.avg_time || 0) * 1000).toFixed(0) + 'ms';
        document.getElementById('statMax').textContent    = ((s.max_time || 0) * 1000).toFixed(0) + 'ms';
        document.getElementById('statErrors').textContent = s.errors || 0;
    }

    function renderLogs(entries) {
        const wrapper = document.getElementById('tableWrapper');
        const noData  = document.getElementById('noDataState');

        if (!entries || !entries.length) {
            wrapper.style.display = 'none';
            noData.style.display  = 'block';
            noData.innerHTML = '<i class="bi bi-search" style="font-size:2rem;"></i><p class="mt-2 mb-0">No entries match the current filters</p>';
            return;
        }

        document.getElementById('logsTableBody').innerHTML = entries.map(e => {
            const mClass = 'method-' + e.method.toLowerCase();
            const sClass = e.status < 300 ? 'status-2xx' : e.status < 400 ? 'status-3xx' : e.status < 500 ? 'status-4xx' : 'status-5xx';
            return `
            <tr>
                <td class="text-muted" style="font-size:.8rem;white-space:nowrap;">${e.timestamp}</td>
                <td style="font-size:.8rem;">${e.client}</td>
                <td><span class="badge-method ${mClass}">${e.method}</span></td>
                <td style="max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${e.path}">${e.path}</td>
                <td><span class="badge-status ${sClass}">${e.status} ${e.status_text}</span></td>
                <td><span class="${e.time > 1 ? 'time-slow' : 'time-normal'}">${(e.time * 1000).toFixed(0)}</span></td>
            </tr>`;
        }).join('');

        wrapper.style.display = 'block';
        noData.style.display  = 'none';
    }

    loadFileList();
</script>
</body>
</html>
"""


def parse_log_line(line: str) -> Optional[dict]:
  pattern = (
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+\|\s+(\w+)\s+\|\s+(\w+)\s+\|"
    r"\s+(.+?)\s+-\s+(\w+)\s+(.+?)\s+-\s+Status:\s+(\d{3})\s+(.+?)\s+-\s+Time:\s+([\d.]+)s"
  )
  match = re.match(pattern, line)
  if not match:
    return None
  timestamp, level, logger_name, client, method, path, status, status_text, time_taken = match.groups()
  return {
    "timestamp": timestamp,
    "level": level,
    "client": client,
    "method": method,
    "path": path,
    "status": int(status),
    "status_text": status_text,
    "time": float(time_taken),
  }


def get_log_files() -> List[dict]:
  logs_dir = Path("logs")
  if not logs_dir.exists():
    return []
  today = datetime.now().strftime("%Y-%m-%d")
  files = []
  for f in sorted(logs_dir.glob("requests.*.log"), reverse=True):
    match = re.match(r"requests\.(\d{4}-\d{2}-\d{2})\.log$", f.name)
    if not match:
      continue
    date_str = match.group(1)
    files.append({
      "filename": f.name,
      "date": date_str,
      "label": date_str,
      "is_today": date_str == today,
    })
  return files


def resolve_log_file(date: Optional[str]) -> Optional[Path]:
  logs_dir = Path("logs")
  if date:
    candidate = logs_dir / f"requests.{date}.log"
    return candidate if candidate.exists() else None
  today = datetime.now().strftime("%Y-%m-%d")
  return logs_dir / f"requests.{today}.log"


def is_admin(request: Request) -> bool:
  if not hasattr(request.state, "user"):
    return False
  user_data = request.state.user
  roles = user_data.get("roles", [])
  return "ADMIN" in roles or any(
      role.get("name") == "ADMIN" for role in roles if isinstance(role, dict)
  )


@router.get("/logs", include_in_schema=False)
async def logs_page(request: Request):
  if not is_admin(request):
    raise HTTPException(status_code=403, detail="Only admins can access logs")
  from fastapi.responses import HTMLResponse
  return HTMLResponse(content=LOGS_HTML_TEMPLATE)


@router.get("/logs/api/files")
async def get_log_file_list(request: Request):
  if not is_admin(request):
    raise HTTPException(status_code=403, detail="Only admins can access logs")
  return {"files": get_log_files()}


@router.get("/logs/api/data")
async def get_logs_data(
  request: Request,
  date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
  status: Optional[int] = Query(None),
  method: Optional[str] = Query(None),
  path: Optional[str] = Query(None),
  min_time: float = Query(0.0),
  limit: int = Query(100, ge=1, le=500),
):
  if not is_admin(request):
    raise HTTPException(status_code=403, detail="Only admins can access logs")

  empty = {"entries": [], "stats": {"total_requests": 0,
                                    "avg_time": 0, "max_time": 0, "errors": 0}}

  log_file = resolve_log_file(date)
  if not log_file or not log_file.exists():
    return empty

  entries = []
  with open(log_file, "r", encoding="utf-8") as f:
    for line in f:
      entry = parse_log_line(line.strip())
      if not entry:
        continue
      if status and entry["status"] != status:
        continue
      if method and entry["method"] != method:
        continue
      if path and path not in entry["path"]:
        continue
      if entry["time"] < min_time:
        continue
      entries.append(entry)

  entries = entries[-limit:]

  if entries:
    error_count = sum(1 for e in entries if e["status"] >= 400)
    avg_time = sum(e["time"] for e in entries) / len(entries)
    max_time = max(e["time"] for e in entries)
  else:
    error_count = avg_time = max_time = 0

  return {
    "entries": entries,
    "stats": {
      "total_requests": len(entries),
      "avg_time": avg_time,
      "max_time": max_time,
      "errors": error_count,
    },
  }
