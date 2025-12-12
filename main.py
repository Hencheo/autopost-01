"""
AutoPost - Entry Point Principal

Sistema de postagem automatizada para Instagram.
"""

import uvicorn
from src.core.config import get_config


def main():
    """Inicia o servidor AutoPost."""
    config = get_config()
    
    print("""
    ╔═══════════════════════════════════════════════╗
    ║                                               ║
    ║     📱 AutoPost - Sistema de Postagem         ║
    ║        Automatizada para Instagram            ║
    ║                                               ║
    ╚═══════════════════════════════════════════════╝
    """)
    
    print(f"🌐 Iniciando servidor em http://{config.api_host}:{config.api_port}")
    print(f"📅 Horários configurados: {', '.join(config.post_times)}")
    print(f"🕐 Timezone: {config.timezone}")
    print()
    
    uvicorn.run(
        "src.api.app:app",
        host=config.api_host,
        port=config.api_port,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
