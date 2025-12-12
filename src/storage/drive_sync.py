"""
Sincronização com Google Drive.

Baixa pastas de conteúdo do Google Drive para postagem local.
"""

import io
import os
from pathlib import Path
from typing import List, Optional, Dict, Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from ..core.config import get_config
from ..core.exceptions import DriveError


# Scopes necessários para o Drive
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


class DriveSync:
    """
    Sincronizador com Google Drive.
    
    Baixa pastas de conteúdo do Drive para o diretório local.
    """
    
    def __init__(self, folder_id: Optional[str] = None):
        """
        Inicializa o sincronizador.
        
        Args:
            folder_id: ID da pasta no Drive.
                      Se None, usa o ID da config.
        """
        config = get_config()
        self.folder_id = folder_id or config.drive_folder_id
        self.local_path = config.local_content_path
        self._service = None
    
    def _get_service(self):
        """
        Retorna o serviço autenticado do Drive.
        
        Usa lazy loading para evitar autenticação desnecessária.
        """
        if self._service is None:
            config = get_config()
            credentials_dict = config.get_google_credentials()
            
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=SCOPES
            )
            
            self._service = build("drive", "v3", credentials=credentials)
            print("✅ Conectado ao Google Drive")
        
        return self._service
    
    def list_remote_folders(self) -> List[Dict[str, Any]]:
        """
        Lista as pastas disponíveis no Drive.
        
        Returns:
            Lista de dicts com informações das pastas.
        """
        try:
            service = self._get_service()
            
            # Buscar subpastas da pasta principal
            query = f"'{self.folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            results = service.files().list(
                q=query,
                fields="files(id, name, createdTime, modifiedTime)",
                orderBy="name"
            ).execute()
            
            folders = results.get("files", [])
            print(f"📂 {len(folders)} pasta(s) encontrada(s) no Drive")
            
            return folders
            
        except Exception as e:
            raise DriveError(f"Erro ao listar pastas do Drive: {e}")
    
    def download_folder(self, folder_id: str, folder_name: str) -> Path:
        """
        Baixa uma pasta do Drive.
        
        Args:
            folder_id: ID da pasta no Drive.
            folder_name: Nome para a pasta local.
            
        Returns:
            Path da pasta baixada.
        """
        try:
            service = self._get_service()
            
            # Criar pasta local
            local_folder = self.local_path / folder_name
            local_folder.mkdir(parents=True, exist_ok=True)
            
            # Listar arquivos na pasta
            query = f"'{folder_id}' in parents and trashed=false"
            
            results = service.files().list(
                q=query,
                fields="files(id, name, mimeType)"
            ).execute()
            
            files = results.get("files", [])
            
            for file in files:
                self._download_file(service, file, local_folder)
            
            print(f"✅ Pasta baixada: {folder_name} ({len(files)} arquivo(s))")
            return local_folder
            
        except Exception as e:
            raise DriveError(f"Erro ao baixar pasta: {e}")
    
    def _download_file(self, service, file_info: dict, local_folder: Path) -> None:
        """
        Baixa um arquivo do Drive.
        """
        file_id = file_info["id"]
        file_name = file_info["name"]
        mime_type = file_info.get("mimeType", "")
        
        # Ignorar pastas e Google Docs
        if mime_type == "application/vnd.google-apps.folder":
            return
        
        if mime_type.startswith("application/vnd.google-apps"):
            return
        
        local_path = local_folder / file_name
        
        # Baixar arquivo
        request = service.files().get_media(fileId=file_id)
        
        with io.FileIO(str(local_path), "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        
        print(f"  📥 {file_name}")
    
    def sync(self) -> List[Path]:
        """
        Sincroniza todas as pastas do Drive.
        
        Baixa apenas pastas que não existem localmente.
        
        Returns:
            Lista de paths das pastas baixadas.
        """
        print("🔄 Sincronizando com Google Drive...")
        
        remote_folders = self.list_remote_folders()
        downloaded = []
        
        for folder in remote_folders:
            folder_name = folder["name"]
            local_folder = self.local_path / folder_name
            
            # Verificar se já existe localmente
            if local_folder.exists():
                print(f"  ⏭️ {folder_name} (já existe)")
                continue
            
            # Verificar se já foi postado
            posted_folder = self.local_path / "posted"
            if posted_folder.exists():
                posted_names = [f.name.rsplit("_", 2)[0] for f in posted_folder.iterdir()]
                if folder_name in posted_names:
                    print(f"  ⏭️ {folder_name} (já postado)")
                    continue
            
            # Baixar
            try:
                path = self.download_folder(folder["id"], folder_name)
                downloaded.append(path)
            except Exception as e:
                print(f"  ❌ Erro ao baixar {folder_name}: {e}")
        
        print(f"✅ Sync concluído: {len(downloaded)} nova(s) pasta(s)")
        return downloaded
    
    def get_sync_status(self) -> dict:
        """
        Retorna status da sincronização.
        
        Returns:
            Dict com status.
        """
        try:
            remote = self.list_remote_folders()
            local_folders = [f.name for f in self.local_path.iterdir() 
                           if f.is_dir() and f.name != "posted"]
            
            remote_names = {f["name"] for f in remote}
            local_names = set(local_folders)
            
            pending = remote_names - local_names
            
            return {
                "remote_count": len(remote),
                "local_count": len(local_names),
                "pending_sync": len(pending),
                "pending_names": list(pending)
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "remote_count": 0,
                "local_count": 0,
                "pending_sync": 0
            }


# Instância global
_sync: Optional[DriveSync] = None


def get_drive_sync() -> DriveSync:
    """Retorna o sync singleton."""
    global _sync
    if _sync is None:
        _sync = DriveSync()
    return _sync
