# Local Launch & Environment Guide: CS2 Highlights Studio

> **Verified Working Directory:** `c:\Users\pyPypy\Documents\MySCOPE\demToshka`  
> **Operating System:** Windows 10/11 x64  
> **Python Version:** 3.12 (Virtual Environment: `.venv`)  
> **Node.js Version:** 20+ (Verified on Node v24.20.0, npm v11.19.0)

---

## 1. Verified Local URLs & Ports

| Component | Verified Local URL | Port | Health Check / Protocol |
| :--- | :--- | :---: | :--- |
| **Frontend Web Application** | `http://127.0.0.1:5173/` | `5173` | HTTP / Vite Dev Server |
| **Backend FastAPI Engine** | `http://127.0.0.1:8000/` | `8000` | HTTP / ASGI (Uvicorn) |
| **Backend Health Endpoint** | `http://127.0.0.1:8000/api/health` | `8000` | Returns `{"status":"ok","schema_version":1}` |
| **OpenAPI / Swagger Docs** | `http://127.0.0.1:8000/docs` | `8000` | Interactive API documentation |

---

## 2. Environment Variables & Defaults

No secret environment variables or external API keys are required (fully local-first).
Optional environment overrides:

```bash
# Database file location (defaults to demtoshka.db in project root)
CS2_DB_PATH="demtoshka.db"

# Renders output directory (defaults to renders/ in project root)
CS2_RENDERS_DIR="renders"

# Server Host and Port
UVICORN_HOST="127.0.0.1"
UVICORN_PORT="8000"
```

---

## 3. Exact Commands to Launch Locally

### Terminal 1: Backend API Server
Execute from the project root (`c:\Users\pyPypy\Documents\MySCOPE\demToshka`):

```powershell
# Using the project's virtual environment:
.venv\Scripts\python.exe -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

> **Verification:** In a browser or via PowerShell, run:  
> `Invoke-RestMethod -Uri http://127.0.0.1:8000/api/health`  
> It will return `{"status": "ok", "schema_version": 1}`.

### Terminal 2: Frontend Vite Server
Execute from the project root using Windows Command Prompt syntax (to avoid PowerShell execution policy issues):

```cmd
cmd.exe /c "npm --prefix frontend run dev -- --host 127.0.0.1 --port 5173"
```
Or directly from the `frontend/` directory:
```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

> **Note on Proxying:** The Vite configuration (`frontend/vite.config.ts`) automatically forwards all `/api` requests to `http://127.0.0.1:8000`. Accessing `http://127.0.0.1:5173/` provides full seamless operation.

---

## 4. Useful File Paths

| Resource | Path |
| :--- | :--- |
| **Project Root** | `c:\Users\pyPypy\Documents\MySCOPE\demToshka` |
| **Active SQLite Database** | `c:\Users\pyPypy\Documents\MySCOPE\demToshka\demtoshka.db` |
| **Completed Rendered MP4s** | `c:\Users\pyPypy\Documents\MySCOPE\demToshka\renders\` |
| **Bundled FFmpeg Binary** | `c:\Users\pyPypy\Documents\MySCOPE\demToshka\tools\hlae\ffmpeg\bin\ffmpeg.exe` |
| **Bundled HLAE Binary** | `c:\Users\pyPypy\Documents\MySCOPE\demToshka\tools\hlae\HLAE.exe` |
| **Video Handoff Screenshots** | `c:\Users\pyPypy\Documents\MySCOPE\demToshka\video-handoff\assets\screenshots\` |
| **Video Handoff Footage** | `c:\Users\pyPypy\Documents\MySCOPE\demToshka\video-handoff\assets\footage\` |

---

## 5. Troubleshooting Common Issues

1. **Port 8000 or 5173 already occupied:**
   Check running processes:
   ```powershell
   Get-Process -Name python, node -ErrorAction SilentlyContinue
   ```
2. **Database locked / WAL checkpoint:**
   The SQLite connection uses WAL mode. Do not delete `demtoshka.db-wal` or `demtoshka.db-shm` while the backend is active.
3. **PowerShell execution policy blocks `npm.ps1`:**
   Always invoke via `cmd.exe /c "npm ..."` or set `Set-ExecutionPolicy -Scope Process Bypass`.

