"""
Rotas do Dashboard.

Página principal e endpoints de status.
"""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ...scheduler.scheduler import get_scheduler
from ...storage.state import get_state_manager
from ...storage.local import get_local_storage
from ...storage.drive_sync import get_drive_sync


router = APIRouter()

# Templates
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Página principal do dashboard."""
    scheduler = get_scheduler()
    state = get_state_manager()
    
    context = {
        "request": request,
        "status": scheduler.get_status(),
        "stats": state.get_stats(),
        "queue": scheduler.get_queue()[:5],  # Primeiros 5
        "history": state.get_history(limit=5)  # Últimos 5
    }
    
    return templates.TemplateResponse("dashboard.html", context)


@router.get("/api/status")
async def get_status():
    """Retorna status completo do scheduler."""
    scheduler = get_scheduler()
    state = get_state_manager()
    storage = get_local_storage()
    
    return {
        "scheduler": scheduler.get_status(),
        "stats": state.get_stats(),
        "folders": storage.get_folder_count()
    }


@router.get("/api/history")
async def get_history(limit: int = 20):
    """Retorna histórico de posts."""
    state = get_state_manager()
    return {"history": state.get_history(limit=limit)}


@router.get("/api/pending")
async def get_pending():
    """Retorna pastas pendentes."""
    scheduler = get_scheduler()
    return {"queue": scheduler.get_queue()}


@router.get("/api/drive-status")
async def get_drive_status():
    """Retorna status do Google Drive."""
    try:
        drive = get_drive_sync()
        return drive.get_sync_status()
    except Exception as e:
        return {"error": str(e)}
