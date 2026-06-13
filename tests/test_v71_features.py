"""
NanoWait v7.1 — Tests for new modules
Tests básicos para stats, config, events, limiter, context
"""

import time
import json
from pathlib import Path
from tempfile import TemporaryDirectory

# Tests para stats.py
def test_execution_stats():
    from nano_wait.stats import ExecutionStats
    
    with TemporaryDirectory() as tmpdir:
        stats = ExecutionStats(Path(tmpdir) / "stats.json")
        stats.enable()
        
        # Registra métricas
        stats.record(
            requested_time=2.0,
            actual_time=2.05,
            cpu_score=5.5,
            wifi_score=8.0,
            profile="testing",
            speed="normal",
            success=True
        )
        
        stats.record(
            requested_time=3.0,
            actual_time=3.1,
            cpu_score=4.0,
            wifi_score=7.5,
            profile="testing",
            speed="fast",
            success=True
        )
        
        # Verifica agregação
        summary = stats.summary()
        assert summary.total_executions == 2
        assert summary.successful == 2
        assert summary.success_rate == 100.0
        assert 2.0 <= summary.avg_time <= 3.1
        
        # Verifica percentis
        p50 = stats.percentile(50)
        assert 2.0 <= p50 <= 3.1
        
        # Verifica relatório
        report = stats.report()
        assert "NanoWait Execution Statistics" in report
        
        print("✅ test_execution_stats passed")


# Tests para config.py
def test_wait_config():
    from nano_wait.config import WaitConfig, get_config, set_config, reset_config
    
    # Test default config
    config = WaitConfig()
    assert config.default_speed == "normal"
    assert config.default_timeout == 15.0
    
    # Test merge
    new_config = config.merge({"default_speed": "fast"})
    assert new_config.default_speed == "fast"
    assert config.default_speed == "normal"  # original não muda
    
    # Test to_dict
    config_dict = config.to_dict()
    assert "default_speed" in config_dict
    
    # Test global config
    test_config = WaitConfig(default_speed="ultra")
    set_config(test_config)
    assert get_config().default_speed == "ultra"
    
    reset_config()
    assert get_config().default_speed == "normal"  # voltou ao padrão
    
    print("✅ test_wait_config passed")


# Tests para events.py
def test_event_bus():
    from nano_wait.events import (
        get_event_bus, WaitEvent, WaitEventType, emit_event, on_success
    )
    
    bus = get_event_bus()
    bus.clear()  # Limpa subscribers
    
    results = []
    
    @on_success()
    def handle_success(event: WaitEvent):
        results.append(event)
    
    # Emite evento
    emit_event(
        WaitEventType.SUCCESS,
        requested_time=2.0,
        duration=2.05,
        success=True
    )
    
    # Aguarda processamento
    time.sleep(0.1)
    
    assert len(results) == 1
    assert results[0].event_type == WaitEventType.SUCCESS
    assert results[0].duration == 2.05
    
    bus.clear()
    print("✅ test_event_bus passed")


# Tests para limiter.py
def test_rate_limiter():
    from nano_wait.limiter import RateLimiter
    
    # Test token bucket
    limiter = RateLimiter.token_bucket(rate=10, capacity=10)
    
    start = time.perf_counter()
    success_count = 0
    
    # Tenta adquirir 10 tokens (deve suceder imediatamente)
    for _ in range(10):
        if limiter.acquire(1.0, timeout=0):
            success_count += 1
    
    elapsed = time.perf_counter() - start
    assert success_count == 10
    assert elapsed < 0.1  # Deve ser rápido (tokens disponíveis)
    
    # Próxima tentativa deve falhar (sem tokens)
    assert not limiter.acquire(1.0, timeout=0)
    
    print("✅ test_rate_limiter passed")


def test_circuit_breaker():
    from nano_wait.limiter import CircuitBreaker
    from nano_wait.exceptions import WaitTimeoutError
    
    cb = CircuitBreaker(failure_threshold=3)
    
    # Registra 3 falhas
    for _ in range(3):
        cb.record_failure()
    
    # Circuito deve estar aberto
    assert cb.is_open()
    
    # Tentar usar deve lançar exceção
    try:
        with cb:
            pass
        assert False, "Deveria ter lançado exceção"
    except WaitTimeoutError:
        pass
    
    # Reset
    cb.reset()
    assert not cb.is_open()
    
    print("✅ test_circuit_breaker passed")


def test_adaptive_backoff():
    from nano_wait.limiter import AdaptiveBackoff
    
    backoff = AdaptiveBackoff(base_delay=0.1, max_delay=1.0)
    
    # Verifica sequência de backoff
    delays = [backoff.next() for _ in range(5)]
    
    # Deve crescer exponencialmente
    assert delays[0] < delays[1] < delays[2]
    
    # Nenhum deve ultrapassar max_delay
    assert all(d <= 1.0 for d in delays)
    
    print("✅ test_adaptive_backoff passed")


# Tests para context.py
def test_execution_context():
    from nano_wait.context import ExecutionContext
    
    # Test current context
    ctx = ExecutionContext.current()
    assert ctx.timeout == 15.0
    
    # Test fluent API
    ctx.set_timeout(30).set_profile("ci").set_speed("fast")
    assert ctx.timeout == 30
    assert ctx.profile == "ci"
    assert ctx.speed == "fast"
    
    # Test metadata
    ctx.set_metadata("request_id", "abc123")
    assert ctx.get_metadata("request_id") == "abc123"
    
    # Test copy
    ctx2 = ctx.copy()
    ctx2.set_timeout(60)
    assert ctx.timeout == 30  # original não muda
    assert ctx2.timeout == 60
    
    print("✅ test_execution_context passed")


def test_context_manager():
    from nano_wait.context import ExecutionContext, ContextManager
    
    manager = ContextManager()
    
    # Test push/pop
    ctx1 = ExecutionContext(timeout=10, profile="ci")
    manager.push(ctx1)
    
    ctx2 = ExecutionContext(timeout=20, profile="rpa")
    manager.push(ctx2)
    
    # Deve retornar o mais recente
    assert manager.current().timeout == 20
    
    # Pop
    manager.pop()
    assert manager.current().timeout == 10
    
    manager.pop()
    
    print("✅ test_context_manager passed")


# Suite de testes
def run_all_tests():
    """Executa todos os testes."""
    print("🧪 Executando testes da v7.1...")
    print()
    
    tests = [
        test_execution_stats,
        test_wait_config,
        test_event_bus,
        test_rate_limiter,
        test_circuit_breaker,
        test_adaptive_backoff,
        test_execution_context,
        test_context_manager,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
    
    print()
    print(f"{'='*50}")
    print(f"📊 Resultados: {passed} ✅ | {failed} ❌")
    print(f"{'='*50}")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
