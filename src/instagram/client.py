"""
Cliente Singleton do Instagram.

Gerencia a conexão única com o Instagram usando instagrapi.
"""

from typing import Optional
from instagrapi import Client

from ..core.config import get_config, reload_config, Config
from ..core.exceptions import LoginError, InstagramError
from .auth import (
    SessionManager,
    apply_session_hijack,
    humanized_delay,
    post_login_delay,
    with_session_retry
)


class InstagramClient:
    """
    Cliente Singleton para interação com o Instagram.
    
    Garante que apenas uma instância do cliente existe,
    evitando múltiplos logins e possíveis bloqueios.
    """
    
    _instance: Optional["InstagramClient"] = None
    _client: Optional[Client] = None
    _logged_in: bool = False
    
    def __new__(cls):
        """Implementa padrão Singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa o cliente (apenas na primeira vez)."""
        if self._client is None:
            self._client = Client()
            self._session_manager = SessionManager()
            self._config = get_config()
            self._setup_client()
    
    def _setup_client(self) -> None:
        """Configura o cliente com delays e settings padrão."""
        # Configurações para evitar detecção
        self._client.delay_range = [2, 5]  # Delay entre requisições
        
        # Tentar carregar sessão existente
        if self._session_manager.has_session():
            self._session_manager.load_session(self._client)
    
    @property
    def client(self) -> Client:
        """Retorna o cliente instagrapi subjacente."""
        return self._client
    
    def login(self, force: bool = False) -> bool:
        """
        Realiza login no Instagram.
        
        Prioriza username/password (mais estável para servidores).
        Session hijacking é usado apenas se credenciais não estiverem configuradas.
        
        Args:
            force: Se True, força novo login mesmo se já logado.
            
        Returns:
            True se o login foi bem-sucedido.
            
        Raises:
            LoginError: Se o login falhar.
        """
        if self._logged_in and not force:
            print("✅ Já está logado.")
            return True
        
        try:
            # Prioridade 1: Sessão salva (evita múltiplos logins)
            if self._session_manager.has_session() and not force:
                if self._try_relogin():
                    return True
                print("⚠️ Sessão salva inválida, tentando login fresh...")
            
            # Prioridade 2: Username/Password (mais confiável para servidores)
            if self._config.instagram_username and self._config.instagram_password:
                print("🔑 Usando login com username/password...")
                return self._login_with_credentials()
            
            # Prioridade 3: Session Hijacking (fallback)
            if self._config.instagram_session_id:
                print("🔐 Usando session hijacking como fallback...")
                return self._login_with_session()
            
            raise LoginError(
                "Nenhum método de login configurado. "
                "Configure INSTAGRAM_USERNAME/PASSWORD ou INSTAGRAM_SESSION_ID."
            )
            
        except Exception as e:
            raise LoginError(f"Falha no login: {e}")
    
    def _login_with_session(self) -> bool:
        """
        Faz login usando session hijacking.
        
        Returns:
            True se bem-sucedido.
        """
        print("🔐 Tentando login com session hijacking...")
        
        success = apply_session_hijack(self._client, self._config.instagram_session_id)
        
        if success:
            # Validar se a sessão funciona
            try:
                user_info = self._client.account_info()
                print(f"✅ Logado como: {user_info.username}")
                self._logged_in = True
                self._session_manager.save_session(self._client)
                post_login_delay()
                return True
            except Exception as e:
                print(f"⚠️ Validação falhou após session hijacking: {e}")
                
                # Verificar se temos credenciais para fallback
                if not self._config.instagram_username or not self._config.instagram_password:
                    raise LoginError(
                        "Sessão do Instagram expirada ou inválida. "
                        "Por favor, renove o INSTAGRAM_SESSION_ID no .env "
                        "extraindo um novo sessionid dos cookies do seu navegador."
                    )
        else:
            # Session hijacking falhou completamente
            if not self._config.instagram_username or not self._config.instagram_password:
                raise LoginError(
                    "Falha ao aplicar session hijacking. "
                    "Verifique se o INSTAGRAM_SESSION_ID está correto no .env."
                )
        
        # Fallback para login com credenciais (só se tiverem sido configuradas)
        return self._login_with_credentials()
    
    def _try_relogin(self) -> bool:
        """
        Tenta relogar usando sessão salva.
        
        Returns:
            True se a sessão ainda é válida.
        """
        print("🔄 Tentando relogar com sessão salva...")
        
        try:
            user_info = self._client.account_info()
            print(f"✅ Sessão válida - Logado como: {user_info.username}")
            self._logged_in = True
            return True
        except Exception:
            print("⚠️ Sessão expirada, fazendo login normal...")
            return False
    
    def _login_with_credentials(self) -> bool:
        """
        Faz login com username e password.
        
        Returns:
            True se bem-sucedido.
        """
        if not self._config.instagram_username or not self._config.instagram_password:
            raise LoginError("Username e password não configurados")
        
        print(f"🔑 Fazendo login como: {self._config.instagram_username}")
        
        humanized_delay()
        
        self._client.login(
            self._config.instagram_username,
            self._config.instagram_password
        )
        
        self._logged_in = True
        self._session_manager.save_session(self._client)
        post_login_delay()
        
        print("✅ Login realizado com sucesso!")
        return True
    
    def logout(self) -> None:
        """Faz logout do Instagram."""
        if self._logged_in:
            try:
                self._client.logout()
            except Exception:
                pass
            self._logged_in = False
            print("👋 Logout realizado.")
    
    def force_relogin(self) -> bool:
        """
        Força um novo login, invalidando a sessão atual.
        
        Usado quando a sessão expira durante uma operação.
        
        Returns:
            True se o re-login foi bem-sucedido.
        """
        print("🔄 Forçando re-login...")
        
        # Resetar estado
        self._logged_in = False
        
        # Recarregar configuração (caso session_id tenha sido atualizado)
        self._config = reload_config()
        
        # Limpar sessão antiga
        self._session_manager.clear_session()
        
        # Criar novo cliente para evitar estado corrompido
        self._client = Client()
        self._client.delay_range = [2, 5]
        
        # Tentar login novamente
        return self.login(force=True)
    
    def reset_session_state(self) -> None:
        """
        Reseta apenas o estado de login sem limpar sessão.
        
        Útil quando você sabe que a sessão expirou.
        """
        self._logged_in = False
        print("⚠️ Estado de sessão resetado")
    
    def is_logged_in(self) -> bool:
        """
        Verifica se está logado.
        
        Faz uma chamada real à API para validar.
        
        Returns:
            True se está logado e a sessão é válida.
        """
        if not self._logged_in:
            return False
        
        try:
            self._client.account_info()
            return True
        except Exception:
            self._logged_in = False
            return False
    
    def get_username(self) -> Optional[str]:
        """
        Retorna o username da conta logada.
        
        Returns:
            Username ou None se não estiver logado.
        """
        if not self.is_logged_in():
            return None
        
        try:
            info = self._client.account_info()
            return info.username
        except Exception:
            return None


# Função utilitária para obter o cliente
def get_instagram_client() -> InstagramClient:
    """
    Retorna a instância singleton do cliente Instagram.
    
    Returns:
        InstagramClient singleton.
    """
    return InstagramClient()
