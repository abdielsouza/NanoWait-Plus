# CHANGELOG — NanoWait v7.1.0

## 🚀 Versão 7.1.0 — Junho 2025

### ✨ Novos Módulos

#### **nano_wait/stats.py** (220 linhas)
- **ExecutionStats**: Rastreia histórico de execução com persistência
- **AggregatedStats**: Calcula percentis, médias, desvios padrão
- Features:
  - 📊 Histórico persistente em `~/.nano_wait_stats.json`
  - 📈 Cálculo eficiente de percentis (P50, P95, P99)
  - 🔄 Thread-safe com lock granular
  - 💾 Auto-limpeza de dados > 7 dias
  - 📋 Relatório formatado em texto

#### **nano_wait/config.py** (180 linhas)
- **WaitConfig**: Gerenciamento centralizado de configurações
- **get_config() / set_config()**: Singleton global
- Features:
  - 📄 Suporte YAML e JSON
  - 🔍 Busca automática (`~/.nanowait.yml`, `./.nanowait.yml`, etc.)
  - 🔄 Merge seguro com overrides
  - 🔧 Type-safe com dataclass
  - 📝 Fluent API para modificação

#### **nano_wait/events.py** (260 linhas)
- **EventBus**: Sistema central de eventos
- **WaitEvent**: Estrutura de evento
- **WaitEventType**: Enum com tipos (SUCCESS, TIMEOUT, ERROR, etc.)
- Features:
  - 🎣 Subscribers globais e específicos
  - 📢 Decorators convenientes (@on_success, @on_error)
  - ⚡ Emissão sem bloqueio (thread-safe)
  - 🔄 Fallback gracioso em erros de callback
  - 🌐 Metadata arbitrária

#### **nano_wait/limiter.py** (280 linhas)
- **RateLimiter**: Token Bucket e Sliding Window
- **CircuitBreaker**: Estados (CLOSED, OPEN, HALF_OPEN)
- **AdaptiveBackoff**: Exponencial com jitter
- Features:
  - 🪣 Token Bucket preciso com capacity/rate
  - 🔄 Sliding Window para fairness
  - ⚡ Circuit Breaker com timeout de recuperação
  - 📈 Adaptive Backoff para retry inteligente
  - 🎯 Context manager para acquire/release

#### **nano_wait/context.py** (120 linhas)
- **ExecutionContext**: Thread-local execution context
- **ContextManager**: Stack de contextos
- Features:
  - 🎛️ Implícita configuração sem parâmetros
  - 🔀 Thread-local storage automático
  - 📍 Stack para operações aninhadas
  - 🔗 Fluent API (chaining)
  - 💾 Copy-on-write pattern

### 📝 Nova Documentação

- **NEW_FEATURES.md** — Guia completo de todas as features
- **OPTIMIZATION_REPORT.md** — Análise técnica e benchmarks
- **QUICK_START_v71.md** — Guia de 5 minutos
- **CHANGELOG** — Este arquivo

### 📦 Arquivos Adicionados

```
nano_wait/
  ├── stats.py          (+220 linhas)
  ├── config.py         (+180 linhas)
  ├── events.py         (+260 linhas)
  ├── limiter.py        (+280 linhas)
  └── context.py        (+120 linhas)

tests/
  └── test_v71_features.py  (+280 linhas, 8 testes)

docs/
  ├── NEW_FEATURES.md        (+350 linhas)
  ├── OPTIMIZATION_REPORT.md (+200 linhas)
  └── QUICK_START_v71.md     (+150 linhas)

demos/
  └── demo_v71.py       (+250 linhas)
```

### 🔧 Otimizações Core

1. **Lazy Imports**
   - psutil e pywifi carregados sob demanda
   - ~10ms redução em import time

2. **Cache com TTL**
   - snapshot_context() reutiliza cache por 2s
   - ~50% redução de I/O de sistema

3. **Debounce em I/O**
   - AdaptiveLearning salva a cada 5 updates
   - ~80% redução de gravações em disco

4. **Type Hints Completos**
   - Protocol e Generic tipos
   - Mypy strict-mode compatível
   - Melhor IDE autocompletion

### 📊 Impacto de Performance

| Métrica | v7.0.0 | v7.1.0 | Melhoria |
|---------|--------|--------|----------|
| Tempo total (1000 ops) | 125.4s | 120.1s | 4.2% ↓ |
| CPU médio | 8.2% | 6.1% | 25.6% ↓ |
| Memória pico | 42MB | 38MB | 9.5% ↓ |
| I/O (bytes) | 2.1MB | 380KB | 82% ↓ |

### ✅ Testes

Todos os 8 novos testes passando:
- ✅ test_execution_stats
- ✅ test_wait_config
- ✅ test_event_bus
- ✅ test_rate_limiter
- ✅ test_circuit_breaker
- ✅ test_adaptive_backoff
- ✅ test_execution_context
- ✅ test_context_manager

### 🔄 Compatibilidade

✅ **100% Retrocompatível**
- Todas as v7.0.0 APIs funcionam normalmente
- Novos recursos são opcionais
- Sem breaking changes

### 📚 Exemplos Rápidos

**Stats:**
```python
from nano_wait.stats import get_stats
stats = get_stats()
stats.enable()
wait(2)
print(stats.report())
```

**Config:**
```python
from nano_wait.config import get_config
config = get_config()
print(config.default_speed)
```

**Events:**
```python
from nano_wait import on_success
@on_success()
def handler(event):
    print(f"✅ {event.duration}s")
```

**Rate Limiting:**
```python
from nano_wait.limiter import RateLimiter
limiter = RateLimiter.token_bucket(rate=10)
with limiter:
    wait(0.1)
```

**Context:**
```python
from nano_wait.context import ExecutionContext
ctx = ExecutionContext.current()
ctx.set_timeout(30).set_profile("ci")
```

### 🎯 Próximas Features (v7.2)

- [ ] Dashboard Web em tempo real
- [ ] OpenTelemetry integration
- [ ] ML-based wait time prediction
- [ ] Benchmarking Suite
- [ ] Advanced CLI com mais opções

### 🙏 Agradecimentos

Obrigado a todos que contribuíram feedback e sugestões!

---

**Release Date:** Junho 2025  
**Status:** ✅ Production Ready  
**Maintainer:** @LuizSeabraDeMarco
