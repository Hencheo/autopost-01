"""
Scheduler principal do AutoPost.

Gerencia agendamento automático de posts.
"""

import asyncio
from datetime import datetime
from typing import Optional, Callable
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from .time_slots import TimeSlotManager, get_time_manager
from .queue import PostQueue, get_post_queue
from ..storage.local import get_local_storage
from ..storage.state import get_state_manager
from ..storage.drive_sync import get_drive_sync
from ..content.folder_parser import get_folder_parser
from ..content.image_processor import get_image_processor
from ..instagram.poster import get_poster
from ..core.config import get_config
from ..core.exceptions import SchedulerError


class PostScheduler:
    """
    Scheduler de posts do Instagram.
    
    Responsável por:
    - Agendar posts nos horários configurados
    - Executar posts automaticamente
    - Sincronizar com Drive periodicamente
    - Lidar com falhas e retry
    """
    
    def __init__(self):
        """Inicializa o scheduler."""
        config = get_config()
        
        self._scheduler = AsyncIOScheduler()
        self._time_manager = get_time_manager()
        self._queue = get_post_queue()
        self._storage = get_local_storage()
        self._state = get_state_manager()
        self._running = False
        self._timezone = pytz.timezone(config.timezone)
        
        # Callbacks customizados
        self._on_post_success: Optional[Callable] = None
        self._on_post_error: Optional[Callable] = None
    
    def start(self) -> None:
        """
        Inicia o scheduler.
        
        Agenda jobs para cada horário configurado.
        """
        if self._running:
            print("⚠️ Scheduler já está rodando")
            return
        
        # Limpar jobs anteriores
        self._scheduler.remove_all_jobs()
        
        # Agendar posts para cada horário
        for time_str in self._time_manager.times:
            hour, minute = map(int, time_str.split(":"))
            
            trigger = CronTrigger(
                hour=hour,
                minute=minute,
                timezone=self._timezone
            )
            
            self._scheduler.add_job(
                self._execute_scheduled_post,
                trigger=trigger,
                id=f"post_{time_str}",
                name=f"Post às {time_str}",
                replace_existing=True
            )
            
            print(f"📅 Agendado: Post às {time_str}")
        
        # Agendar sync do Drive (a cada 30 min)
        self._scheduler.add_job(
            self._sync_drive,
            trigger=CronTrigger(minute="*/30", timezone=self._timezone),
            id="drive_sync",
            name="Sync Drive",
            replace_existing=True
        )
        
        # Keep-alive para evitar que o Render Free durma (a cada 5 min)
        self._scheduler.add_job(
            self._keep_alive,
            trigger=CronTrigger(minute="*/5", timezone=self._timezone),
            id="keep_alive",
            name="Keep Alive",
            replace_existing=True
        )
        
        # Iniciar scheduler
        self._scheduler.start()
        self._running = True
        
        # Atualizar estado
        self._state.set_scheduler_enabled(True)
        
        next_slot = self._time_manager.format_next_slot()
        print(f"✅ Scheduler iniciado! Próximo post: {next_slot}")
    
    def stop(self) -> None:
        """Para o scheduler."""
        if not self._running:
            return
        
        self._scheduler.shutdown(wait=False)
        self._running = False
        self._state.set_scheduler_enabled(False)
        
        print("🛑 Scheduler parado")
    
    def is_running(self) -> bool:
        """Verifica se está rodando."""
        return self._running
    
    async def _execute_scheduled_post(self) -> None:
        """Executa um post agendado."""
        print(f"\n⏰ [{datetime.now().strftime('%H:%M')}] Executando post agendado...")
        
        try:
            result = await self.post_next()
            
            if result:
                print(f"✅ Post realizado com sucesso!")
                if self._on_post_success:
                    self._on_post_success(result)
            else:
                print("⚠️ Nenhum conteúdo disponível para postar")
                
        except Exception as e:
            print(f"❌ Erro no post agendado: {e}")
            if self._on_post_error:
                self._on_post_error(str(e))
    
    async def _sync_drive(self) -> None:
        """Sincroniza com o Drive."""
        try:
            drive = get_drive_sync()
            downloaded = drive.sync()
            
            if downloaded:
                print(f"📥 {len(downloaded)} nova(s) pasta(s) baixada(s) do Drive")
                
        except Exception as e:
            print(f"⚠️ Erro no sync do Drive: {e}")
    
    async def _keep_alive(self) -> None:
        """Pinga a própria URL para manter o servidor acordado no Render Free."""
        import os
        import httpx
        
        # Pegar URL do ambiente (Render define automaticamente)
        render_url = os.getenv("RENDER_EXTERNAL_URL")
        
        if render_url:
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    response = await client.get(f"{render_url}/")
                    print(f"💓 Keep-alive ping: {response.status_code}")
            except Exception as e:
                # Timeout é esperado às vezes, não é erro crítico
                print(f"💓 Keep-alive enviado (timeout ignorado)")


    
    async def post_next(self) -> Optional[dict]:
        """
        Posta o próximo item da fila.
        
        Returns:
            Dict com resultado ou None se fila vazia.
        """
        # Pegar próxima pasta
        folder = self._queue.dequeue()
        
        if folder is None:
            return None
        
        return await self.post_folder(folder)
    
    async def post_folder(self, folder: Path) -> dict:
        """
        Posta uma pasta específica.
        
        Args:
            folder: Path da pasta.
            
        Returns:
            Dict com resultado.
        """
        print(f"📤 Postando: {folder.name}")
        
        try:
            # Parse da pasta
            parser = get_folder_parser()
            content = parser.parse(folder)
            
            # Processar imagens
            processor = get_image_processor()
            processed_images = processor.process_folder(
                content.slides,
                content.post_type
            )
            
            # Postar
            poster = get_poster()
            
            if content.post_type.value == "story":
                result = poster.post_story(processed_images)
            else:
                result = poster.post_carousel(processed_images, content.caption)
            
            # Marcar como postado
            self._storage.mark_as_posted(folder)
            
            # Salvar no histórico
            post_info = {
                "folder": folder.name,
                "type": content.post_type.value,
                "slides": content.slide_count,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
            self._state.add_to_history(post_info)
            
            return post_info
            
        except Exception as e:
            print(f"❌ Erro ao postar {folder.name}: {e}")
            raise SchedulerError(f"Falha ao postar: {e}")
    
    def post_now(self, folder_name: Optional[str] = None) -> dict:
        """
        Posta imediatamente (síncrono).
        
        Args:
            folder_name: Nome da pasta específica ou None para próxima.
            
        Returns:
            Dict com resultado.
        """
        if folder_name:
            folder = self._storage.get_folder_by_name(folder_name)
            if not folder:
                raise SchedulerError(f"Pasta não encontrada: {folder_name}")
        else:
            folder = self._queue.dequeue()
            if not folder:
                raise SchedulerError("Fila vazia")
        
        # Executar de forma síncrona (sem asyncio)
        return self._post_folder_sync(folder)
    
    def _post_folder_sync(self, folder: Path) -> dict:
        """
        Posta uma pasta de forma síncrona.
        
        Args:
            folder: Path da pasta.
            
        Returns:
            Dict com resultado.
        """
        print(f"📤 Postando: {folder.name}")
        
        try:
            # Parse da pasta
            parser = get_folder_parser()
            content = parser.parse(folder)
            
            # Processar imagens
            processor = get_image_processor()
            processed_images = processor.process_folder(
                content.slides,
                content.post_type
            )
            
            # Postar
            poster = get_poster()
            
            if content.post_type.value == "story":
                result = poster.post_story(processed_images)
            else:
                result = poster.post_carousel(processed_images, content.caption)
            
            # Marcar como postado
            self._storage.mark_as_posted(folder)
            
            # Salvar no histórico
            post_info = {
                "folder": folder.name,
                "type": content.post_type.value,
                "slides": content.slide_count,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
            self._state.add_to_history(post_info)
            
            print(f"✅ Post realizado: {folder.name}")
            return post_info
            
        except Exception as e:
            print(f"❌ Erro ao postar {folder.name}: {e}")
            raise SchedulerError(f"Falha ao postar: {e}")
    
    def update_times(self, times: list) -> None:
        """
        Atualiza os horários de postagem.
        
        Args:
            times: Lista de novos horários.
        """
        self._time_manager.set_slots(times)
        self._state.update_post_times(times)
        
        # Se estiver rodando, reagendar
        if self._running:
            self.stop()
            self.start()
    
    def get_status(self) -> dict:
        """
        Retorna o status atual do scheduler.
        
        Returns:
            Dict com status.
        """
        self._queue.refresh()
        
        return {
            "running": self._running,
            "enabled": self._state.is_scheduler_enabled(),
            "post_times": self._time_manager.times,
            "next_post": self._time_manager.format_next_slot(),
            "queue_size": self._queue.size(),
            "next_folder": self._queue.peek().name if self._queue.peek() else None
        }
    
    def get_queue(self) -> list:
        """Retorna a fila atual."""
        return self._queue.list()
    
    def set_callbacks(self, 
                      on_success: Optional[Callable] = None,
                      on_error: Optional[Callable] = None) -> None:
        """Define callbacks para eventos."""
        self._on_post_success = on_success
        self._on_post_error = on_error


# Instância global
_scheduler: Optional[PostScheduler] = None


def get_scheduler() -> PostScheduler:
    """Retorna o scheduler singleton."""
    global _scheduler
    if _scheduler is None:
        _scheduler = PostScheduler()
    return _scheduler
