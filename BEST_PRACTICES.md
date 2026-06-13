# 🎯 NanoWait v7.1 — Boas Práticas

Orientações para usar os novos módulos de forma eficaz.

---

## 📊 Stats Module

### ✅ Boas Práticas

**1. Ativa stats na inicialização da aplicação**
```python
from nano_wait.stats import get_stats

# No início da aplicação
stats = get_stats()
stats.enable()
```

**2. Limpa stats periodicamente em longa execução**
```python
if total_executions > 100000:
    stats.clear()
    stats.enable()
```

**3. Usa profiles para análise segmentada**
```python
# Armazena por perfil
for profile in ["ci", "testing", "rpa"]:
    summary = stats.summary(profile=profile)
    print(f"{profile}: {summary.success_rate}%")
```

### ❌ Evitar

**Não desabilita stats para "performance"**
- O overhead é negligenciável (~0.1%)
- Benefício de observabilidade supera o custo

**Não lê stats a cada operação**
- Stats é para análise posterior, não real-time
- Use eventos se precisa de callbacks em tempo real

---

## ⚙️ Config Module

### ✅ Boas Práticas

**1. Cria config padrão no projeto**
```bash
# ~/.nanowait.yml
default_profile: ci
default_timeout: 30
enable_stats: true
```

**2. Override para ambiente específico**
```python
import os
from nano_wait.config import get_config

config = get_config()

# Aplica overrides de CI/CD
if os.getenv("CI") == "true":
    config = config.merge({
        "default_profile": "ci",
        "default_speed": "ultra"
    })
```

**3. Valida config ao iniciar**
```python
from nano_wait.config import get_config

config = get_config()
assert config.default_timeout > 0, "Invalid timeout"
```

### ❌ Evitar

**Não hardcoda valores de configuração**
- Use arquivo config ou variáveis de ambiente

**Não modifica config global frequentemente**
- Config deve ser estável durante execução

---

## 🎣 Events Module

### ✅ Boas Práticas

**1. Registra handlers essenciais apenas**
```python
from nano_wait import on_error, on_timeout

@on_error()
def log_error(event):
    logger.error(f"Erro: {event.error}", extra=event.metadata)

@on_timeout()
def on_timeout(event):
    metrics.increment("wait.timeout", tags=[f"profile:{event.profile}"])
```

**2. Handlers devem ser rápidos (< 100ms)**
```python
@on_success()
def handler(event):
    # ✅ Bom: apenas log e métrica
    logger.debug(f"Done: {event.duration}s")
    
    # ❌ Ruim: chamada de API
    api.notify(event)  # Bloqueia callback
```

**3. Usa metadata para contexto**
```python
emit_event(
    WaitEventType.RETRY,
    duration=0.5,
    metadata={
        "endpoint": "/api/users",
        "user_id": 123,
        "retry_count": 2
    }
)
```

### ❌ Evitar

**Não faz processamento pesado em eventos**
- Eventos devem ser leves e rápidos

**Não lança exceções em handlers**
- Exceções em handlers são silenciadas
- Use try/except dentro do handler

---

## 🚦 Limiter Module

### ✅ Boas Práticas

**1. Token Bucket para APIs**
```python
from nano_wait.limiter import RateLimiter

# 100 requisições por segundo, capacity para bursts
limiter = RateLimiter.token_bucket(rate=100, capacity=200)

for api_call in api_calls:
    with limiter:
        response = api_call()
```

**2. Circuit Breaker com fallback**
```python
from nano_wait.limiter import CircuitBreaker

cb = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

for i in range(max_retries):
    try:
        with cb:
            result = critical_operation()
        return result
    except WaitTimeoutError:
        # Circuito aberto, usa fallback
        return fallback_value
```

**3. Backoff com jitter para retry**
```python
from nano_wait.limiter import AdaptiveBackoff
from nano_wait import wait

backoff = AdaptiveBackoff(base_delay=0.1, max_delay=30)

for attempt in range(10):
    try:
        result = operation()
        break
    except Exception:
        delay = backoff.next()
        wait(delay)
```

### ❌ Evitar

**Não trata token bucket como fila**
- Aceita ou rejeita, não espera indefinidamente
- Timeout=0 para non-blocking, timeout>0 para blocking

**Não reseta backoff durante tentativas**
- Reset apenas após sucesso

---

## 🎛️ Context Module

### ✅ Boas Práticas

**1. Define contexto no início de thread**
```python
from nano_wait.context import ExecutionContext

def worker():
    ctx = ExecutionContext.current()
    ctx.set_profile("rpa").set_timeout(60)
    
    # Todas as operações herdam contexto
    for task in tasks:
        process_task(task)

from threading import Thread
Thread(target=worker).start()
```

**2. Herança implícita em funções**
```python
from nano_wait import wait
from nano_wait.context import ExecutionContext

# Setup uma vez
ctx = ExecutionContext.current()
ctx.set_profile("ci")

def expensive_operation():
    # Herda profile="ci" do contexto
    wait(2)
    do_something()

expensive_operation()  # Já tem profile="ci"
```

**3. Stack para seções aninhadas**
```python
from nano_wait.context import ContextManager, ExecutionContext

mgr = ContextManager()

# Contexto geral
ctx1 = ExecutionContext(timeout=30, profile="default")
mgr.push(ctx1)

def sensitive_section():
    # Override local
    ctx2 = ExecutionContext(timeout=5, profile="safe")
    mgr.push(ctx2)
    
    do_critical_work()
    
    mgr.pop()  # volta a ctx1

sensitive_section()
```

### ❌ Evitar

**Não passa contexto explicitamente**
- Use thread-local storage implícito

**Não aninha contextos demais (> 3 níveis)**
- Dificulta rastreamento

---

## 🏗️ Arquitetura: Integrando Tudo

### Exemplo Produção-Ready

```python
import logging
from nano_wait import wait, execute
from nano_wait.stats import get_stats
from nano_wait.config import get_config
from nano_wait.limiter import RateLimiter, CircuitBreaker, AdaptiveBackoff
from nano_wait.context import ExecutionContext
from nano_wait.events import on_error, on_success

# Logger
logger = logging.getLogger(__name__)

# Setup
def setup():
    # Config
    config = get_config()
    logger.info(f"Profile: {config.default_profile}")
    
    # Stats
    stats = get_stats()
    stats.enable()
    
    # Events
    @on_error()
    def log_error(event):
        logger.error(f"Error: {event.error}", extra=event.metadata)
    
    @on_success()
    def log_success(event):
        logger.debug(f"Success: {event.duration:.3f}s")
    
    # Context
    ctx = ExecutionContext.current()
    ctx.set_profile(config.default_profile)
    ctx.set_timeout(config.default_timeout)

# Usar
def fetch_data_resilient(url, max_retries=5):
    limiter = RateLimiter.token_bucket(rate=10)
    cb = CircuitBreaker(failure_threshold=3)
    backoff = AdaptiveBackoff(base_delay=0.5)
    
    for attempt in range(max_retries):
        try:
            with limiter:
                with cb:
                    result = execute(
                        lambda: requests.get(url),
                        timeout=10,
                        profile="ci"
                    )
                    if result.success:
                        backoff.reset()
                        return result.result
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            delay = backoff.next()
            wait(delay)
    
    raise Exception(f"Failed after {max_retries} attempts")

# Main
if __name__ == "__main__":
    setup()
    data = fetch_data_resilient("https://api.example.com/data")
```

---

## 📈 Metrics para Monitoramento

Colete essas métricas em produção:

```python
from nano_wait.stats import get_stats

stats = get_stats()
summary = stats.summary()

# Enviar para APM/Prometheus
metrics = {
    "nano_wait.executions.total": summary.total_executions,
    "nano_wait.executions.success": summary.successful,
    "nano_wait.executions.failed": summary.failed,
    "nano_wait.duration.avg": summary.avg_time,
    "nano_wait.duration.p95": summary.p95,
    "nano_wait.duration.p99": summary.p99,
    "nano_wait.cpu_score.avg": summary.avg_cpu_score,
    "nano_wait.wifi_score.avg": summary.avg_wifi_score,
}

for name, value in metrics.items():
    send_to_monitoring(name, value)
```

---

## 🧪 Testing com Novos Módulos

```python
from nano_wait import wait
from nano_wait.stats import ExecutionStats
from nano_wait.limiter import CircuitBreaker
from pathlib import Path
from tempfile import TemporaryDirectory

def test_with_stats():
    with TemporaryDirectory() as tmpdir:
        stats = ExecutionStats(Path(tmpdir) / "stats.json")
        stats.enable()
        
        wait(0.1)
        
        summary = stats.summary()
        assert summary.total_executions == 1
        assert summary.success_rate == 100.0

def test_circuit_breaker():
    cb = CircuitBreaker(failure_threshold=3)
    
    for i in range(3):
        cb.record_failure()
    
    assert cb.is_open()

def test_with_context():
    from nano_wait.context import ExecutionContext
    
    ctx = ExecutionContext.current()
    ctx.set_timeout(10)
    
    assert ctx.timeout == 10
```

---

## 📞 Debugging

### Circuit Breaker está aberto?
```python
from nano_wait.limiter import CircuitBreaker

cb = CircuitBreaker()
print(f"Estado: {cb.state}")
print(f"Falhas: {cb._failure_count}")
print(f"Está aberto: {cb.is_open()}")

cb.reset()  # Force reset se necessário
```

### Config não está sendo carregada?
```python
from nano_wait.config import get_config, reset_config

config = get_config()
print(f"Arquivo procurado em:")
print(f"  - ~/.nanowait.yml")
print(f"  - ~/.nanowait.json")
print(f"  - ./.nanowait.yml")
print(f"  - ./.nanowait.json")

# Força reload
reset_config()
```

### Stats vazio?
```python
from nano_wait.stats import get_stats

stats = get_stats()
print(f"Habilitado: {stats._enabled}")
print(f"Total métricas: {len(stats._metrics)}")
```

---

**v7.1.0** — Junho 2025
