# 🔥 PyroSat

Sistema de detecção e alerta precoce de incêndios florestais baseado em dados de satélite, sensores IoT e análise de risco ambiental.

---

## Sobre o projeto

O PyroSat monitora regiões florestais divididas em células de 1km², calcula o risco de incêndio de cada célula, detecta focos de calor via satélite e escalona alertas para os órgãos responsáveis. A simulação de propagação do fogo usa o algoritmo de Dijkstra para estimar quais células podem ser atingidas em uma janela de tempo.

---

## Estruturas de dados

| Estrutura | Uso |
|---|---|
| Grafo de adjacência | Células de monitoramento interligadas por fator de propagação |
| Fila de prioridade (`heapq`) | Escalonamento de alertas por severidade |
| Pilha LIFO | Histórico de ocorrências por área |
| BFS | Delimitação da área de risco ao redor de um foco |
| Dijkstra | Simulação de propagação do fogo |

---

## Principais componentes

### `CelulaMonitoramento`
Representa uma célula de 1km² com mais de 40 atributos: condições ambientais, cobertura vegetal, dados de satélite, infraestrutura e histórico de incêndios.

### `FocoCalor`
Registro de um foco detectado por satélite (GOES-16, Sentinel-2, VIIRS), com classificação, severidade e órgãos acionados.

### `GrafoMonitoramento`
Grafo de adjacência onde cada nó é uma `CelulaMonitoramento`. As arestas representam o fator de propagação do fogo entre células vizinhas.

### `PilhaOcorrencias`
Pilha LIFO para registrar, consultar e cancelar ocorrências de incêndio em uma área monitorada.

---

## Funções principais

- **`calcular_risco(celula)`** — calcula o score de risco (0–100) com base em temperatura, umidade, vento, NDVI e histórico.
- **`classificar_foco(temp, ndvi, umidade)`** — classifica um foco como `CONFIRMADO`, `SUSPEITO` ou `FALSO`.
- **`propagar_fogo(grafo, foco_id, horas)`** — simula a propagação via Dijkstra e retorna o tempo estimado para cada célula ser atingida.
- **`escalonar_alertas(focos)`** — prioriza focos confirmados e define os órgãos a acionar conforme a severidade.
- **`busca_bfs_area_risco(grafo, origem, raio)`** — mapeia todas as células dentro de um raio de nós ao redor do foco.

---

## Níveis de risco

| Score | Nível | Órgãos acionados |
|---|---|---|
| 80 – 100 | EMERGÊNCIA | ICMBio, IBAMA, Defesa Civil, Bombeiros, INPE |
| 60 – 79 | ALERTA | Brigada Local, IBAMA, Defesa Civil |
| 40 – 59 | ATENÇÃO | Brigada Local, ICMBio |
| 0 – 39 | MONITORAMENTO | — |

---

## Como executar

```bash
python pyrosat.py
```

A simulação passa por 7 etapas com intervalo de 2 segundos entre cada uma:

1. Construção do grafo de monitoramento
2. Cálculo de risco por célula
3. Detecção e classificação de focos
4. Escalonamento de alertas por prioridade
5. Simulação de propagação do fogo (Dijkstra)
6. Mapeamento da área de risco (BFS)
7. Gerenciamento do histórico de ocorrências (pilha LIFO)

---

## Requisitos

- Python 3.10+
- Apenas bibliotecas da stdlib: `heapq`, `math`, `random`, `time`, `collections`, `dataclasses`

---

## Biomas monitorados

Cerrado · Amazônia · Pantanal · Mata Atlântica · Caatinga · Pampa
