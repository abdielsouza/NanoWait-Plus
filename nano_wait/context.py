"""
NanoWait Execution Context
--------------------------
Gerencia contexto compartilhado entre diferentes operações.

Uso:
    from nano_wait.context import ExecutionContext

    ctx = ExecutionContext()
    ctx.set_timeout(30)
    ctx.set_profile("ci")
    
    wait(2)  # usa contexto atual
"""

import threading
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ExecutionContext:
    """
    Contexto thread-local para execução do NanoWait.
    Permite configuração implícita sem passar parâmetros.
    """
    
    timeout: float = 15.0
    profile: Optional[str] = None
    speed: str | float = "normal"
    verbose: bool = False
    smart: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    _local = threading.local()
    
    @classmethod
    def current(cls) -> "ExecutionContext":
        """Retorna contexto da thread atual."""
        if not hasattr(cls._local, "context"):
            cls._local.context = cls()
        return cls._local.context
    
    @classmethod
    def set_current(cls, context: "ExecutionContext") -> None:
        """Define contexto da thread atual."""
        cls._local.context = context
    
    @classmethod
    def reset(cls) -> None:
        """Reseta contexto para padrão."""
        cls._local.context = cls()
    
    def set_timeout(self, timeout: float) -> "ExecutionContext":
        """Define timeout."""
        self.timeout = timeout
        return self
    
    def set_profile(self, profile: str) -> "ExecutionContext":
        """Define perfil."""
        self.profile = profile
        return self
    
    def set_speed(self, speed: str | float) -> "ExecutionContext":
        """Define velocidade."""
        self.speed = speed
        return self
    
    def set_verbose(self, verbose: bool) -> "ExecutionContext":
        """Define verbose."""
        self.verbose = verbose
        return self
    
    def set_smart(self, smart: bool) -> "ExecutionContext":
        """Define smart mode."""
        self.smart = smart
        return self
    
    def set_metadata(self, key: str, value: Any) -> "ExecutionContext":
        """Define metadata."""
        self.metadata[key] = value
        return self
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Obtém metadata."""
        return self.metadata.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário (para passar como kwargs)."""
        return {
            "timeout": self.timeout,
            "profile": self.profile,
            "speed": self.speed,
            "verbose": self.verbose,
            "smart": self.smart,
        }
    
    def copy(self) -> "ExecutionContext":
        """Retorna cópia do contexto."""
        return ExecutionContext(
            timeout=self.timeout,
            profile=self.profile,
            speed=self.speed,
            verbose=self.verbose,
            smart=self.smart,
            metadata=dict(self.metadata),
        )


class ContextManager:
    """Gerenciador de contexto stack para operações aninhadas."""
    
    def __init__(self):
        self._stack: list[ExecutionContext] = []
    
    def push(self, context: ExecutionContext) -> ExecutionContext:
        """Push de contexto."""
        self._stack.append(context)
        ExecutionContext.set_current(context)
        return context
    
    def pop(self) -> ExecutionContext | None:
        """Pop de contexto."""
        if self._stack:
            context = self._stack.pop()
            if self._stack:
                ExecutionContext.set_current(self._stack[-1])
            else:
                ExecutionContext.reset()
            return context
        return None
    
    def current(self) -> ExecutionContext:
        """Retorna contexto atual."""
        if self._stack:
            return self._stack[-1]
        return ExecutionContext.current()


# Instância global
_context_manager = ContextManager()


def get_context_manager() -> ContextManager:
    """Retorna gerenciador global de contexto."""
    return _context_manager
