# 🚀 NanoWait v7.1 — Novas Features & Otimizações

> **Edição Plus com novos módulos para produção e monitoramento**

## ✨ O que há de novo?

### 1. **📊 Statistics & Metrics** (`stats.py`)

Rastreie e analise o desempenho das suas esperas:

```python
from nano_wait import wait
from nano_wait.stats import get_stats

# Ativa rastreamento
stats = get_stats()
stats.enable()

# Suas operações
wait(2)
wait(3, smart=True)
wait(lambda: condition(), timeout=5)

# Análise
print(stats.report())
# 📊 NanoWait Execution Statistics
# ==================================================
# Total Executions: 3
# Success Rate: 100.0% (3✓ / 0✗)
#
# ⏱ Timing (seconds):
#   Average: 2.6567
#   Median:  2.5000
#   Min:     2.0012
#   Max:     3.2145
#   StdDev:  0.5234
#
# 📈 Percentiles:
#   P50:     2.5000
#   P95:     3.1234
#   P99:     3.2145

# Estatísticas específicas
print(f"P95: {stats.percentile(95)}s")
print(f"Success rate: {stats.summary().success_rate}%")
```

**Features:**
- 📈 Histórico persistente (7 dias em `~/.nano_wait_stats.json`)
- 📊 Percentis (P50, P95, P99)
- 🎯 Filtragem por perfil
- 💾 Auto-limpeza de dados antigos

---

### 2. **⚙️ Configuration Management** (`config.py`)

Centralize configurações em arquivo:

```yaml
# ~/.nanowait.yml
default_speed: fast
default_profile: ci
default_timeout: 20
auto_smart: false
enable_stats: true
verbose_default: false
log_file: ~/nano_wait.log
```

```python
from nano_wait.config import get_config

config = get_config()
print(config.default_speed)      # "fast"
print(config.default_profile)    # "ci"

# Sobrescrever em runtime
overrides = {"default_speed": "ultra"}
new_config = config.merge(overrides)
```

**Suporta:**
- 📄 `.nanowait.yml` / `.nanowait.yaml`
- 📋 `.nanowait.json`
- 🔍 Busca automática em `~` e diretório atual
- 🔄 Profiles customizados

---

### 3. **🎣 Events & Webhooks** (`events.py`)

Reaja a eventos do NanoWait com callbacks:

```python
from nano_wait import wait
from nano_wait.events import on_success, on_timeout, emit_event

@on_success()
def log_success(event):
    print(f"✅ Sucesso: {event.duration:.3f}s")

@on_timeout()
def handle_timeout(event):
    print(f"⏱ Timeout após {event.attempts} tentativas")

# Seus códigos
try:
    wait(2)
except WaitTimeoutError:
    pass
```

**Tipos de eventos:**
- `SUCCESS` — Espera completada
- `TIMEOUT` — Timeout ocorreu
- `CONDITION_MET` — Condição satisfeita
- `ERROR` — Erro durante execução
- `RETRY` — Tentativa de retry
- `STARTED` — Espera iniciada

```python
from nano_wait.events import (
    on, on_success, on_timeout, on_error, 
    on_any_event, WaitEventType
)

# Escutar qualquer evento
@on_any_event()
def log_all(event):
    print(f"[{event.event_type.value}] {event.duration}s")
```

---

### 4. **🚦 Rate Limiting & Circuit Breaker** (`limiter.py`)

Controle velocidade e falhas em cascata:

#### **Token Bucket** (controle de taxa)
```python
from nano_wait.limiter import RateLimiter
from nano_wait import wait

# 10 requisições por segundo, capacity de 50
limiter = RateLimiter.token_bucket(rate=10, capacity=50)

for i in range(100):
    with limiter:
        wait(0.1)  # Será rate-limited a 10 req/s
```

#### **Sliding Window** (janelas deslizantes)
```python
limiter = RateLimiter.sliding_window(rate=5)  # 5 req/s

with limiter:
    api_call()
```

#### **Circuit Breaker** (falha rápida)
```python
from nano_wait.limiter import CircuitBreaker
from nano_wait import execute

cb = CircuitBreaker(
    failure_threshold=5,      # 5 falhas = abre circuito
    recovery_timeout=60,      # Tenta recuperar após 60s
    success_threshold=2       # 2 sucessos = fecha circuito
)

for i in range(10):
    try:
        with cb:
            result = risky_api_call()
    except WaitTimeoutError:
        print("Circuito aberto, falhando rápido")
        
# Monitorar estado
print(f"Circuito está: {cb.state}")  # CircuitState.OPEN
```

#### **Adaptive Backoff** (backoff exponencial com jitter)
```python
from nano_wait.limiter import AdaptiveBackoff

backoff = AdaptiveBackoff(base_delay=0.1, max_delay=60)

for attempt in range(10):
    try:
        result = api.call()
        backoff.reset()  # Sucesso: reseta
    except Exception:
        delay = backoff.next()  # 0.1s, 0.2s, 0.4s, ...
        wait(delay)
```

---

### 5. **🎛️ Execution Context** (`context.py`)

Implícita configuração thread-local sem parâmetros:

```python
from nano_wait import wait
from nano_wait.context import ExecutionContext

# Define contexto global para thread
ctx = ExecutionContext.current()
ctx.set_timeout(30).set_profile("ci").set_speed("fast")

# Todas as operações usam esse contexto
wait(2)          # usa profile="ci", speed="fast"
wait(lambda: x, timeout=30)

# Contextos em stack (para seções)
ctx_manager = get_context_manager()
new_ctx = ExecutionContext(timeout=5, profile="rpa")
ctx_manager.push(new_ctx)

wait(1)  # Usa novo contexto

ctx_manager.pop()  # Volta ao anterior
wait(1)  # Usa profile="ci" novamente
```

---

## 🔧 Otimizações Core

### Type Hints Melhorados
- ✅ Type hints completos com `Union`, `Optional`, `Protocol`
- ✅ Mypy compliance (strict mode)
- ✅ Melhor IDE autocompletion

### Performance
- ✅ Lazy import de `psutil` e `pywifi` (carregam sob demanda)
- ✅ Cache de contexto com TTL de 2s
- ✅ Debounce em gravação de aprendizado (a cada 5 updates)
- ✅ I/O reduzido em estatísticas

### Error Handling
- ✅ Melhor propagação de exceções
- ✅ Mensagens de erro mais informativas
- ✅ Fallback gracioso em falhas

---

## 📝 Exemplo Completo: Monitoramento de API

```python
from nano_wait import wait, execute
from nano_wait.stats import get_stats
from nano_wait.limiter import CircuitBreaker, AdaptiveBackoff
from nano_wait.events import on_error

# Setup
stats = get_stats()
stats.enable()

cb = CircuitBreaker(failure_threshold=5)
backoff = AdaptiveBackoff()

@on_error()
def log_error(event):
    print(f"❌ Erro em {event.profile}: {event.error}")

# Função com proteção
def fetch_user(user_id: int):
    try:
        with cb:
            result = execute(
                lambda: api.get_user(user_id),
                timeout=10,
                profile="ci"
            )
            if result.success:
                backoff.reset()
                return result.result
            else:
                delay = backoff.next()
                wait(delay)
    except Exception as e:
        print(f"Circuito aberto ou erro: {e}")
        return None

# Monitorar
print(stats.report())
# 📊 NanoWait Execution Statistics
# ==================================================
# Total Executions: 42
# Success Rate: 95.2% (40✓ / 2✗)
```

---

## 🎁 Bonus: Integração com Dashboard (Futuro)

Planejado para v7.2:
- 📊 Web dashboard em tempo real
- 📈 Gráficos de performance
- 🎯 Alertas personalizados
- 💾 Exportação de métricas

---

## 🔄 Compatibilidade

✅ **Retrocompatível** — Todas as v7.0.0 APIs funcionam normalmente

```python
# v7.0.0 — continua funcionando
from nano_wait import wait
wait(2)

# v7.1 — novos recursos adicionados
from nano_wait.stats import get_stats
stats = get_stats()
stats.enable()
wait(2)
print(stats.report())
```

---

## 📦 Instalação

```bash
pip install nano-wait --upgrade
```

---

## 🤝 Contribuindo

Sugestões e PRs são bem-vindas! Veja [CONTRIBUTING.md](CONTRIBUTING.md)

---

**v7.1.0** - Junho 2025 — Made with ❤️
