"""
NanoWait Rate Limiter
---------------------
Implementa padrões de rate limiting: Token Bucket, Sliding Window, e Circuit Breaker.

Uso:
    from nano_wait.limiter import RateLimiter, CircuitBreaker

    # Token Bucket: 10 requisições por segundo
    limiter = RateLimiter.token_bucket(rate=10, capacity=50)
    
    with limiter:
        wait(2)

    # Circuit Breaker: falha rápida após threshold
    cb = CircuitBreaker(failure_threshold=5)
    
    for i in range(10):
        with cb:
            result = api.call()
"""

import threading
import time
from enum import Enum
from typing import Optional
from datetime import datetime, timedelta
from collections import deque


class CircuitState(Enum):
    """Estados do Circuit Breaker."""
    CLOSED = "closed"          # Operação normal
    OPEN = "open"              # Falhas acima do threshold
    HALF_OPEN = "half_open"    # Testando recuperação


class RateLimiter:
    """
    Limitador de taxa com suporte a múltiplas estratégias.
    Thread-safe com capacidade de bursting.
    """

    def __init__(
        self,
        rate: float,
        capacity: float | None = None,
        strategy: str = "token_bucket"
    ):
        """
        Args:
            rate: Requisições por segundo
            capacity: Capacidade máxima de burst (padrão: rate * 2)
            strategy: "token_bucket" ou "sliding_window"
        """
        self.rate = rate
        self.capacity = capacity or (rate * 2)
        self.strategy = strategy
        self._lock = threading.Lock()
        
        # Token bucket
        self._tokens = float(self.capacity)
        self._last_update = time.monotonic()
        
        # Sliding window
        self._requests: deque = deque()

    def acquire(self, tokens: float = 1.0, timeout: float = 0.0) -> bool:
        """
        Tenta adquirir tokens.
        
        Args:
            tokens: Número de tokens desejados
            timeout: Tempo máximo de espera (0 = sem espera)
            
        Returns:
            True se adquiriu, False se timeout
        """
        if self.strategy == "sliding_window":
            return self._acquire_sliding_window(tokens, timeout)
        else:
            return self._acquire_token_bucket(tokens, timeout)

    def _acquire_token_bucket(self, tokens: float, timeout: float) -> bool:
        """Implementação Token Bucket."""
        start_time = time.monotonic()
        
        while True:
            with self._lock:
                # Recarrega tokens baseado em tempo decorrido
                now = time.monotonic()
                elapsed = now - self._last_update
                new_tokens = elapsed * self.rate
                self._tokens = min(self.capacity, self._tokens + new_tokens)
                self._last_update = now
                
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True
            
            if timeout <= 0:
                return False
            
            if (time.monotonic() - start_time) > timeout:
                return False
            
            time.sleep(0.01)  # Backoff pequeno

    def _acquire_sliding_window(self, tokens: float, timeout: float) -> bool:
        """Implementação Sliding Window."""
        start_time = time.monotonic()
        window = 1.0 / self.rate  # Janela em segundos
        
        while True:
            with self._lock:
                now = time.monotonic()
                # Remove requisições fora da janela
                while self._requests and (self._requests[0] < now - window):
                    self._requests.popleft()
                
                if len(self._requests) < self.rate:
                    self._requests.append(now)
                    return True
            
            if timeout <= 0:
                return False
            
            if (time.monotonic() - start_time) > timeout:
                return False
            
            time.sleep(0.01)

    def __enter__(self):
        """Context manager: aguarda por um token."""
        self.acquire(timeout=float('inf'))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @staticmethod
    def token_bucket(rate: float, capacity: Optional[float] = None) -> "RateLimiter":
        """Factory para Token Bucket."""
        return RateLimiter(rate, capacity, "token_bucket")

    @staticmethod
    def sliding_window(rate: float) -> "RateLimiter":
        """Factory para Sliding Window."""
        return RateLimiter(rate, None, "sliding_window")


class CircuitBreaker:
    """
    Implementa padrão Circuit Breaker para falha rápida.
    
    Estados:
    - CLOSED: Normal, requisições passam
    - OPEN: Falhas acima do threshold, requisições rejeitadas
    - HALF_OPEN: Testando recuperação
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
    ):
        """
        Args:
            failure_threshold: Falhas para abrir circuito
            recovery_timeout: Segundos antes de tentar HALF_OPEN
            success_threshold: Sucessos antes de fechar (em HALF_OPEN)
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self._lock = threading.Lock()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None

    @property
    def state(self) -> CircuitState:
        """Retorna estado atual do circuito."""
        return self._state

    def record_success(self) -> None:
        """Registra uma operação bem-sucedida."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
            elif self._state == CircuitState.CLOSED:
                self._failure_count = max(0, self._failure_count - 1)

    def record_failure(self) -> None:
        """Registra uma falha."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN

    def is_open(self) -> bool:
        """Verifica se o circuito está aberto."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                # Tenta transicionar para HALF_OPEN se timeout expirou
                if (
                    self._last_failure_time
                    and (time.time() - self._last_failure_time) >= self.recovery_timeout
                ):
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                    return False
                return True
            return False

    def reset(self) -> None:
        """Reseta o circuito para CLOSED."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None

    def __enter__(self):
        """Context manager: verifica se circuito está aberto."""
        if self.is_open():
            from .exceptions import WaitTimeoutError
            raise WaitTimeoutError(
                f"Circuit breaker is OPEN (failures: {self._failure_count}/{self.failure_threshold})"
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager: registra sucesso ou falha."""
        if exc_type is None:
            self.record_success()
        else:
            self.record_failure()


class AdaptiveBackoff:
    """
    Implementa backoff exponencial e de jitter para retries.
    """

    def __init__(self, base_delay: float = 0.1, max_delay: float = 60.0):
        """
        Args:
            base_delay: Delay inicial em segundos
            max_delay: Delay máximo
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._attempt = 0

    def next(self) -> float:
        """Retorna próximo delay com jitter."""
        import random
        
        # Backoff exponencial: 2^attempt
        delay = self.base_delay * (2 ** self._attempt)
        delay = min(delay, self.max_delay)
        
        # Jitter: ±20%
        jitter = delay * 0.2 * (random.random() - 0.5)
        
        self._attempt += 1
        return max(0, delay + jitter)

    def reset(self) -> None:
        """Reseta tentativas."""
        self._attempt = 0

    def __iter__(self):
        """Iterador infinito de delays."""
        while True:
            yield self.next()
