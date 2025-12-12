"""
Gerenciamento de horários de postagem.

Calcula próximos horários e valida configurações.
"""

from datetime import datetime, time, timedelta
from typing import List, Optional, Tuple
import pytz

from ..core.config import get_config
from ..core.constants import DEFAULT_POST_TIMES, DEFAULT_TIMEZONE
from ..core.exceptions import SchedulerError


class TimeSlotManager:
    """
    Gerenciador de horários de postagem.
    
    Responsável por:
    - Manter lista de horários configurados
    - Calcular próximo horário de post
    - Validar formato de horários
    """
    
    def __init__(self, times: Optional[List[str]] = None, 
                 timezone: Optional[str] = None):
        """
        Inicializa o gerenciador de horários.
        
        Args:
            times: Lista de horários (ex: ["09:00", "15:00"]).
            timezone: Timezone (ex: "America/Sao_Paulo").
        """
        config = get_config()
        self._times = times or config.post_times or DEFAULT_POST_TIMES
        self._timezone_str = timezone or config.timezone or DEFAULT_TIMEZONE
        self._timezone = pytz.timezone(self._timezone_str)
    
    @property
    def times(self) -> List[str]:
        """Retorna os horários configurados."""
        return self._times.copy()
    
    def set_slots(self, times: List[str]) -> None:
        """
        Define os horários de postagem.
        
        Args:
            times: Lista de horários no formato "HH:MM".
            
        Raises:
            SchedulerError: Se algum horário for inválido.
        """
        # Validar todos
        for t in times:
            if not self.is_valid_time(t):
                raise SchedulerError(f"Horário inválido: {t}")
        
        # Ordenar
        self._times = sorted(times)
    
    def add_slot(self, time_str: str) -> None:
        """
        Adiciona um horário.
        
        Args:
            time_str: Horário no formato "HH:MM".
        """
        if not self.is_valid_time(time_str):
            raise SchedulerError(f"Horário inválido: {time_str}")
        
        if time_str not in self._times:
            self._times.append(time_str)
            self._times.sort()
    
    def remove_slot(self, time_str: str) -> None:
        """
        Remove um horário.
        
        Args:
            time_str: Horário a remover.
        """
        if time_str in self._times:
            self._times.remove(time_str)
    
    def get_next_slot(self) -> Optional[datetime]:
        """
        Calcula o próximo horário de postagem.
        
        Returns:
            DateTime do próximo slot ou None se não houver horários.
        """
        if not self._times:
            return None
        
        now = datetime.now(self._timezone)
        today = now.date()
        
        # Verificar slots de hoje
        for time_str in self._times:
            slot_time = self._parse_time(time_str)
            slot_datetime = self._timezone.localize(
                datetime.combine(today, slot_time)
            )
            
            if slot_datetime > now:
                return slot_datetime
        
        # Se todos os slots de hoje já passaram, pegar o primeiro de amanhã
        tomorrow = today + timedelta(days=1)
        first_slot = self._parse_time(self._times[0])
        
        return self._timezone.localize(
            datetime.combine(tomorrow, first_slot)
        )
    
    def get_all_slots_today(self) -> List[datetime]:
        """
        Retorna todos os slots de hoje.
        
        Returns:
            Lista de datetimes.
        """
        today = datetime.now(self._timezone).date()
        slots = []
        
        for time_str in self._times:
            slot_time = self._parse_time(time_str)
            slot_datetime = self._timezone.localize(
                datetime.combine(today, slot_time)
            )
            slots.append(slot_datetime)
        
        return slots
    
    def is_valid_time(self, time_str: str) -> bool:
        """
        Verifica se um horário é válido.
        
        Args:
            time_str: Horário no formato "HH:MM".
            
        Returns:
            True se válido.
        """
        try:
            self._parse_time(time_str)
            return True
        except (ValueError, AttributeError):
            return False
    
    def _parse_time(self, time_str: str) -> time:
        """
        Converte string para objeto time.
        
        Args:
            time_str: Horário no formato "HH:MM".
            
        Returns:
            Objeto time.
        """
        parts = time_str.strip().split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        
        return time(hour=hour, minute=minute)
    
    def get_time_until_next(self) -> Optional[timedelta]:
        """
        Calcula tempo até o próximo slot.
        
        Returns:
            Timedelta ou None.
        """
        next_slot = self.get_next_slot()
        if next_slot is None:
            return None
        
        now = datetime.now(self._timezone)
        return next_slot - now
    
    def format_next_slot(self) -> str:
        """
        Retorna o próximo slot formatado.
        
        Returns:
            String formatada (ex: "Hoje às 15:00").
        """
        next_slot = self.get_next_slot()
        if next_slot is None:
            return "Nenhum horário configurado"
        
        now = datetime.now(self._timezone)
        
        if next_slot.date() == now.date():
            return f"Hoje às {next_slot.strftime('%H:%M')}"
        elif next_slot.date() == (now + timedelta(days=1)).date():
            return f"Amanhã às {next_slot.strftime('%H:%M')}"
        else:
            return next_slot.strftime("%d/%m às %H:%M")


# Instância global
_time_manager: Optional[TimeSlotManager] = None


def get_time_manager() -> TimeSlotManager:
    """Retorna o time manager singleton."""
    global _time_manager
    if _time_manager is None:
        _time_manager = TimeSlotManager()
    return _time_manager
