# ❓ NanoWait v7.1 — FAQ (Perguntas Frequentes)

---

## 📚 Geral

### P: Qual é a diferença entre v7.0 e v7.1?
**R:** v7.1 adiciona 5 novos módulos para produção:
- **stats.py** — Rastreamento de métricas
- **config.py** — Gerenciamento de configuração
- **events.py** — Sistema de eventos
- **limiter.py** — Rate limiting e circuit breaker
- **context.py** — Execution context

Tudo é **retrocompatível** — código existente funciona sem mudanças.

---

### P: Preciso usar os novos módulos?
**R:** Não! São completamente **opcionais**. Use apenas o que precisar:
```python
# v7.0 — continua funcionando
from nano_wait import wait
wait(2)

# v7.1 — novo, mas opcional
from nano_wait.stats import get_stats
stats = get_stats()
```

---

### P: Como migrar de v7.0 para v7.1?
**R:** Apenas instale:
```bash
pip install nano-wait --upgrade
```

Não há mudanças necessárias em código existente.

---

## 📊 Stats Module

### P: Como habilitar rastreamento de stats?
**R:**
```python
from nano_wait.stats import get_stats

stats = get_stats()
stats.enable()
```

### P: Onde os dados de stats são salvos?
**R:** Em `~/.nano_wait_stats.json` com retenção de 7 dias.

### P: Qual é o overhead de stats?
**R:** Negligenciável (~0.1% CPU, alguns KB de memória).

### P: Como limpar dados antigos?
**R:** Automático! Dados > 7 dias são removidos. Ou manual:
```python
stats.clear()
```

---

## ⚙️ Config Module

### P: Como criar arquivo de config?
**R:**
```yaml
# ~/.nanowait.yml
default_speed: fast
default_profile: ci
default_timeout: 30
enable_stats: true
```

### P: Quais formatos são suportados?
**R:** YAML (`.yml`, `.yaml`) e JSON (`.json`)

### P: Em qual ordem procura por config?
**R:**
1. `~/.nanowait.yml`
2. `~/.nanowait.yaml`
3. `~/.nanowait.json`
4. `./.nanowait.yml` (diretório atual)
5. `./.nanowait.json` (diretório atual)

Primeira encontrada é usada.

### P: Como override config em runtime?
**R:**
```python
from nano_wait.config import get_config

config = get_config()
new_config = config.merge({"default_speed": "ultra"})
```

---

## 🎣 Events Module

### P: Como registrar um event listener?
**R:**
```python
from nano_wait import on_success, on_error

@on_success()
def handler(event):
    print(f"Success: {event.duration}s")

@on_error()
def error_handler(event):
    print(f"Error: {event.error}")
```

### P: Quais tipos de eventos existem?
**R:** SUCCESS, TIMEOUT, CONDITION_MET, ERROR, RETRY, STARTED

### P: Posso ouvir todos os eventos?
**R:** Sim:
```python
from nano_wait.events import on_any_event

@on_any_event()
def log_all(event):
    print(f"Event: {event.event_type}")
```

### P: Um erro em handler quebra a aplicação?
**R:** Não! Erros em handlers são capturados e logados.

### P: Como emitir eventos customizados?
**R:**
```python
from nano_wait.events import emit_event, WaitEventType

emit_event(
    WaitEventType.RETRY,
    duration=0.5,
    metadata={"reason": "api_throttled"}
)
```

---

## 🚦 Limiter Module

### P: Quando usar Token Bucket vs Sliding Window?
**R:**
- **Token Bucket** — Previsível, permite bursts. Use para APIs.
- **Sliding Window** — Mais justo, sem bursts. Use para recursos críticos.

### P: Como funciona Circuit Breaker?
**R:**
1. **CLOSED** — Normal, requisições passam
2. **OPEN** — Falhas acima do threshold, requisições rejeitadas
3. **HALF_OPEN** — Testando recuperação

```python
from nano_wait.limiter import CircuitBreaker

cb = CircuitBreaker(
    failure_threshold=5,      # 5 falhas = abre
    recovery_timeout=60,      # Tenta recuperar após 60s
    success_threshold=2       # 2 sucessos = fecha
)

with cb:
    api_call()
```

### P: Como resetar Circuit Breaker?
**R:**
```python
cb.reset()
```

### P: O que é "jitter" no Backoff?
**R:** Variação aleatória para evitar "thundering herd" (múltiplas requisições simultâneas):
```python
from nano_wait.limiter import AdaptiveBackoff

backoff = AdaptiveBackoff()
delay = backoff.next()  # 0.1s, 0.2s±jitter, 0.4s±jitter, ...
```

---

## 🎛️ Context Module

### P: Como usar Execution Context?
**R:**
```python
from nano_wait.context import ExecutionContext

ctx = ExecutionContext.current()
ctx.set_timeout(30).set_profile("ci").set_speed("fast")

# Todas as operações herdam este contexto
wait(2)
```

### P: Como Execution Context funciona em multithreading?
**R:** Cada thread tem seu próprio contexto (thread-local storage):
```python
from threading import Thread
from nano_wait.context import ExecutionContext

def worker():
    ctx = ExecutionContext.current()
    ctx.set_profile("rpa")
    # Só afeta esta thread
    wait(1)

t = Thread(target=worker)
t.start()

# Thread principal não é afetada
wait(1)  # Usa profile padrão
```

### P: Como herdar contexto de função para função?
**R:** Implicitamente:
```python
from nano_wait.context import ExecutionContext

ctx = ExecutionContext.current()
ctx.set_profile("ci")

def process():
    wait(2)  # Herda profile="ci"

process()
```

---

## 🧪 Testes

### P: Como testar com novos módulos?
**R:**
```python
from nano_wait.stats import ExecutionStats
from nano_wait.config import WaitConfig
from nano_wait.limiter import CircuitBreaker

def test_stats():
    stats = ExecutionStats()
    stats.enable()
    wait(0.1)
    assert stats.summary().total_executions == 1

def test_config():
    config = WaitConfig(default_speed="fast")
    assert config.default_speed == "fast"

def test_circuit_breaker():
    cb = CircuitBreaker(failure_threshold=3)
    cb.record_failure()
    cb.record_failure()
    cb.record_failure()
    assert cb.is_open()
```

---

## 🐛 Troubleshooting

### P: Stats não está registrando nada
**R:** Verifique se está habilitado:
```python
from nano_wait.stats import get_stats

stats = get_stats()
print(f"Enabled: {stats._enabled}")

stats.enable()  # Se False
```

### P: Config não está sendo carregada
**R:** Verifique se arquivo existe e está em local correto:
```python
from pathlib import Path
from nano_wait.config import WaitConfig

# Verifica locais de busca
for path in WaitConfig._config_paths:
    print(f"Verificando: {path.expanduser()}")
    if path.exists():
        print(f"  ✅ Encontrado!")
```

### P: Circuit Breaker não reseta automaticamente
**R:** Espere `recovery_timeout` segundos:
```python
import time
from nano_wait.limiter import CircuitBreaker

cb = CircuitBreaker(failure_threshold=3, recovery_timeout=5)

# Force 3 falhas
for _ in range(3):
    cb.record_failure()

print(cb.is_open())  # True

time.sleep(6)  # Aguarda recovery_timeout
print(cb.is_open())  # False (HALF_OPEN agora)
```

### P: Rate Limiter está rejeitando requisições rápido demais
**R:** Aumente a capacity:
```python
from nano_wait.limiter import RateLimiter

# Antes: 10 req/s, capacity=20 (default)
limiter = RateLimiter.token_bucket(rate=10, capacity=10)

# Depois: permite mais burst
limiter = RateLimiter.token_bucket(rate=10, capacity=50)
```

---

## 🎯 Performance

### P: Qual é o overhead de stats?
**R:** ~0.1% CPU, negligenciável

### P: Rate Limiter afeta latência?
**R:** Não, apenas controla throughput. Latência é da operação original.

### P: Qual é o melhor profile?
**R:** Depende:
- **ci** — CI/CD, máxima agressividade
- **testing** — Testes, equilíbrio
- **rpa** — RPA, máxima estabilidade
- **default** — Uso geral
- **turbo** — Máxima velocidade
- **safe** — Máxima estabilidade

### P: Posso usar múltiplas limiters?
**R:** Sim, cada uma é independente:
```python
limiter1 = RateLimiter.token_bucket(rate=10)
limiter2 = RateLimiter.token_bucket(rate=5)

with limiter1:
    with limiter2:
        wait(0.1)  # Limitado pelo mais restritivo
```

---

## 📖 Documentação

### P: Onde encontro exemplos?
**R:** Veja [demo_v71.py](demo_v71.py) para 7 exemplos completos

### P: Qual documentação devo ler?
**R:**
- Rápido: [QUICK_START_v71.md](QUICK_START_v71.md) (5 min)
- Completo: [NEW_FEATURES.md](NEW_FEATURES.md)
- Técnico: [OPTIMIZATION_REPORT.md](OPTIMIZATION_REPORT.md)
- Práticas: [BEST_PRACTICES.md](BEST_PRACTICES.md)

---

## 🤝 Comunidade

### P: Onde reporatar bugs?
**R:** https://github.com/LuizSeabraDeMarco/NanoWait/issues

### P: Como contribuir?
**R:** Veja [CONTRIBUTING.md](CONTRIBUTING.md)

### P: Qual é a roadmap para v7.2?
**R:**
- Dashboard Web
- OpenTelemetry integration
- ML-based optimization
- Benchmarking Suite

---

## 📞 Suporte

Se sua pergunta não está respondida aqui, abra uma issue no GitHub!

---

**v7.1.0** — Junho 2025
