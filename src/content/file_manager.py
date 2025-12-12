"""
Gerenciamento de arquivos do AutoPost.

Funções utilitárias para manipulação de arquivos e pastas.
"""

import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from ..core.config import get_config


def get_pending_folders() -> List[Path]:
    """
    Lista todas as pastas pendentes para postagem.
    
    Returns:
        Lista de paths de pastas ordenadas por nome.
    """
    config = get_config()
    content_path = config.local_content_path
    
    if not content_path.exists():
        return []
    
    folders = []
    
    for item in content_path.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            # Ignorar pasta "posted"
            if item.name.lower() != "posted":
                folders.append(item)
    
    return sorted(folders, key=lambda f: f.name)


def get_next_folder() -> Optional[Path]:
    """
    Retorna a próxima pasta a ser postada.
    
    Returns:
        Path da próxima pasta ou None se não houver.
    """
    folders = get_pending_folders()
    return folders[0] if folders else None


def mark_as_posted(folder: Path, delete: bool = False) -> Path:
    """
    Marca uma pasta como postada.
    
    Move para a pasta "posted" ou deleta.
    
    Args:
        folder: Path da pasta.
        delete: Se True, deleta em vez de mover.
        
    Returns:
        Novo path da pasta (ou None se deletada).
    """
    if delete:
        shutil.rmtree(folder)
        return None
    
    config = get_config()
    posted_path = config.local_content_path / "posted"
    posted_path.mkdir(exist_ok=True)
    
    # Adicionar timestamp para evitar conflitos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_name = f"{folder.name}_{timestamp}"
    destination = posted_path / new_name
    
    shutil.move(str(folder), str(destination))
    
    return destination


def cleanup_posted(days: int = 30) -> int:
    """
    Remove pastas postadas há mais de X dias.
    
    Args:
        days: Número de dias para manter.
        
    Returns:
        Quantidade de pastas removidas.
    """
    config = get_config()
    posted_path = config.local_content_path / "posted"
    
    if not posted_path.exists():
        return 0
    
    removed = 0
    cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
    
    for folder in posted_path.iterdir():
        if folder.is_dir():
            if folder.stat().st_mtime < cutoff:
                shutil.rmtree(folder)
                removed += 1
    
    return removed


def ensure_content_structure() -> None:
    """
    Garante que a estrutura de pastas existe.
    """
    config = get_config()
    
    # Criar pastas principais
    config.local_content_path.mkdir(parents=True, exist_ok=True)
    (config.local_content_path / "posted").mkdir(exist_ok=True)
    config.data_path.mkdir(parents=True, exist_ok=True)


def get_folder_info(folder: Path) -> dict:
    """
    Retorna informações sobre uma pasta.
    
    Args:
        folder: Path da pasta.
        
    Returns:
        Dict com informações.
    """
    if not folder.exists() or not folder.is_dir():
        return {}
    
    images = list(folder.glob("*.jpg")) + list(folder.glob("*.png"))
    caption_file = folder / "caption.txt"
    
    return {
        "name": folder.name,
        "path": str(folder),
        "image_count": len(images),
        "has_caption": caption_file.exists(),
        "created": datetime.fromtimestamp(folder.stat().st_ctime).isoformat(),
    }


def list_folders_with_info() -> List[dict]:
    """
    Lista pastas pendentes com informações detalhadas.
    
    Returns:
        Lista de dicts com info de cada pasta.
    """
    folders = get_pending_folders()
    return [get_folder_info(f) for f in folders]
