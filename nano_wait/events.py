"""
NanoWait Events & Webhooks
---------------------------
Sistema de callbacks e webhooks para eventos de execução.

Uso:
    from nano_wait import wait
    from nano_wait.events import on_wait, on_timeout

    @on_wait("success")
    def log_success(event):
        print(f"✅ Wait succeeded: {event.duration}s")

    @on_timeout()
    def handle_timeout(event):
        print(f"⏱ Timeout after {event.attempts}")

    wait(2, timeout=5)
"""

import threading
from enum import Enum
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


class WaitEventType(Enum):
    """Tipos de eventos do NanoWait."""
    SUCCESS = "success"          # Espera completada com sucesso
    TIMEOUT = "timeout"          # Timeout em operação
    CONDITION_MET = "condition_met"  # Condição verificada com sucesso
    RETRY = "retry"              # Tentativa de retry
    ERROR = "error"              # Erro durante execução
    STARTED = "started"          # Espera iniciada


@dataclass
class WaitEvent:
    """Evento de execução do NanoWait."""
    event_type: WaitEventType
    timestamp: str
    requested_time: Optional[float]
    duration: float
    attempts: int = 0
    success: bool = False
    error: Optional[str] = None
    profile: Optional[str] = None
    speed: Optional[str | float] = None
    cpu_score: Optional[float] = None
    wifi_score: Optional[float] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class EventBus:
    """
    Sistema central de eventos com suporte a subscribers.
    Thread-safe com registro e disparo de eventos.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._subscribers: Dict[WaitEventType, List[Callable]] = {
            event_type: [] for event_type in WaitEventType
        }
        self._global_subscribers: List[Callable] = []  # Listeners para todos os eventos

    def subscribe(
        self,
        event_type: WaitEventType | None,
        callback: Callable[[WaitEvent], None]
    ) -> None:
        """
        Registra um callback para um tipo de evento.
        
        Args:
            event_type: Tipo de evento (None para todos)
            callback: Função a chamar com o evento
        """
        with self._lock:
            if event_type is None:
                self._global_subscribers.append(callback)
            else:
                self._subscribers[event_type].append(callback)

    def unsubscribe(
        self,
        event_type: WaitEventType | None,
        callback: Callable[[WaitEvent], None]
    ) -> None:
        """Remove um callback."""
        with self._lock:
            if event_type is None:
                self._global_subscribers.remove(callback)
            else:
                self._subscribers[event_type].remove(callback)

    def emit(self, event: WaitEvent) -> None:
        """
        Dispara um evento para todos os subscribers.
        
        Args:
            event: Evento a disparar
        """
        with self._lock:
            # Callbacks específicos do tipo
            callbacks = self._subscribers.get(event.event_type, [])
            # Callbacks globais
            callbacks = callbacks + self._global_subscribers

        # Executa fora do lock para evitar deadlock
        for callback in callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"[EventBus] Erro ao executar callback: {e}")

    def clear(self) -> None:
        """Limpa todos os subscribers."""
        with self._lock:
            for event_type in self._subscribers:
                self._subscribers[event_type].clear()
            self._global_subscribers.clear()


# Instância global
_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """Retorna instância global de EventBus."""
    return _event_bus


def on(event_type: WaitEventType | None = None):
    """
    Decorator para registrar callback de evento.
    
    Args:
        event_type: Tipo de evento (None para todos)
        
    Usage:
        @on(WaitEventType.SUCCESS)
        def handle_success(event):
            print(f"Sucesso: {event.duration}s")
    """
    def decorator(func: Callable[[WaitEvent], None]) -> Callable:
        _event_bus.subscribe(event_type, func)
        return func
    return decorator


def on_success():
    """Decorator para evento de sucesso."""
    return on(WaitEventType.SUCCESS)


def on_timeout():
    """Decorator para evento de timeout."""
    return on(WaitEventType.TIMEOUT)


def on_condition_met():
    """Decorator para condição satisfeita."""
    return on(WaitEventType.CONDITION_MET)


def on_retry():
    """Decorator para evento de retry."""
    return on(WaitEventType.RETRY)


def on_error():
    """Decorator para evento de erro."""
    return on(WaitEventType.ERROR)


def on_started():
    """Decorator para evento de início."""
    return on(WaitEventType.STARTED)


def on_any_event():
    """Decorator para qualquer evento."""
    return on(None)


def emit_event(
    event_type: WaitEventType,
    requested_time: Optional[float] = None,
    duration: float = 0.0,
    attempts: int = 0,
    success: bool = False,
    error: Optional[str] = None,
    profile: Optional[str] = None,
    speed: Optional[str | float] = None,
    cpu_score: Optional[float] = None,
    wifi_score: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Dispara um evento.
    
    Args:
        event_type: Tipo de evento
        requested_time: Tempo solicitado
        duration: Duração real
        attempts: Número de tentativas
        success: Se foi bem-sucedido
        error: Mensagem de erro
        profile: Perfil usado
        speed: Velocidade usada
        cpu_score: Score de CPU
        wifi_score: Score de Wi-Fi
        metadata: Dados adicionais
    """
    event = WaitEvent(
        event_type=event_type,
        timestamp=datetime.now().isoformat(),
        requested_time=requested_time,
        duration=duration,
        attempts=attempts,
        success=success,
        error=error,
        profile=profile,
        speed=speed,
        cpu_score=cpu_score,
        wifi_score=wifi_score,
        metadata=metadata or {},
    )
    _event_bus.emit(event)


# Helpers para emissão rápida
def emit_success(duration: float, requested_time: float, **kwargs) -> None:
    """Emite evento de sucesso."""
    emit_event(WaitEventType.SUCCESS, requested_time=requested_time, duration=duration, success=True, **kwargs)


def emit_timeout(attempts: int, **kwargs) -> None:
    """Emite evento de timeout."""
    emit_event(WaitEventType.TIMEOUT, attempts=attempts, success=False, **kwargs)


def emit_error(error: str, **kwargs) -> None:
    """Emite evento de erro."""
    emit_event(WaitEventType.ERROR, error=error, success=False, **kwargs)
