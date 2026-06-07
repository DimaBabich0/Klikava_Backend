from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from pathlib import Path
import re
from typing import Optional, List

from app.database import get_db
from app.services.access_manager import AccessManager
from app.services.logger import setup_logger
from app.api.responses.response_rest import ResponseRest

router = APIRouter(tags=["logs"])
response = ResponseRest()
logger = setup_logger(__name__)

# HTML template for logs page
LOGS_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Request Logs - Marketplace API</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 0.95em;
            opacity: 0.9;
        }
        
        .controls {
            padding: 25px;
            background: #f8f9fa;
            border-bottom: 1px solid #e0e0e0;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            align-items: end;
        }
        
        .control-group {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        
        .control-group label {
            font-size: 0.85em;
            font-weight: 600;
            color: #333;
        }
        
        .control-group input,
        .control-group select {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 0.9em;
        }
        
        .control-group input:focus,
        .control-group select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .button-group {
            display: flex;
            gap: 10px;
        }
        
        button {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            font-size: 0.9em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-filter {
            background: #667eea;
            color: white;
        }
        
        .btn-filter:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        
        .btn-refresh {
            background: #28a745;
            color: white;
        }
        
        .btn-refresh:hover {
            background: #218838;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
        }
        
        .btn-reset {
            background: #6c757d;
            color: white;
        }
        
        .btn-reset:hover {
            background: #5a6268;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(108, 117, 125, 0.3);
        }
        
        .content {
            padding: 25px;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        
        .stat-card .value {
            font-size: 1.8em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-card .label {
            font-size: 0.85em;
            opacity: 0.9;
        }
        
        .logs-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9em;
        }
        
        .logs-table thead {
            background: #f8f9fa;
            border-bottom: 2px solid #667eea;
        }
        
        .logs-table th {
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #333;
        }
        
        .logs-table td {
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .logs-table tbody tr:hover {
            background: #f8f9fa;
        }
        
        .status {
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
            display: inline-block;
            font-size: 0.85em;
        }
        
        .status.success {
            background: #d4edda;
            color: #155724;
        }
        
        .status.redirect {
            background: #cce5ff;
            color: #004085;
        }
        
        .status.warning {
            background: #fff3cd;
            color: #856404;
        }
        
        .status.error {
            background: #f8d7da;
            color: #721c24;
        }
        
        .method {
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.85em;
            display: inline-block;
        }
        
        .method.get {
            background: #d1ecf1;
            color: #0c5460;
        }
        
        .method.post {
            background: #fff3cd;
            color: #856404;
        }
        
        .method.put {
            background: #e7d4f5;
            color: #5a2d82;
        }
        
        .method.delete {
            background: #f8d7da;
            color: #721c24;
        }
        
        .method.patch {
            background: #d4edda;
            color: #155724;
        }
        
        .time-slow {
            color: #dc3545;
            font-weight: 600;
        }
        
        .time-normal {
            color: #28a745;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .no-data {
            text-align: center;
            padding: 40px;
            color: #999;
            font-size: 1.1em;
        }
        
        .timestamp {
            color: #666;
            font-size: 0.85em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 Request Logs</h1>
            <p>Monitor and filter all API requests</p>
        </div>
        
        <div class="controls">
            <div class="control-group">
                <label>Status Code</label>
                <select id="statusFilter">
                    <option value="">All</option>
                    <option value="2">2xx - Success</option>
                    <option value="3">3xx - Redirect</option>
                    <option value="4">4xx - Client Error</option>
                    <option value="5">5xx - Server Error</option>
                </select>
            </div>
            
            <div class="control-group">
                <label>Method</label>
                <select id="methodFilter">
                    <option value="">All</option>
                    <option value="GET">GET</option>
                    <option value="POST">POST</option>
                    <option value="PUT">PUT</option>
                    <option value="DELETE">DELETE</option>
                    <option value="PATCH">PATCH</option>
                </select>
            </div>
            
            <div class="control-group">
                <label>Path (substring)</label>
                <input type="text" id="pathFilter" placeholder="/api/users">
            </div>
            
            <div class="control-group">
                <label>Min Time (seconds)</label>
                <input type="number" id="timeFilter" min="0" step="0.1" placeholder="0">
            </div>
            
            <div class="control-group">
                <label>Limit</label>
                <input type="number" id="limitFilter" value="50" min="1" max="500">
            </div>
            
            <div class="button-group">
                <button class="btn-filter" onclick="applyFilters()">🔍 Filter</button>
                <button class="btn-refresh" onclick="loadLogs()">🔄 Refresh</button>
                <button class="btn-reset" onclick="resetFilters()">↺ Reset</button>
            </div>
        </div>
        
        <div class="content">
            <div id="stats" class="stats"></div>
            
            <div id="loadingContainer" class="loading" style="display: none;">
                <div class="spinner"></div>
                <p>Loading logs...</p>
            </div>
            
            <div id="noData" class="no-data" style="display: none;">
                No logs found matching the criteria
            </div>
            
            <table id="logsTable" class="logs-table" style="display: none;">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Client</th>
                        <th>Method</th>
                        <th>Path</th>
                        <th>Status</th>
                        <th>Time (ms)</th>
                    </tr>
                </thead>
                <tbody id="logsTableBody">
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        const logCache = {
            entries: [],
            stats: {}
        };
        
        function formatStatus(statusCode) {
            if (statusCode < 300) return 'success';
            if (statusCode < 400) return 'redirect';
            if (statusCode < 500) return 'warning';
            return 'error';
        }
        
        function formatMethod(method) {
            return method.toLowerCase();
        }
        
        function formatTime(seconds) {
            return (seconds * 1000).toFixed(0);
        }
        
        function loadLogs() {
            const loadingContainer = document.getElementById('loadingContainer');
            loadingContainer.style.display = 'block';
            
            const limit = document.getElementById('limitFilter').value || 50;
            
            fetch(`/logs/api/data?limit=${limit}`)
                .then(response => response.json())
                .then(data => {
                    logCache.entries = data.entries || [];
                    logCache.stats = data.stats || {};
                    renderLogs();
                    renderStats();
                    loadingContainer.style.display = 'none';
                })
                .catch(error => {
                    console.error('Error loading logs:', error);
                    loadingContainer.style.display = 'none';
                });
        }
        
        function applyFilters() {
            const statusFilter = document.getElementById('statusFilter').value;
            const methodFilter = document.getElementById('methodFilter').value;
            const pathFilter = document.getElementById('pathFilter').value.toLowerCase();
            const timeFilter = parseFloat(document.getElementById('timeFilter').value) || 0;
            
            const filtered = logCache.entries.filter(entry => {
                if (statusFilter && !entry.status.toString().startsWith(statusFilter)) return false;
                if (methodFilter && entry.method !== methodFilter) return false;
                if (pathFilter && !entry.path.toLowerCase().includes(pathFilter)) return false;
                if (entry.time < timeFilter) return false;
                return true;
            });
            
            renderFilteredLogs(filtered);
        }
        
        function resetFilters() {
            document.getElementById('statusFilter').value = '';
            document.getElementById('methodFilter').value = '';
            document.getElementById('pathFilter').value = '';
            document.getElementById('timeFilter').value = '';
            document.getElementById('limitFilter').value = '50';
            renderLogs();
        }
        
        function renderStats() {
            const statsDiv = document.getElementById('stats');
            statsDiv.innerHTML = `
                <div class="stat-card">
                    <div class="value">${logCache.stats.total_requests || 0}</div>
                    <div class="label">Total Requests</div>
                </div>
                <div class="stat-card">
                    <div class="value">${(logCache.stats.avg_time || 0).toFixed(3)}s</div>
                    <div class="label">Avg Time</div>
                </div>
                <div class="stat-card">
                    <div class="value">${(logCache.stats.max_time || 0).toFixed(3)}s</div>
                    <div class="label">Max Time</div>
                </div>
                <div class="stat-card">
                    <div class="value">${logCache.stats.errors || 0}</div>
                    <div class="label">Errors</div>
                </div>
            `;
        }
        
        function renderFilteredLogs(entries) {
            if (entries.length === 0) {
                document.getElementById('logsTable').style.display = 'none';
                document.getElementById('noData').style.display = 'block';
                return;
            }
            
            const tbody = document.getElementById('logsTableBody');
            tbody.innerHTML = entries.map(entry => `
                <tr>
                    <td><span class="timestamp">${entry.timestamp}</span></td>
                    <td>${entry.client}</td>
                    <td><span class="method ${formatMethod(entry.method)}">${entry.method}</span></td>
                    <td>${entry.path}</td>
                    <td><span class="status ${formatStatus(entry.status)}">${entry.status} ${entry.status_text}</span></td>
                    <td><span class="${entry.time > 1 ? 'time-slow' : 'time-normal'}">${formatTime(entry.time)}</span></td>
                </tr>
            `).join('');
            
            document.getElementById('logsTable').style.display = 'table';
            document.getElementById('noData').style.display = 'none';
        }
        
        function renderLogs() {
            renderFilteredLogs(logCache.entries);
        }
        
        // Load logs on page load
        document.addEventListener('DOMContentLoaded', loadLogs);
    </script>
</body>
</html>
"""


def parse_log_line(line: str) -> Optional[dict]:
  """Parse a log line and extract information."""
  pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+) \| (\w+) \| (.+?) - (\w+) (.+?) - Status: (\d{3}) (.+?) - Time: ([\d.]+)s"

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


def is_admin(request: Request) -> bool:
  """Check if user is admin."""
  if not hasattr(request.state, "user"):
    return False

  user_data = request.state.user
  roles = user_data.get("roles", [])
  return "ADMIN" in roles or any(role.get("name") == "ADMIN" for role in roles if isinstance(role, dict))


@router.get("/logs", include_in_schema=False)
async def logs_page(request: Request):
  """Render logs viewer page (HTML)."""
  if not is_admin(request):
    raise HTTPException(status_code=403, detail="Only admins can access logs")

  from fastapi.responses import HTMLResponse
  return HTMLResponse(content=LOGS_HTML_TEMPLATE)


@router.get("/logs/api/data")
async def get_logs_data(
    request: Request,
    status: Optional[int] = Query(None),
    method: Optional[str] = Query(None),
    path: Optional[str] = Query(None),
    min_time: float = Query(0.0),
    limit: int = Query(50, ge=1, le=500),
):
  """API endpoint to get logs data in JSON format."""
  if not is_admin(request):
    raise HTTPException(status_code=403, detail="Only admins can access logs")

  log_file = Path("logs/requests.log")

  if not log_file.exists():
    return {
        "entries": [],
        "stats": {
            "total_requests": 0,
            "avg_time": 0,
            "max_time": 0,
            "errors": 0,
        }
    }

  entries = []
  with open(log_file, "r", encoding="utf-8") as f:
    for line in f:
      entry = parse_log_line(line.strip())
      if not entry:
        continue

      # Apply filters
      if status and entry["status"] != status:
        continue
      if method and entry["method"] != method:
        continue
      if path and path not in entry["path"]:
        continue
      if entry["time"] < min_time:
        continue

      entries.append(entry)

  # Get last N entries
  entries = entries[-limit:]

  # Calculate stats
  if entries:
    error_count = sum(1 for e in entries if e["status"] >= 400)
    avg_time = sum(e["time"] for e in entries) / len(entries)
    max_time = max(e["time"] for e in entries)
  else:
    error_count = 0
    avg_time = 0
    max_time = 0

  return {
      "entries": entries,
      "stats": {
          "total_requests": len(entries),
          "avg_time": avg_time,
          "max_time": max_time,
          "errors": error_count,
      }
  }
