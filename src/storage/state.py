"""
Gerenciamento de estado persistente.

Salva e recupera o estado do scheduler e histórico de posts.
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..core.config import get_config
from ..core.exceptions import StateError


class StateManager:
    """
    Gerenciador de estado persistente.
    
    Responsável por:
    - Salvar/carregar estado do scheduler
    - Manter histórico de posts
    - Recuperação após reinício
    """
    
    def __init__(self, state_path: Optional[Path] = None,
                 history_path: Optional[Path] = None):
        """
        Inicializa o gerenciador de estado.
        
        Args:
            state_path: Path do arquivo de estado.
            history_path: Path do arquivo de histórico.
        """
        config = get_config()
        self.state_path = state_path or config.get_state_path()
        self.history_path = history_path or config.get_history_path()
        self._ensure_files()
    
    def _ensure_files(self) -> None:
        """Garante que os diretórios existem."""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
    
    def save_state(self, state: dict) -> None:
        """
        Salva o estado atual.
        
        Args:
            state: Dicionário com o estado.
        """
        try:
            state["last_updated"] = datetime.now().isoformat()
            
            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise StateError(f"Erro ao salvar estado: {e}")
    
    def load_state(self) -> dict:
        """
        Carrega o estado salvo.
        
        Returns:
            Dicionário com o estado ou estado padrão.
        """
        if not self.state_path.exists():
            return self._get_default_state()
        
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception):
            return self._get_default_state()
    
    def _get_default_state(self) -> dict:
        """Retorna o estado padrão."""
        config = get_config()
        return {
            "scheduler_enabled": True,
            "post_times": config.post_times,
            "last_post_time": None,
            "next_post_time": None,
            "posts_today": 0,
            "last_updated": datetime.now().isoformat()
        }
    
    def add_to_history(self, post_info: dict) -> None:
        """
        Adiciona um post ao histórico.
        
        Args:
            post_info: Informações do post.
        """
        history = self.get_history()
        
        # Adicionar timestamp se não tiver
        if "timestamp" not in post_info:
            post_info["timestamp"] = datetime.now().isoformat()
        
        history.insert(0, post_info)
        
        # Manter apenas os últimos 100 posts
        history = history[:100]
        
        try:
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise StateError(f"Erro ao salvar histórico: {e}")
    
    def get_history(self, limit: int = 50) -> List[dict]:
        """
        Retorna o histórico de posts.
        
        Args:
            limit: Número máximo de posts a retornar.
            
        Returns:
            Lista de posts (mais recentes primeiro).
        """
        if not self.history_path.exists():
            return []
        
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
            return history[:limit]
        except (json.JSONDecodeError, Exception):
            return []
    
    def get_last_post(self) -> Optional[dict]:
        """
        Retorna o último post.
        
        Returns:
            Informações do último post ou None.
        """
        history = self.get_history(limit=1)
        return history[0] if history else None
    
    def get_stats(self) -> dict:
        """
        Retorna estatísticas do histórico.
        
        Returns:
            Dict com estatísticas.
        """
        history = self.get_history(limit=100)
        
        if not history:
            return {
                "total_posts": 0,
                "posts_today": 0,
                "posts_this_week": 0,
                "last_post": None
            }
        
        today = datetime.now().date().isoformat()
        week_ago = (datetime.now().timestamp() - (7 * 24 * 60 * 60))
        
        posts_today = 0
        posts_week = 0
        
        for post in history:
            post_time = post.get("timestamp", "")
            if post_time.startswith(today):
                posts_today += 1
            
            try:
                post_dt = datetime.fromisoformat(post_time.replace("Z", "+00:00"))
                if post_dt.timestamp() > week_ago:
                    posts_week += 1
            except (ValueError, AttributeError):
                pass
        
        return {
            "total_posts": len(history),
            "posts_today": posts_today,
            "posts_this_week": posts_week,
            "last_post": history[0] if history else None
        }
    
    def update_post_times(self, times: List[str]) -> None:
        """
        Atualiza os horários de postagem.
        
        Args:
            times: Lista de horários (ex: ["09:00", "15:00", "21:00"]).
        """
        state = self.load_state()
        state["post_times"] = times
        self.save_state(state)
    
    def get_post_times(self) -> List[str]:
        """
        Retorna os horários de postagem configurados.
        
        Returns:
            Lista de horários.
        """
        state = self.load_state()
        return state.get("post_times", [])
    
    def set_scheduler_enabled(self, enabled: bool) -> None:
        """
        Ativa/desativa o scheduler.
        
        Args:
            enabled: True para ativar.
        """
        state = self.load_state()
        state["scheduler_enabled"] = enabled
        self.save_state(state)
    
    def is_scheduler_enabled(self) -> bool:
        """
        Verifica se o scheduler está ativo.
        
        Returns:
            True se ativo.
        """
        state = self.load_state()
        return state.get("scheduler_enabled", True)
    
    def clear_state(self) -> None:
        """Limpa o estado (reinicia)."""
        self.save_state(self._get_default_state())
    
    def clear_history(self) -> None:
        """Limpa o histórico."""
        try:
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump([], f)
        except Exception:
            pass


# Instância global
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Retorna o state manager singleton."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager
