"""
Storage local do AutoPost.

Gerencia arquivos e pastas de conteúdo no sistema local.
"""

import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from ..core.config import get_config
from ..core.exceptions import StorageError


class LocalStorage:
    """
    Gerenciador de armazenamento local.
    
    Responsável por:
    - Listar pastas pendentes
    - Mover pastas para "posted"
    - Limpar posts antigos
    """
    
    def __init__(self, content_path: Optional[Path] = None):
        """
        Inicializa o storage local.
        
        Args:
            content_path: Path do diretório de conteúdo.
                         Se None, usa o path da config.
        """
        config = get_config()
        self.content_path = content_path or config.local_content_path
        self.posted_path = self.content_path / "posted"
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Garante que os diretórios existem."""
        self.content_path.mkdir(parents=True, exist_ok=True)
        self.posted_path.mkdir(exist_ok=True)
    
    def get_pending_folders(self) -> List[Path]:
        """
        Lista pastas pendentes para postagem.
        
        Returns:
            Lista de paths ordenada por nome.
        """
        if not self.content_path.exists():
            return []
        
        folders = []
        
        for item in self.content_path.iterdir():
            if self._is_valid_content_folder(item):
                folders.append(item)
        
        return sorted(folders, key=lambda f: f.name.lower())
    
    def _is_valid_content_folder(self, path: Path) -> bool:
        """Verifica se é uma pasta válida de conteúdo."""
        if not path.is_dir():
            return False
        
        # Ignorar pastas especiais
        if path.name.startswith("."):
            return False
        
        if path.name.lower() in ("posted", "processed", "__pycache__"):
            return False
        
        # Verificar se tem pelo menos uma imagem
        images = list(path.glob("*.jpg")) + list(path.glob("*.png")) + list(path.glob("*.jpeg"))
        return len(images) > 0
    
    def get_next_folder(self) -> Optional[Path]:
        """
        Retorna a próxima pasta a ser postada.
        
        Returns:
            Path da próxima pasta ou None.
        """
        folders = self.get_pending_folders()
        return folders[0] if folders else None
    
    def mark_as_posted(self, folder: Path, delete: bool = False) -> Optional[Path]:
        """
        Marca uma pasta como postada.
        
        Args:
            folder: Path da pasta.
            delete: Se True, deleta em vez de mover.
            
        Returns:
            Novo path ou None se deletada.
        """
        if not folder.exists():
            raise StorageError(f"Pasta não encontrada: {folder}")
        
        if delete:
            shutil.rmtree(folder)
            print(f"🗑️ Pasta deletada: {folder.name}")
            return None
        
        # Mover para posted com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_name = f"{folder.name}_{timestamp}"
        destination = self.posted_path / new_name
        
        shutil.move(str(folder), str(destination))
        print(f"📁 Pasta movida para: {destination}")
        
        return destination
    
    def cleanup_posted(self, days: int = 30) -> int:
        """
        Remove pastas postadas há mais de X dias.
        
        Args:
            days: Número de dias para manter.
            
        Returns:
            Quantidade de pastas removidas.
        """
        if not self.posted_path.exists():
            return 0
        
        removed = 0
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for folder in self.posted_path.iterdir():
            if folder.is_dir():
                if folder.stat().st_mtime < cutoff:
                    shutil.rmtree(folder)
                    removed += 1
                    print(f"🗑️ Removido: {folder.name}")
        
        if removed > 0:
            print(f"✅ {removed} pasta(s) antiga(s) removida(s)")
        
        return removed
    
    def get_folder_count(self) -> dict:
        """
        Retorna contagem de pastas.
        
        Returns:
            Dict com contagens.
        """
        pending = len(self.get_pending_folders())
        posted = len(list(self.posted_path.iterdir())) if self.posted_path.exists() else 0
        
        return {
            "pending": pending,
            "posted": posted,
            "total": pending + posted
        }
    
    def folder_exists(self, folder_name: str) -> bool:
        """
        Verifica se uma pasta existe.
        
        Args:
            folder_name: Nome da pasta.
            
        Returns:
            True se existe.
        """
        return (self.content_path / folder_name).exists()
    
    def get_folder_by_name(self, folder_name: str) -> Optional[Path]:
        """
        Retorna uma pasta pelo nome.
        
        Args:
            folder_name: Nome da pasta.
            
        Returns:
            Path da pasta ou None.
        """
        folder = self.content_path / folder_name
        if folder.exists() and folder.is_dir():
            return folder
        return None


# Instância global
_storage: Optional[LocalStorage] = None


def get_local_storage() -> LocalStorage:
    """Retorna o storage singleton."""
    global _storage
    if _storage is None:
        _storage = LocalStorage()
    return _storage
