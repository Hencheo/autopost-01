"""
Autenticação e gerenciamento de sessão do Instagram.

Gerencia login, sessão persistente e session hijacking.
"""

import json
import random
import time
import functools
from pathlib import Path
from typing import Optional, Callable, TypeVar, Any
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ClientError, ClientLoginRequired

from ..core.config import get_config
from ..core.exceptions import LoginError
from ..core.constants import POST_LOGIN_DELAY, MIN_ACTION_DELAY, MAX_ACTION_DELAY


# Type variable para preservar tipo de retorno
T = TypeVar('T')


def with_session_retry(max_retries: int = 2) -> Callable:
    """
    Decorator que adiciona retry automático quando a sessão expira.
    
    Detecta erros de LoginRequired/ClientLoginRequired e força
    re-autenticação automática.
    
    Args:
        max_retries: Número máximo de tentativas de re-login.
        
    Returns:
        Função decorada com retry automático.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs) -> T:
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(self, *args, **kwargs)
                    
                except (LoginRequired, ClientLoginRequired, ClientError) as e:
                    error_msg = str(e).lower()
                    
                    # Verificar se é erro de autenticação
                    is_auth_error = (
                        isinstance(e, (LoginRequired, ClientLoginRequired)) or
                        'login_required' in error_msg or
                        'challenge_required' in error_msg or
                        'checkpoint_required' in error_msg or
                        'session' in error_msg
                    )
                    
                    if not is_auth_error:
                        # Não é erro de autenticação, propagar
                        raise
                    
                    last_error = e
                    
                    if attempt < max_retries:
                        print(f"⚠️ Sessão expirada (tentativa {attempt + 1}/{max_retries}). Re-autenticando...")
                        
                        # Forçar re-login
                        try:
                            # Acessar o cliente do Instagram
                            if hasattr(self, '_instagram'):
                                self._instagram.force_relogin()
                            elif hasattr(self, 'force_relogin'):
                                self.force_relogin()
                            else:
                                print("❌ Não foi possível encontrar método de re-login")
                                raise
                                
                            print("✅ Re-autenticação bem-sucedida. Tentando novamente...")
                            humanized_delay(2, 4)  # Delay antes de retry
                            
                        except Exception as relogin_error:
                            print(f"❌ Falha no re-login: {relogin_error}")
                            raise LoginError(f"Não foi possível re-autenticar: {relogin_error}")
                    else:
                        print(f"❌ Todas as tentativas de retry falharam")
                        raise LoginError(f"Sessão expirada após {max_retries} tentativas: {last_error}")
            
            # Não deveria chegar aqui, mas por segurança
            if last_error:
                raise last_error
                
        return wrapper
    return decorator


class SessionManager:
    """
    Gerenciador de sessão do Instagram.
    
    Responsável por:
    - Salvar/carregar sessão persistente
    - Gerenciar device_id consistente
    - Suportar session hijacking
    """
    
    def __init__(self, session_path: Optional[Path] = None):
        """
        Inicializa o gerenciador de sessão.
        
        Args:
            session_path: Caminho para o arquivo de sessão.
                         Se None, usa o path padrão da config.
        """
        config = get_config()
        self.session_path = session_path or config.get_session_path()
        self._ensure_session_dir()
    
    def _ensure_session_dir(self) -> None:
        """Garante que o diretório da sessão existe."""
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
    
    def save_session(self, client: Client) -> None:
        """
        Salva a sessão atual do cliente.
        
        Args:
            client: Cliente do Instagram logado.
        """
        session_data = {
            "settings": client.get_settings(),
            "device_id": client.device_id if hasattr(client, 'device_id') else None,
        }
        
        with open(self.session_path, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2)
        
        print(f"✅ Sessão salva em: {self.session_path}")
    
    def load_session(self, client: Client) -> bool:
        """
        Carrega a sessão salva no cliente.
        
        Args:
            client: Cliente do Instagram.
            
        Returns:
            True se a sessão foi carregada com sucesso.
        """
        if not self.session_path.exists():
            print("⚠️ Nenhuma sessão salva encontrada.")
            return False
        
        try:
            with open(self.session_path, "r", encoding="utf-8") as f:
                session_data = json.load(f)
            
            if "settings" in session_data:
                client.set_settings(session_data["settings"])
            
            if "device_id" in session_data and session_data["device_id"]:
                client.device_id = session_data["device_id"]
            
            print(f"✅ Sessão carregada de: {self.session_path}")
            return True
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️ Erro ao carregar sessão: {e}")
            return False
    
    def clear_session(self) -> None:
        """Remove o arquivo de sessão."""
        if self.session_path.exists():
            self.session_path.unlink()
            print("🗑️ Sessão removida.")
    
    def has_session(self) -> bool:
        """Verifica se existe uma sessão salva."""
        return self.session_path.exists()


def apply_session_hijack(client: Client, session_id: str) -> bool:
    """
    Aplica session hijacking usando o session_id do navegador.
    
    Esta técnica evita o fluxo de login normal e usa a sessão
    já autenticada do navegador do usuário.
    
    Args:
        client: Cliente do Instagram.
        session_id: Session ID extraído dos cookies do navegador.
        
    Returns:
        True se o login foi bem-sucedido.
    """
    print("🔐 Aplicando session hijacking...")
    
    from urllib.parse import unquote
    
    # Decodificar se estiver URL-encoded
    decoded_session = unquote(session_id)
    
    # Extrair o user_id do session_id
    # Formato: userid:hash:unknown:hash
    parts = decoded_session.split(":")
    user_id = parts[0] if parts else ""
    
    try:
        # Configurar apenas o necessário para autenticação
        client.set_settings({
            "authorization_data": {
                "ds_user_id": user_id,
                "sessionid": decoded_session,
            },
            "cookies": {
                "sessionid": decoded_session,
                "ds_user_id": user_id,
            }
        })
        
        print(f"✅ Sessão configurada para user_id: {user_id}")
        return True
        
    except Exception as e:
        print(f"⚠️ Erro ao configurar sessão: {e}")
        return False


def humanized_delay(min_delay: float = MIN_ACTION_DELAY, 
                    max_delay: float = MAX_ACTION_DELAY) -> None:
    """
    Aplica um delay aleatório para simular comportamento humano.
    
    Args:
        min_delay: Tempo mínimo de espera (segundos).
        max_delay: Tempo máximo de espera (segundos).
    """
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)


def post_login_delay() -> None:
    """Aplica delay após login bem-sucedido."""
    print(f"⏳ Aguardando {POST_LOGIN_DELAY}s após login...")
    time.sleep(POST_LOGIN_DELAY)
