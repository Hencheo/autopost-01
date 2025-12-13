"""
Rotas de ações do AutoPost.

Endpoints para executar ações manuais.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...scheduler.scheduler import get_scheduler
from ...storage.local import get_local_storage
from ...storage.state import get_state_manager
from ...storage.drive_sync import get_drive_sync


router = APIRouter(tags=["actions"])


class PostFolderRequest(BaseModel):
    """Request para postar pasta específica."""
    folder_name: str


class CleanupRequest(BaseModel):
    """Request para cleanup."""
    days: int = 30


@router.post("/post-now")
async def post_now():
    """Posta o próximo item da fila imediatamente."""
    try:
        scheduler = get_scheduler()
        result = scheduler.post_now()
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/post-folder")
async def post_folder(request: PostFolderRequest):
    """Posta uma pasta específica."""
    try:
        scheduler = get_scheduler()
        result = scheduler.post_now(request.folder_name)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sync-drive")
async def sync_drive():
    """Sincroniza com o Google Drive."""
    try:
        drive = get_drive_sync()
        downloaded = drive.sync()
        return {
            "success": True,
            "downloaded": len(downloaded),
            "folders": [p.name for p in downloaded]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cleanup")
async def cleanup(request: CleanupRequest):
    """Remove pastas postadas antigas."""
    storage = get_local_storage()
    removed = storage.cleanup_posted(days=request.days)
    return {"success": True, "removed": removed}


@router.post("/reset-state")
async def reset_state():
    """Reseta o estado do scheduler."""
    state = get_state_manager()
    state.clear_state()
    return {"success": True, "message": "Estado resetado"}


@router.post("/toggle-scheduler")
async def toggle_scheduler():
    """Liga/desliga o scheduler."""
    scheduler = get_scheduler()
    
    if scheduler.is_running():
        scheduler.stop()
        return {"success": True, "running": False}
    else:
        scheduler.start()
        return {"success": True, "running": True}


@router.post("/move-to-front")
async def move_to_front(request: PostFolderRequest):
    """Move uma pasta para o início da fila."""
    from ...scheduler.queue import get_post_queue
    
    queue = get_post_queue()
    success = queue.move_to_front(request.folder_name)
    
    if success:
        return {"success": True, "message": f"{request.folder_name} movido para frente"}
    else:
        raise HTTPException(status_code=404, detail="Pasta não encontrada na fila")


@router.post("/test-login")
async def test_login():
    """Testa o login no Instagram (força re-autenticação)."""
    try:
        from ...instagram.client import get_instagram_client
        
        client = get_instagram_client()
        
        # Forçar re-login para testar credenciais
        client.force_relogin()
        
        # Verificar se está logado
        if client.is_logged_in():
            username = client.get_username()
            return {
                "success": True, 
                "message": f"Login bem-sucedido como @{username}",
                "username": username
            }
        else:
            return {"success": False, "message": "Login falhou"}
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro no login: {str(e)}")


@router.post("/clear-session")
async def clear_session():
    """Limpa a sessão salva do Instagram (força novo login no próximo uso)."""
    try:
        from ...instagram.auth import SessionManager
        
        session_manager = SessionManager()
        session_manager.clear_session()
        
        # Também resetar o estado do cliente singleton
        from ...instagram.client import get_instagram_client
        client = get_instagram_client()
        client.reset_session_state()
        
        return {
            "success": True, 
            "message": "Sessão limpa. Próximo login usará credenciais fresh."
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao limpar sessão: {str(e)}")
