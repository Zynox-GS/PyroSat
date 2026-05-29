```markdown
# PyroSat 

> Módulo de **Programação Dinâmica** do sistema PyroSat: detecção e alerta precoce de incêndios florestais via satélite e IA.

**Disciplina:** Dynamic Programming — Filas, Pilhas e Grafos  
**Curso:** Engenharia de Software — FIAP  
**Projeto:** Global Solution (GS)

---

## Sobre o Projeto

O PyroSat é um sistema que integra dados de satélites (GOES-16, Sentinel-2, VIIRS) para detectar focos de calor, calcular risco de propagação e acionar os órgãos responsáveis de forma automática e priorizada.

Este módulo Python implementa a **camada de processamento e inteligência** do sistema, responsável por:

- Modelar o território monitorado como um **grafo de células de 1km²**
- Calcular o **score de risco** de cada célula com base em dados ambientais
- Classificar focos de calor como `CONFIRMADO`, `SUSPEITO` ou `FALSO`
- Simular a **propagação do fogo** usando Dijkstra
- Escalonar alertas por severidade usando **fila de prioridade**
- Manter o **histórico de ocorrências** em pilha LIFO

---

## Estruturas de Dados

###  Grafo de Adjacência — `GrafoMonitoramento`

Cada nó do grafo é uma `CelulaMonitoramento` representando 1km² de território. As arestas conectam células vizinhas e carregam um **peso de propagação** calculado a partir de vento e vegetação.

```
[Célula 0] ── 0.42 ── [Célula 1] ── 0.31 ── [Célula 2]
     |                      |                      |
   0.55                   0.38                   0.27
     |                      |                      |
[Célula 5] ── 0.61 ── [Célula 6] ── 0.44 ── [Célula 7]
```

- **Nós:** células de monitoramento com 53 atributos cada
- **Arestas:** bidirecionais, peso = `(velocidade_vento / 50 + ndvi) / 2`
- **Travessia:** BFS para área de risco, Dijkstra para propagação temporal

---

###  Fila de Prioridade — `heapq`

Usada em `escalonar_alertas()` para ordenar focos confirmados por severidade. Implementa o protocolo de acionamento em cascata (RN02).

```python
# Foco EMERGÊNCIA (score 80-100) → topo da fila
# Foco ALERTA     (score 60-79)  → segunda prioridade  
# Foco ATENÇÃO    (score 40-59)  → terceira prioridade
# Foco MONIT.     (score  0-39)  → apenas registro
```

A prioridade é armazenada como valor **negativo** no heap (min-heap do Python simula max-heap).

---

###  Pilha LIFO — `PilhaOcorrencias`

Mantém o histórico de ocorrências de incêndio de uma área monitorada. O `pop()` implementa a operação de **cancelar/desfazer** um falso positivo.

| Operação | Método | Descrição |
|---|---|---|
| Empilhar | `push(ocorrencia)` | Registra nova ocorrência |
| Desempilhar | `pop()` | Cancela/desfaz a mais recente |
| Consultar topo | `peek()` | Lê sem remover |
| Listar | `listar_historico()` | Retorna em ordem LIFO |

---

## Funções Principais

### `calcular_risco(celula)` → `float`

Calcula o score de risco de incêndio de uma célula (0–100) com base em 6 fatores ambientais ponderados:

| Fator | Peso | Lógica |
|---|---|---|
| Temperatura | 25 | Pontua acima de 35°C |
| Umidade relativa | 30 | Inversamente proporcional |
| Velocidade do vento | 20 | Pontua acima de 20 km/h |
| NDVI (vegetação) | 15 | Vegetação densa seca = maior risco |
| Precipitação 24h | 10 | Chuva reduz risco |
| Histórico | bônus | +15% se > 3 ocorrências anteriores |

Atualiza `celula.score_risco` e `celula.nivel_risco` automaticamente.

---

### `classificar_foco(temperatura_brilho, ndvi, umidade)` → `str`

Simula o modelo de IA do PyroSat para classificar um foco detectado por satélite.

```
temperatura_brilho > 340K  +  ndvi > 0.3  +  umidade < 40%  →  CONFIRMADO
temperatura_brilho > 310K  +  ndvi > 0.15                    →  SUSPEITO
ndvi < 0.1  (sem vegetação)                                   →  FALSO
```

Implementa a **RN01**: apenas focos `CONFIRMADO` geram alertas.

---

### `propagar_fogo(grafo, foco_inicial_id, horas)` → `dict`

Simula a frente de fogo usando **algoritmo de Dijkstra** no grafo de células. Retorna um dicionário `{celula_id: horas_para_atingir}` com todas as células alcançáveis dentro da janela de tempo informada.

```python
propagacao = propagar_fogo(grafo, foco_inicial_id=3, horas=6)
# {3: 0.0, 4: 1.2, 8: 2.7, 9: 3.1, ...}
```

O tempo de travessia de cada aresta é `1 / (peso + 0.01)` — peso alto significa propagação rápida.

---

### `escalonar_alertas(fila_focos)` → `list[FocoCalor]`

Filtra apenas focos `CONFIRMADO`, define os órgãos a acionar conforme o nível e retorna a lista ordenada do mais urgente ao menos urgente.

```
EMERGÊNCIA → ICMBio, IBAMA, Defesa Civil, Bombeiros, INPE
ALERTA     → Brigada Local, IBAMA, Defesa Civil
ATENÇÃO    → Brigada Local, ICMBio
MONIT.     → (sem acionamento externo)
```

---

### `busca_bfs_area_risco(grafo, celula_origem_id, raio_nos)` → `list[int]`

BFS a partir de um foco confirmado para delimitar a área de risco ao redor. Retorna os IDs de todas as células dentro do raio de nós informado.

---

## Modelos de Dados

### `CelulaMonitoramento` (nó do grafo)

```python
# Identificação (6)
id, latitude, longitude, municipio, estado, bioma

# Condições ambientais (10)
temperatura, umidade, velocidade_vento, direcao_vento, precipitacao_24h,
pressao_atmosferica, indice_calor, ponto_orvalho, radiacao_solar, visibilidade_km

# Cobertura vegetal (8)
ndvi, tipo_vegetacao, densidade_florestal, altura_media_vegetacao_m,
percentual_vegetacao_seca, carga_combustivel_ton_ha,
indice_umidade_combustivel, especie_dominante

# Risco calculado (5)
score_risco, nivel_risco, indice_fwi,
probabilidade_propagacao, velocidade_propagacao_kmh

# Estado do foco (5)
tem_foco_ativo, classificacao_foco, timestamp_deteccao,
area_queimada_ha, perimetro_fogo_km

# Histórico (5)
ocorrencias_historicas, ultimo_incendio_anos,
area_total_queimada_historica_ha, recorrencia_media_anos,
maior_incendio_registrado_ha

# Infraestrutura (8)
distancia_brigada_km, tem_torre_observacao, tem_sensor_iot,
distancia_estrada_km, distancia_corpo_hidrico_km,
tem_aceiro, capacidade_tanque_agua_l, cobertura_satelite

# Dados de satélite (6)
temperatura_superficie_k, reflectancia_banda_swir, anomalia_termica_mw,
ultima_passagem_satelite, indice_nbr, indice_evi
```

**Total: 53 atributos por nó do grafo.**

### `FocoCalor` (elemento da fila de prioridade)

```python
prioridade, id, celula_id, latitude, longitude,
temperatura_brilho, frp, classificacao, severidade_score,
nivel_alerta, fonte_satelite, timestamp,
confirmado_operador, orgaos_acionados
```

### `Ocorrencia` (elemento da pilha)

```python
id, focos_ids, area_afetada_ha, nivel_maximo,
duracao_horas, brigadas_envolvidas, status,
timestamp_inicio, timestamp_fim, relatorio_gerado
```

---

## Como Executar

**Pré-requisitos:** Python 3.10 ou superior. Nenhuma biblioteca externa necessária — apenas módulos da biblioteca padrão.

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/pyrosat.git
cd pyrosat

# Execute a simulação
python pyrosat.py
```

---

## Exemplo de Saída

```
============================================================
   PyroSat — Simulação de Detecção e Alerta de Incêndios
============================================================

[1] Construindo grafo de monitoramento...
    Grafo criado: 20 células, 31 arestas

[2] Calculando score de risco para cada célula...
    Células em ALERTA ou EMERGÊNCIA: 4
      → Celula(id=2, bioma=Cerrado, risco=84.3, nivel=EMERGÊNCIA)
      → Celula(id=7, bioma=Amazônia, risco=71.2, nivel=ALERTA)
      ...

[3] Detectando e classificando focos de calor (satélite)...
    Total detectado: 8 focos
    Confirmados: 3 | Suspeitos: 3 | Falsos: 2

[4] Escalonando alertas por prioridade (fila heapq)...
    3 focos confirmados na fila:
      → Foco(id=0, nivel=EMERGÊNCIA, score=84.3) | Órgãos: ['ICMBio', 'IBAMA', ...]
      → Foco(id=2, nivel=ALERTA, score=71.2)     | Órgãos: ['Brigada Local', ...]
      → Foco(id=1, nivel=ATENÇÃO, score=52.8)    | Órgãos: ['Brigada Local', ...]

[5] Simulando propagação do fogo (Dijkstra, 6h)...
    Fogo pode atingir 9 células em até 6 horas:
      → Célula 0: ~0.00h
      → Célula 1: ~1.18h
      → Célula 5: ~1.52h
      ...

[6] BFS: mapeando área de risco (raio 3 nós ao redor do foco)...
    8 células na área de risco: [0, 1, 5, 2, 6, 10, 3, 7]

[7] Gerenciando histórico de ocorrências com pilha LIFO...
  [PILHA] Ocorrência 1001 registrada na área 1.
  [PILHA] Ocorrência 1002 registrada na área 1.
  [PILHA] Ocorrência 1003 registrada na área 1.
    Total na pilha: 3 ocorrências
    Mais recente (peek): Ocorrência 1003

    Cancelando última ocorrência (falso positivo — pop):
  [PILHA] Ocorrência 1003 removida (cancelada/falso positivo).
    Total após remoção: 2

    Histórico LIFO (mais recente primeiro):
      → Ocorrência 1002 | Status: ATIVA     | Área: 45.0ha
      → Ocorrência 1001 | Status: ENCERRADA | Área: 120.5ha

============================================================
   Simulação concluída com sucesso!
============================================================
```

---

## Conexão com as Outras Disciplinas

O PyroSat é um projeto integrado entre três disciplinas. Este módulo Python é a **camada de processamento** que conecta as outras duas:

```
Foco detectado (satélite)
        │
        ▼
┌─────────────────┐        SELECT focos, áreas
│  DATABASE DESIGN │ ◄──────────────────────────┐
│  PostgreSQL +    │                             │
│  PostGIS         │ ──── CRUD entidades ───►   │
└─────────────────┘                             │
        │                                       │
        │ lê focos e áreas                      │ grava score_risco
        ▼                                       │
┌─────────────────────────────────────────────┐ │
│         DYNAMIC PROGRAMMING — Python        │─┘
│                                             │
│  GrafoMonitoramento   →  células de risco   │
│  propagar_fogo()      →  BFS / Dijkstra     │
│  escalonar_alertas()  →  fila de prioridade │
│  PilhaOcorrencias     →  histórico LIFO     │
└─────────────────────────────────────────────┘
        │
        │ score de risco calculado
        ▼
┌─────────────────┐
│   DDD — JAVA    │
│                 │
│  FocoCalor      │  ← espelha a dataclass Python
│  FocoConfirmado │  ← extends FocoCalor
│  Coordenador    │  ← acionarProtocoloCascata()
│  Notificavel    │  ← interface dos órgãos
└─────────────────┘
```

| Disciplina | Papel no sistema | Ponto de contato com este módulo |
|---|---|---|
| **Database Design** | Persiste todas as entidades | `CelulaMonitoramento` e `FocoCalor` espelham as tabelas; `score_risco` é gravado de volta |
| **Dynamic Programming** | Processa e calcula risco | **Este arquivo** |
| **DDD Java** | Camada de aplicação e regras OO | `FocoCalor`, `Ocorrencia` e `escalonar_alertas()` são replicados como classes Java com herança |

---

## Regras de Negócio Implementadas

| Código | Regra | Onde no código |
|---|---|---|
| RN01 | Foco só gera alerta se classificado como `CONFIRMADO` | `escalonar_alertas()` — filtra antes de enfileirar |
| RN02 | Acionamento em cascata conforme severidade | `escalonar_alertas()` — define `orgaos_acionados` por nível |
| RN03 | Score de risco baseado em múltiplos fatores ambientais | `calcular_risco()` |
| RN04 | Propagação do fogo considera vento e vegetação | `propagar_fogo()` — peso da aresta |
| RN05 | Cancelamento de falso positivo desfaz o último alerta | `PilhaOcorrencias.pop()` |
| RN06 | Histórico de ocorrências retido por área monitorada | `PilhaOcorrencias` por `area_id` |

---
