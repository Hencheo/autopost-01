"""
Aplicação FastAPI do AutoPost Dashboard.

Servidor web para gerenciar e monitorar o sistema.
"""

from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from .routes import dashboard, actions, settings
from ..scheduler.scheduler import get_scheduler
from ..core.config import get_config


# Lifecycle manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia startup e shutdown."""
    # Startup
    print("🚀 Iniciando AutoPost Dashboard...")
    
    config = get_config()
    config.ensure_directories()
    
    # Iniciar scheduler
    scheduler = get_scheduler()
    scheduler.start()
    
    yield
    
    # Shutdown
    print("👋 Encerrando AutoPost...")
    scheduler.stop()


# Criar app
app = FastAPI(
    title="AutoPost Dashboard",
    description="Sistema de postagem automatizada para Instagram",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files e templates
CURRENT_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=CURRENT_DIR / "static"), name="static")
templates = Jinja2Templates(directory=CURRENT_DIR / "templates")

# Incluir rotas
app.include_router(dashboard.router)
app.include_router(actions.router, prefix="/api")
app.include_router(settings.router, prefix="/api/settings")


@app.get("/health")
async def health_check():
    """Endpoint de health check."""
    return {"status": "ok"}
