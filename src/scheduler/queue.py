"""
Fila de posts para agendamento.

Gerencia a ordem de postagem e priorização.
"""

from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from ..storage.local import get_local_storage


@dataclass
class QueueItem:
    """
    Item na fila de posts.
    
    Attributes:
        folder: Path da pasta de conteúdo.
        priority: Prioridade (menor = mais urgente).
        added_at: Quando foi adicionado à fila.
    """
    folder: Path
    priority: int = 0
    added_at: datetime = field(default_factory=datetime.now)
    
    @property
    def folder_name(self) -> str:
        """Nome da pasta."""
        return self.folder.name


class PostQueue:
    """
    Fila de posts para agendamento.
    
    Gerencia a ordem de postagem baseada em:
    - Prioridade manual
    - Ordem alfabética
    - Ordem de chegada
    """
    
    def __init__(self):
        """Inicializa a fila."""
        self._queue: List[QueueItem] = []
        self._storage = get_local_storage()
    
    def refresh(self) -> None:
        """
        Atualiza a fila com as pastas disponíveis.
        """
        folders = self._storage.get_pending_folders()
        
        # Manter itens existentes que ainda existem
        existing = {item.folder for item in self._queue}
        
        # Adicionar novos
        for folder in folders:
            if folder not in existing:
                self._queue.append(QueueItem(folder=folder))
        
        # Remover os que não existem mais
        self._queue = [
            item for item in self._queue
            if item.folder.exists()
        ]
        
        # Ordenar por prioridade e depois por nome
        self._queue.sort(key=lambda x: (x.priority, x.folder_name.lower()))
    
    def enqueue(self, folder: Path, priority: int = 0) -> None:
        """
        Adiciona uma pasta à fila.
        
        Args:
            folder: Path da pasta.
            priority: Prioridade (menor = mais urgente).
        """
        # Verificar se já está na fila
        for item in self._queue:
            if item.folder == folder:
                item.priority = priority
                self._sort()
                return
        
        self._queue.append(QueueItem(folder=folder, priority=priority))
        self._sort()
    
    def dequeue(self) -> Optional[Path]:
        """
        Remove e retorna o próximo item da fila.
        
        Returns:
            Path da pasta ou None se vazia.
        """
        self.refresh()
        
        if not self._queue:
            return None
        
        item = self._queue.pop(0)
        return item.folder
    
    def peek(self) -> Optional[Path]:
        """
        Retorna o próximo item sem remover.
        
        Returns:
            Path da pasta ou None se vazia.
        """
        self.refresh()
        
        if not self._queue:
            return None
        
        return self._queue[0].folder
    
    def is_empty(self) -> bool:
        """Verifica se a fila está vazia."""
        self.refresh()
        return len(self._queue) == 0
    
    def size(self) -> int:
        """Retorna o tamanho da fila."""
        self.refresh()
        return len(self._queue)
    
    def list(self) -> List[dict]:
        """
        Lista todos os itens da fila.
        
        Returns:
            Lista de dicts com informações.
        """
        self.refresh()
        
        return [
            {
                "folder": item.folder_name,
                "path": str(item.folder),
                "priority": item.priority,
                "position": i + 1
            }
            for i, item in enumerate(self._queue)
        ]
    
    def set_priority(self, folder_name: str, priority: int) -> bool:
        """
        Define a prioridade de uma pasta.
        
        Args:
            folder_name: Nome da pasta.
            priority: Nova prioridade.
            
        Returns:
            True se encontrou e atualizou.
        """
        for item in self._queue:
            if item.folder_name == folder_name:
                item.priority = priority
                self._sort()
                return True
        return False
    
    def move_to_front(self, folder_name: str) -> bool:
        """
        Move uma pasta para frente da fila.
        
        Args:
            folder_name: Nome da pasta.
            
        Returns:
            True se moveu.
        """
        # Encontrar menor prioridade e diminuir 1
        if not self._queue:
            return False
        
        min_priority = min(item.priority for item in self._queue)
        return self.set_priority(folder_name, min_priority - 1)
    
    def _sort(self) -> None:
        """Ordena a fila por prioridade e nome."""
        self._queue.sort(key=lambda x: (x.priority, x.folder_name.lower()))
    
    def clear(self) -> None:
        """Limpa a fila."""
        self._queue.clear()


# Instância global
_queue: Optional[PostQueue] = None


def get_post_queue() -> PostQueue:
    """Retorna a fila singleton."""
    global _queue
    if _queue is None:
        _queue = PostQueue()
    return _queue
