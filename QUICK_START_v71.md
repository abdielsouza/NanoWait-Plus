# 🚀 NanoWait v7.1 — Guia Rápido

Comece a usar os novos recursos em 5 minutos.

## 📦 Instalação

```bash
pip install nano-wait --upgrade
```

## 📊 1. Statistics (Métricas)

```python
from nano_wait import wait
from nano_wait.stats import get_stats

# Ativa rastreamento
stats = get_stats()
stats.enable()

# Use normalmente
wait(2)
wait(3, smart=True)

# Visualize as métricas
print(stats.report())
# 📊 NanoWait Execution Statistics
# Total Executions: 2
# Success Rate: 100.0%
# Average: 2.5s
# P95: 2.99s
```

---

## ⚙️ 2. Configuration (Arquivo de Config)

**Crie `~/.nanowait.yml`:**
```yaml
default_speed: fast
default_profile: ci
default_timeout: 20
enable_stats: true
```

**Use em seu código:**
```python
from nano_wait.config import get_config

config = get_config()
print(config.default_speed)  # "fast"

# Ou override em runtime
new_config = config.merge({"default_speed": "ultra"})
```

---

## 🎣 3. Events (Callbacks)

```python
from nano_wait import wait, on_success, on_timeout

@on_success()
def my_success_handler(event):
    print(f"✅ Completou em {event.duration:.2f}s")

@on_timeout()
def my_timeout_handler(event):
    print(f"⏱ Timeout após {event.attempts} tentativas")

# Seus códigos
wait(2)
wait(lambda: condition(), timeout=5)
```

---

## 🚦 4. Rate Limiting

```python
from nano_wait import wait
from nano_wait.limiter import RateLimiter, CircuitBreaker

# Limita a 10 requisições por segundo
limiter = RateLimiter.token_bucket(rate=10)

for i in range(100):
    with limiter:
        wait(0.01)

# Proteção contra cascata de falhas
cb = CircuitBreaker(failure_threshold=5)

try:
    with cb:
        result = api.call()
except:
    print("Circuito aberto, falhando rápido")
```

---

## 🎛️ 5. Execution Context

```python
from nano_wait import wait
from nano_wait.context import ExecutionContext

# Configure contexto global
ctx = ExecutionContext.current()
ctx.set_timeout(30).set_profile("ci").set_speed("fast")

# Todas as operações usam esse contexto
wait(2)
wait(lambda: x, timeout=30)
```

---

## 🔗 Caso Integrado: API com Resilience

```python
from nano_wait import execute
from nano_wait.stats import get_stats
from nano_wait.limiter import CircuitBreaker, AdaptiveBackoff
from nano_wait.events import on_error

# Setup
stats = get_stats()
stats.enable()

cb = CircuitBreaker()
backoff = AdaptiveBackoff()

@on_error()
def log_error(event):
    print(f"❌ {event.error}")

# Função resiliente
for attempt in range(10):
    try:
        with cb:
            result = execute(
                lambda: api.get_user(42),
                timeout=10,
                profile="ci"
            )
            if result.success:
                print(result.result)
                backoff.reset()
            else:
                delay = backoff.next()
                wait(delay)
    except Exception as e:
        print(f"Falha: {e}")
        break

# Relatório
print(stats.report())
```

---

## 📚 Mais Informações

- 📄 [NEW_FEATURES.md](NEW_FEATURES.md) — Todas as features
- 📋 [OPTIMIZATION_REPORT.md](OPTIMIZATION_REPORT.md) — Detalhes técnicos
- 🎬 [demo_v71.py](demo_v71.py) — Demo executável
- 🧪 [tests/test_v71_features.py](tests/test_v71_features.py) — Testes

---

**v7.1.0** — Junho 2025
