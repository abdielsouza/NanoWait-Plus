"""
NanoWait Statistics & Metrics
------------------------------
Coleta e análise de métricas de execução.
Permite rastrear histórico, calcular percentis, ETA e gerar relatórios.

Uso:
    from nano_wait import wait
    from nano_wait.stats import ExecutionStats

    stats = ExecutionStats()
    stats.enable()  # começa a rastrear

    wait(2)
    wait(3)

    print(stats.summary())  # resume estatísticas
    print(stats.percentile(95))  # p95 da duração
"""

import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from statistics import mean, median, stdev


@dataclass
class ExecutionMetric:
    """Métrica individual de uma execução."""
    timestamp: str
    requested_time: float
    actual_time: float
    cpu_score: float
    wifi_score: float
    profile: str
    speed: str | float
    success: bool
    error: Optional[str] = None


@dataclass
class AggregatedStats:
    """Estatísticas agregadas."""
    total_executions: int
    successful: int
    failed: int
    success_rate: float
    avg_time: float
    median_time: float
    min_time: float
    max_time: float
    std_dev: float
    p50: float
    p95: float
    p99: float
    avg_cpu_score: float
    avg_wifi_score: float


class ExecutionStats:
    """
    Coletor de métricas de execução com persistência.
    
    Thread-safe e com arquivo de backup (.nano_wait_stats.json).
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self._lock = threading.Lock()
        self._enabled = False
        self._metrics: List[ExecutionMetric] = []
        self._storage = storage_path or (Path.home() / ".nano_wait_stats.json")
        self._load()

    def enable(self) -> None:
        """Ativa rastreamento de métricas."""
        self._enabled = True

    def disable(self) -> None:
        """Desativa rastreamento de métricas."""
        self._enabled = False

    def record(
        self,
        requested_time: float,
        actual_time: float,
        cpu_score: float,
        wifi_score: float,
        profile: str,
        speed: str | float,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """
        Registra uma métrica de execução.
        
        Args:
            requested_time: Tempo solicitado em segundos
            actual_time: Tempo real de espera
            cpu_score: Score de CPU [0-10]
            wifi_score: Score de Wi-Fi [0-10]
            profile: Nome do perfil usado
            speed: Fator de velocidade
            success: Se a execução foi bem-sucedida
            error: Mensagem de erro (se houver)
        """
        if not self._enabled:
            return

        metric = ExecutionMetric(
            timestamp=datetime.now().isoformat(),
            requested_time=requested_time,
            actual_time=actual_time,
            cpu_score=cpu_score,
            wifi_score=wifi_score,
            profile=profile,
            speed=speed,
            success=success,
            error=error,
        )

        with self._lock:
            self._metrics.append(metric)
            # Limpa métricas antigas (> 7 dias)
            cutoff = datetime.now() - timedelta(days=7)
            self._metrics = [
                m for m in self._metrics
                if datetime.fromisoformat(m.timestamp) > cutoff
            ]
            self._flush()

    def clear(self) -> None:
        """Limpa todas as métricas."""
        with self._lock:
            self._metrics.clear()
            self._flush()

    def summary(self, profile: Optional[str] = None) -> AggregatedStats:
        """
        Retorna um resumo agregado das métricas.
        
        Args:
            profile: Filtra por perfil (opcional)
            
        Returns:
            AggregatedStats com estatísticas consolidadas
        """
        with self._lock:
            metrics = self._metrics
            if profile:
                metrics = [m for m in metrics if m.profile == profile]

        if not metrics:
            return AggregatedStats(
                total_executions=0,
                successful=0,
                failed=0,
                success_rate=0.0,
                avg_time=0.0,
                median_time=0.0,
                min_time=0.0,
                max_time=0.0,
                std_dev=0.0,
                p50=0.0,
                p95=0.0,
                p99=0.0,
                avg_cpu_score=0.0,
                avg_wifi_score=0.0,
            )

        actual_times = [m.actual_time for m in metrics]
        cpu_scores = [m.cpu_score for m in metrics]
        wifi_scores = [m.wifi_score for m in metrics]
        
        successful = sum(1 for m in metrics if m.success)
        failed = len(metrics) - successful

        sorted_times = sorted(actual_times)
        n = len(sorted_times)
        
        p50_idx = int(n * 0.50)
        p95_idx = int(n * 0.95)
        p99_idx = int(n * 0.99)

        return AggregatedStats(
            total_executions=len(metrics),
            successful=successful,
            failed=failed,
            success_rate=successful / len(metrics) * 100 if metrics else 0,
            avg_time=mean(actual_times),
            median_time=median(actual_times),
            min_time=min(actual_times),
            max_time=max(actual_times),
            std_dev=stdev(actual_times) if len(actual_times) > 1 else 0.0,
            p50=sorted_times[p50_idx] if p50_idx < n else 0,
            p95=sorted_times[p95_idx] if p95_idx < n else 0,
            p99=sorted_times[p99_idx] if p99_idx < n else 0,
            avg_cpu_score=mean(cpu_scores),
            avg_wifi_score=mean(wifi_scores),
        )

    def percentile(self, p: int) -> float:
        """
        Calcula percentil de tempo de execução.
        
        Args:
            p: Percentil desejado (ex: 95 para p95)
            
        Returns:
            Valor do percentil em segundos
        """
        with self._lock:
            if not self._metrics:
                return 0.0
            
            actual_times = sorted([m.actual_time for m in self._metrics])
            idx = int(len(actual_times) * (p / 100))
            return actual_times[min(idx, len(actual_times) - 1)]

    def report(self, profile: Optional[str] = None) -> str:
        """
        Gera um relatório formatado em texto.
        
        Args:
            profile: Filtra por perfil (opcional)
            
        Returns:
            String com relatório formatado
        """
        stats = self.summary(profile)
        
        profile_str = f" (Profile: {profile})" if profile else ""
        
        return (
            f"📊 NanoWait Execution Statistics{profile_str}\n"
            f"{'='*50}\n"
            f"Total Executions: {stats.total_executions}\n"
            f"Success Rate: {stats.success_rate:.1f}% "
            f"({stats.successful}✓ / {stats.failed}✗)\n"
            f"\n⏱ Timing (seconds):\n"
            f"  Average: {stats.avg_time:.4f}\n"
            f"  Median:  {stats.median_time:.4f}\n"
            f"  Min:     {stats.min_time:.4f}\n"
            f"  Max:     {stats.max_time:.4f}\n"
            f"  StdDev:  {stats.std_dev:.4f}\n"
            f"\n📈 Percentiles:\n"
            f"  P50:     {stats.p50:.4f}\n"
            f"  P95:     {stats.p95:.4f}\n"
            f"  P99:     {stats.p99:.4f}\n"
            f"\n🖥️  System Averages:\n"
            f"  CPU Score: {stats.avg_cpu_score:.1f}/10\n"
            f"  WiFi Score: {stats.avg_wifi_score:.1f}/10\n"
        )

    def _load(self) -> None:
        """Carrega métricas do arquivo."""
        if not self._storage.exists():
            return
        
        try:
            with open(self._storage, "r") as f:
                data = json.load(f)
                self._metrics = [
                    ExecutionMetric(**m) for m in data.get("metrics", [])
                ]
        except Exception:
            pass  # Falha silenciosa

    def _flush(self) -> None:
        """Salva métricas em disco (deve ser chamado dentro do _lock)."""
        try:
            data = {
                "metrics": [asdict(m) for m in self._metrics],
                "saved_at": datetime.now().isoformat(),
            }
            with open(self._storage, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass  # Falha silenciosa


# Instância global
_stats_instance: Optional[ExecutionStats] = None
_stats_lock = threading.Lock()


def get_stats() -> ExecutionStats:
    """Retorna instância global de ExecutionStats."""
    global _stats_instance
    if _stats_instance is None:
        with _stats_lock:
            if _stats_instance is None:
                _stats_instance = ExecutionStats()
    return _stats_instance
