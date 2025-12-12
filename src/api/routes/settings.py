"""
Rotas de configurações do AutoPost.

Endpoints para gerenciar configurações.
"""

from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...scheduler.scheduler import get_scheduler
from ...storage.state import get_state_manager


router = APIRouter(tags=["settings"])


class UpdateTimesRequest(BaseModel):
    """Request para atualizar horários."""
    times: List[str]


@router.get("/")
async def get_settings():
    """Retorna configurações atuais."""
    scheduler = get_scheduler()
    state = get_state_manager()
    
    return {
        "post_times": state.get_post_times(),
        "scheduler_enabled": state.is_scheduler_enabled(),
        "running": scheduler.is_running()
    }


@router.post("/times")
async def update_times(request: UpdateTimesRequest):
    """Atualiza os horários de postagem."""
    try:
        scheduler = get_scheduler()
        scheduler.update_times(request.times)
        
        return {
            "success": True,
            "times": request.times,
            "message": f"Horários atualizados: {', '.join(request.times)}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/toggle")
async def toggle_scheduler():
    """Liga/desliga o scheduler."""
    scheduler = get_scheduler()
    
    if scheduler.is_running():
        scheduler.stop()
        return {"success": True, "enabled": False}
    else:
        scheduler.start()
        return {"success": True, "enabled": True}
