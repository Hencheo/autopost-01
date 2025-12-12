"""
Configurações centralizadas do AutoPost.

Carrega e valida todas as variáveis de ambiente necessárias.
"""

import os
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

from .exceptions import ConfigError
from .constants import DEFAULT_POST_TIMES, DEFAULT_TIMEZONE


# Carrega .env do diretório raiz
load_dotenv()


@dataclass
class Config:
    """
    Configuração centralizada do AutoPost.
    
    Carrega valores do .env e fornece defaults sensatos.
    """
    
    # ============================================================
    # INSTAGRAM
    # ============================================================
    instagram_username: str = field(default_factory=lambda: os.getenv("INSTAGRAM_USERNAME", ""))
    instagram_password: str = field(default_factory=lambda: os.getenv("INSTAGRAM_PASSWORD", ""))
    instagram_session_id: str = field(default_factory=lambda: os.getenv("INSTAGRAM_SESSION_ID", ""))
    
    # ============================================================
    # GOOGLE DRIVE
    # ============================================================
    drive_folder_id: str = field(default_factory=lambda: os.getenv("DRIVE_FOLDER_ID", ""))
    google_credentials_path: str = field(default_factory=lambda: os.getenv("GOOGLE_CREDENTIALS_PATH", ""))
    google_credentials_json: str = field(default_factory=lambda: os.getenv("GOOGLE_CREDENTIALS_JSON", ""))
    
    # ============================================================
    # AGENDAMENTO
    # ============================================================
    post_times: list = field(default_factory=lambda: Config._parse_times(os.getenv("POST_TIMES", "")))
    timezone: str = field(default_factory=lambda: os.getenv("TIMEZONE", DEFAULT_TIMEZONE))
    
    # ============================================================
    # API
    # ============================================================
    api_host: str = field(default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"))
    api_port: int = field(default_factory=lambda: int(os.getenv("API_PORT", "8000")))
    
    # ============================================================
    # PATHS
    # ============================================================
    local_content_path: Path = field(default_factory=lambda: Path(os.getenv("LOCAL_CONTENT_PATH", "./content/posts")))
    data_path: Path = field(default_factory=lambda: Path(os.getenv("DATA_PATH", "./data")))
    
    @staticmethod
    def _parse_times(times_str: str) -> list:
        """Converte string de horários em lista."""
        if not times_str:
            return DEFAULT_POST_TIMES.copy()
        return [t.strip() for t in times_str.split(",") if t.strip()]
    
    def __post_init__(self):
        """Converte paths para objetos Path."""
        if isinstance(self.local_content_path, str):
            self.local_content_path = Path(self.local_content_path)
        if isinstance(self.data_path, str):
            self.data_path = Path(self.data_path)
    
    def validate(self) -> bool:
        """
        Valida se as configurações obrigatórias estão presentes.
        
        Raises:
            ConfigError: Se alguma configuração obrigatória estiver ausente.
        """
        errors = []
        
        # Instagram: precisa de username/password OU session_id
        if not self.instagram_session_id:
            if not self.instagram_username:
                errors.append("INSTAGRAM_USERNAME não configurado")
            if not self.instagram_password:
                errors.append("INSTAGRAM_PASSWORD não configurado")
        
        # Google Drive: precisa de folder_id e credenciais
        if not self.drive_folder_id:
            errors.append("DRIVE_FOLDER_ID não configurado")
        
        if not self.google_credentials_path and not self.google_credentials_json:
            errors.append("GOOGLE_CREDENTIALS_PATH ou GOOGLE_CREDENTIALS_JSON não configurado")
        
        if errors:
            raise ConfigError(f"Configuração inválida: {', '.join(errors)}")
        
        return True
    
    def get_google_credentials(self) -> dict:
        """
        Retorna as credenciais do Google como dicionário.
        
        Prioriza GOOGLE_CREDENTIALS_JSON (para deploy),
        depois GOOGLE_CREDENTIALS_PATH (para desenvolvimento local).
        """
        # Primeiro tenta JSON direto (para Render/Railway)
        if self.google_credentials_json:
            try:
                return json.loads(self.google_credentials_json)
            except json.JSONDecodeError as e:
                raise ConfigError(f"GOOGLE_CREDENTIALS_JSON inválido: {e}")
        
        # Depois tenta carregar do arquivo
        if self.google_credentials_path:
            cred_path = Path(self.google_credentials_path)
            if not cred_path.exists():
                raise ConfigError(f"Arquivo de credenciais não encontrado: {cred_path}")
            try:
                with open(cred_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                raise ConfigError(f"Arquivo de credenciais inválido: {e}")
        
        raise ConfigError("Nenhuma credencial do Google configurada")
    
    def get_session_path(self) -> Path:
        """Retorna o path do arquivo de sessão do Instagram."""
        return self.data_path / "session.json"
    
    def get_state_path(self) -> Path:
        """Retorna o path do arquivo de estado."""
        return self.data_path / "state.json"
    
    def get_history_path(self) -> Path:
        """Retorna o path do arquivo de histórico."""
        return self.data_path / "posted.json"
    
    def ensure_directories(self) -> None:
        """Cria os diretórios necessários se não existirem."""
        self.local_content_path.mkdir(parents=True, exist_ok=True)
        self.data_path.mkdir(parents=True, exist_ok=True)


# Instância global de configuração
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Retorna a instância global de configuração.
    
    Usa padrão singleton para evitar múltiplos carregamentos.
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config() -> Config:
    """
    Recarrega a configuração do .env.
    
    Útil para atualizar configurações em runtime.
    """
    global _config
    load_dotenv(override=True)
    _config = Config()
    return _config
