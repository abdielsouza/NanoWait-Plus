#!/usr/bin/env python3
"""
NanoWait v7.1 — Demo Completo
Demonstra todos os novos recursos: stats, config, events, limiter, context
"""

from nano_wait import (
    wait, wait_until, execute,
    ExecutionStats, WaitConfig, RateLimiter, CircuitBreaker,
    ExecutionContext, on_success, on_timeout, on_error,
)
from nano_wait.stats import get_stats
from nano_wait.config import get_config
from nano_wait.events import emit_event, WaitEventType
from nano_wait.limiter import AdaptiveBackoff
import time


def demo_1_stats():
    """Demo 1: Rastreamento de métricas"""
    print("\n" + "="*60)
    print("📊 DEMO 1: Statistics & Metrics")
    print("="*60)
    
    stats = get_stats()
    stats.enable()
    
    print("Executando 5 operações com rastreamento...")
    for i in range(5):
        wait(0.1 * (i + 1), verbose=False)
    
    print("\n📈 Relatório de Execução:")
    print(stats.report())
    
    print(f"\n✅ Métrica: P95 = {stats.percentile(95):.3f}s")


def demo_2_config():
    """Demo 2: Gerenciamento de configuração"""
    print("\n" + "="*60)
    print("⚙️  DEMO 2: Configuration Management")
    print("="*60)
    
    # Carrega config (ou usa defaults)
    config = get_config()
    print(f"Config atual:")
    print(f"  - Speed: {config.default_speed}")
    print(f"  - Profile: {config.default_profile}")
    print(f"  - Timeout: {config.default_timeout}s")
    print(f"  - Auto Smart: {config.auto_smart}")
    print(f"  - Stats Habilitado: {config.enable_stats}")
    
    # Merge com overrides
    ci_config = config.merge({
        "default_profile": "ci",
        "default_speed": "fast",
        "verbose_default": True
    })
    
    print(f"\n✅ Config CI:")
    print(f"  - Profile: {ci_config.default_profile}")
    print(f"  - Speed: {ci_config.default_speed}")


def demo_3_events():
    """Demo 3: Events & Webhooks"""
    print("\n" + "="*60)
    print("🎣 DEMO 3: Events & Webhooks")
    print("="*60)
    
    # Register callbacks
    @on_success()
    def on_success_handler(event):
        print(f"  ✅ SUCCESS: {event.duration:.3f}s (pedido: {event.requested_time}s)")
    
    @on_timeout()
    def on_timeout_handler(event):
        print(f"  ⏱ TIMEOUT: {event.attempts} tentativas")
    
    @on_error()
    def on_error_handler(event):
        print(f"  ❌ ERROR: {event.error}")
    
    print("Executando operações com event listeners...")
    
    # Success
    wait(0.5, verbose=False)
    
    # Emite evento customizado
    emit_event(
        WaitEventType.RETRY,
        duration=0.2,
        attempts=3,
        metadata={"reason": "api_throttled"}
    )
    
    print("\n✅ Eventos disparados com sucesso!")


def demo_4_rate_limiting():
    """Demo 4: Rate Limiting & Circuit Breaker"""
    print("\n" + "="*60)
    print("🚦 DEMO 4: Rate Limiting & Circuit Breaker")
    print("="*60)
    
    # Token Bucket
    print("\n🪣 Token Bucket (5 req/s):")
    limiter = RateLimiter.token_bucket(rate=5, capacity=10)
    
    start = time.time()
    acquired = 0
    for i in range(7):
        if limiter.acquire(1.0, timeout=0):
            acquired += 1
            print(f"  ✅ Token {i+1} adquirido")
        else:
            print(f"  ⏳ Token {i+1} pendente")
    print(f"Tempo: {time.time() - start:.2f}s")
    
    # Circuit Breaker
    print("\n⚡ Circuit Breaker (3 falhas para abrir):")
    cb = CircuitBreaker(failure_threshold=3)
    
    for i in range(5):
        try:
            with cb:
                if i < 3:
                    cb.record_failure()
                    print(f"  ❌ Falha {i+1}")
                else:
                    cb.record_success()
                    print(f"  ✅ Sucesso {i+1}")
        except Exception as e:
            print(f"  🔴 Circuito ABERTO: {type(e).__name__}")
    
    print(f"\n✅ Estado final: {cb.state.value}")


def demo_5_backoff():
    """Demo 5: Adaptive Backoff"""
    print("\n" + "="*60)
    print("📈 DEMO 5: Adaptive Backoff")
    print("="*60)
    
    backoff = AdaptiveBackoff(base_delay=0.1, max_delay=2.0)
    
    print("Sequência de backoff exponencial com jitter:")
    total_delay = 0
    for i in range(6):
        delay = backoff.next()
        total_delay += delay
        print(f"  Tentativa {i+1}: aguarda {delay:.3f}s")
    
    print(f"\n✅ Delay total: {total_delay:.3f}s")


def demo_6_context():
    """Demo 6: Execution Context"""
    print("\n" + "="*60)
    print("🎛️  DEMO 6: Execution Context")
    print("="*60)
    
    # Context padrão
    ctx1 = ExecutionContext.current()
    print(f"Context padrão: timeout={ctx1.timeout}s, profile={ctx1.profile}")
    
    # Modifica para CI
    ctx1.set_timeout(30).set_profile("ci").set_speed("fast")
    print(f"Context modificado: timeout={ctx1.timeout}s, profile={ctx1.profile}")
    
    # Metadata
    ctx1.set_metadata("request_id", "req-12345")
    ctx1.set_metadata("user", "admin")
    
    print(f"Metadata: request_id={ctx1.get_metadata('request_id')}, user={ctx1.get_metadata('user')}")
    
    # Cópia
    ctx2 = ctx1.copy()
    ctx2.set_timeout(5)
    print(f"\n✅ Cópia independente: ctx1.timeout={ctx1.timeout}s, ctx2.timeout={ctx2.timeout}s")


def demo_7_integrated():
    """Demo 7: Caso de uso integrado"""
    print("\n" + "="*60)
    print("🚀 DEMO 7: Caso Integrado (API com Resilience)")
    print("="*60)
    
    # Setup
    stats = get_stats()
    stats.enable()
    
    cb = CircuitBreaker(failure_threshold=3)
    backoff = AdaptiveBackoff(base_delay=0.1, max_delay=1.0)
    
    def simulated_api_call():
        """Simula uma chamada de API."""
        import random
        if random.random() < 0.3:  # 30% de falha
            raise Exception("API temporarily unavailable")
        return {"data": "success"}
    
    print("Tentando chamar API com retry inteligente...")
    
    attempt = 0
    max_attempts = 5
    
    while attempt < max_attempts:
        attempt += 1
        try:
            with cb:
                # Executa com timeout
                result = execute(
                    simulated_api_call,
                    timeout=2,
                    profile="testing"
                )
                
                if result.success:
                    print(f"  ✅ Tentativa {attempt}: Sucesso!")
                    backoff.reset()
                    break
                else:
                    cb.record_failure()
                    delay = backoff.next()
                    print(f"  ⏳ Tentativa {attempt}: Falhou, aguardando {delay:.3f}s...")
                    wait(delay)
        
        except Exception as e:
            print(f"  🔴 Tentativa {attempt}: Circuito aberto!")
            break
    
    print(f"\n📊 Resumo:")
    print(stats.report())


def main():
    """Executa todas as demos."""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  🚀 NanoWait v7.1 — Demonstração Completa".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    demos = [
        demo_1_stats,
        demo_2_config,
        demo_3_events,
        demo_4_rate_limiting,
        demo_5_backoff,
        demo_6_context,
        demo_7_integrated,
    ]
    
    for demo in demos:
        try:
            demo()
        except Exception as e:
            print(f"\n❌ Erro em {demo.__name__}: {e}")
    
    print("\n" + "="*60)
    print("✅ Todas as demos completadas com sucesso!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
