"""
NanoWait Configuration Management
----------------------------------
Gerencia configurações via arquivo .nanowait.yml ou .nanowait.json

Uso:
    from nano_wait.config import WaitConfig

    config = WaitConfig()
    config.load()  # carrega de ~/.nanowait.yml
    
    # Acesso aos valores
    print(config.default_speed)
    print(config.default_profile)
    print(config.default_timeout)
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from copy import deepcopy


@dataclass
class WaitConfig:
    """Configuração centralizada do NanoWait."""
    
    # Defaults globais
    default_speed: str | float = "normal"
    default_profile: str = "default"
    default_timeout: float = 15.0
    
    # Comportamento
    auto_smart: bool = False  # ativa smart=True por padrão
    enable_stats: bool = True  # habilita rastreamento de métricas
    enable_telemetry: bool = False  # envia telemetria (se implementado)
    verbose_default: bool = False
    
    # Logging
    log_file: Optional[str] = None
    log_level: str = "INFO"
    
    # Performance
    context_cache_ttl: float = 2.0
    wifi_init_lazy: bool = True
    
    # Presets de perfis customizados (avançado)
    custom_profiles: Dict[str, Dict[str, Any]] = None
    
    _config_paths = [
        Path.home() / ".nanowait.yml",
        Path.home() / ".nanowait.yaml",
        Path.home() / ".nanowait.json",
        Path.cwd() / ".nanowait.yml",
        Path.cwd() / ".nanowait.json",
    ]

    def __post_init__(self):
        if self.custom_profiles is None:
            self.custom_profiles = {}

    @classmethod
    def load(cls) -> "WaitConfig":
        """
        Carrega configuração do arquivo (yml ou json).
        
        Busca em ordem:
        1. ~/.nanowait.yml
        2. ~/.nanowait.yaml
        3. ~/.nanowait.json
        4. ./.nanowait.yml
        5. ./.nanowait.json
        
        Returns:
            WaitConfig com valores carregados
        """
        config = cls()
        
        for config_path in cls._config_paths:
            if not config_path.exists():
                continue
            
            try:
                if config_path.suffix == ".yml" or config_path.suffix == ".yaml":
                    with open(config_path) as f:
                        data = yaml.safe_load(f) or {}
                else:  # .json
                    with open(config_path) as f:
                        data = json.load(f)
                
                # Merge com defaults
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                
                return config
            except Exception as e:
                print(f"[WaitConfig] Erro ao carregar {config_path}: {e}")
                continue
        
        return config

    def save(self, path: Optional[Path] = None) -> None:
        """
        Salva configuração em arquivo.
        
        Args:
            path: Caminho do arquivo (padrão: ~/.nanowait.yml)
        """
        save_path = path or (Path.home() / ".nanowait.yml")
        
        try:
            data = asdict(self)
            
            if save_path.suffix in (".yml", ".yaml"):
                with open(save_path, "w") as f:
                    yaml.dump(data, f, default_flow_style=False)
            else:  # .json
                with open(save_path, "w") as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[WaitConfig] Erro ao salvar {save_path}: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Retorna configuração como dicionário."""
        return asdict(self)

    def merge(self, overrides: Dict[str, Any]) -> "WaitConfig":
        """
        Retorna nova configuração com valores sobrescrevidos.
        
        Args:
            overrides: Dicionário com valores a sobrescrever
            
        Returns:
            Nova instância de WaitConfig
        """
        current = asdict(self)
        current.update(overrides)
        return WaitConfig(**current)

    def __repr__(self) -> str:
        return f"WaitConfig({asdict(self)})"


# Instância global
_global_config: Optional[WaitConfig] = None


def get_config() -> WaitConfig:
    """Retorna instância global de WaitConfig."""
    global _global_config
    if _global_config is None:
        _global_config = WaitConfig.load()
    return _global_config


def set_config(config: WaitConfig) -> None:
    """Define instância global de WaitConfig."""
    global _global_config
    _global_config = config


def reset_config() -> None:
    """Reseta para configuração padrão."""
    global _global_config
    _global_config = None
