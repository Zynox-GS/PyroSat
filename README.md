<div align="center">

# 🔥 PyroSat 

**Sistema de Detecção e Alerta Precoce de Incêndios Florestais Globais**

![Python](https://img.shields.io/badge/Python-3.7+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Status](https://img.shields.io/badge/Status-Concluído-success?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

</div>

---

## 📋 Visão Geral

O **PyroSat** é uma simulação computacional construída em Python que utiliza estruturas de dados clássicas para monitorar, detectar, escalonar e prever a propagação de incêndios florestais. O sistema processa dados simulados de satélites, condições climáticas e cobertura vegetal para classificar riscos, alertar órgãos competentes e prever o avanço do fogo no terreno.

---

## 🚨 Problema

Incêndios florestais se propagam rapidamente, mas os sistemas de alertas atuais são lentos e fragmentados. O PyroSat resolve isso integrando dados de satélite, condições climáticas e histórico de ocorrências para detectar focos, classificar riscos e acionar os órgãos competentes de forma automatizada e priorizada.

---

## 👥 Equipe Desenvolvedora

| Nome | RM |
|------|----|
| Arthur Serrano Veloso | 561542 |
| Carlos Eduardo Goes | 562389 |
| Hyann dos Santos Espindas | 563421 |
| Israel Araujo Henriques de Moura | 559068 |
| Walter Henrique Pereira de Toledo | 562476 |

---

## 🏗️ Estruturas de Dados e Algoritmos

| Estrutura / Algoritmo | Aplicação no Sistema |
|---|---|
| 🗺️ **Grafo de Adjacência** | Mapeamento das células territoriais de monitoramento (1km²) e suas conexões baseadas no vento e vegetação. |
| 📊 **Fila de Prioridade (Heapq)** | Escalonamento de alertas ambientais para priorizar automaticamente os focos de incêndio de maior severidade. |
| 🔁 **Algoritmo de Dijkstra** | Simulação da propagação do fogo, calculando o tempo estimado que as chamas levarão para atingir células vizinhas. |
| 🔍 **Busca em Largura (BFS)** | Mapeamento de zonas de risco globais imediatas ao redor de um foco confirmado. |
| 📚 **Pilha (LIFO)** | Gerenciamento do histórico de ocorrências, facilitando a reversão e o cancelamento rápido de alarmes falsos. |

---

## 🧩 Entidades Principais

- **`CelulaMonitoramento`** — Representa um fragmento de área. Armazena dados climáticos (temperatura, umidade, vento), geográficos, infraestrutura de combate e índices de vegetação (NDVI).
- **`FocoCalor`** — Representa uma anomalia térmica capturada por satélites (ex: GOES-16). É classificada por temperatura de brilho, severidade e nível de alerta.
- **`Ocorrencia`** — Evento consolidado que agrupa focos de calor, calcula área afetada e gerencia o acionamento de brigadas e o status da emergência.

---

## ⚙️ Regras de Negócio Implementadas

- **Cálculo de Risco:** Avalia a probabilidade de incêndio cruzando variáveis como temperatura acima de 35°C, baixa umidade, ventos fortes e histórico de ocorrências.
- **Classificação Automática:** Filtra ruídos térmicos avaliando a temperatura de brilho e os índices de vegetação, descartando falsos positivos.
- **Acionamento Inteligente:** Direciona os alertas para diferentes instâncias (Brigada Local, Defesa Civil, Agência Espacial) de acordo com a gravidade do foco escalonado.

---

## 🔧 Funções Principais (`def`)

### `calcular_risco(celula)`
Calcula o score de risco de incêndio (0–100) de uma célula de monitoramento. Leva em conta temperatura, umidade, velocidade do vento, índice de vegetação (NDVI), precipitação nas últimas 24h e histórico de ocorrências. Atualiza os atributos `score_risco` e `nivel_risco` diretamente na célula.

---

### `classificar_foco(temperatura_brilho, ndvi, umidade)`
Classifica um foco de calor detectado por satélite como **CONFIRMADO**, **SUSPEITO** ou **FALSO**. Utiliza temperatura de brilho, NDVI e umidade relativa para filtrar ruídos térmicos e distinguir focos reais de falsos positivos.

---

### `propagar_fogo(grafo, foco_inicial_id, horas)`
Simula a propagação do fogo a partir de um foco inicial usando o **algoritmo de Dijkstra**. Calcula o tempo estimado (em horas) para o fogo atingir cada célula vizinha, considerando o peso das arestas como fator de propagação (vento + vegetação). Retorna apenas as células alcançáveis dentro da janela de horas definida.

---

### `escalonar_alertas(fila_focos)`
Escalonamento de focos confirmados por prioridade usando **fila de mínimo (heapq)**. Define o nível de alerta e os órgãos a serem acionados conforme o score de severidade, retornando os focos ordenados do mais crítico para o menos crítico.

---

### `busca_bfs_area_risco(grafo, celula_origem_id, raio_nos)`
Mapeia a zona de risco ao redor de um foco usando **Busca em Largura (BFS)**. Percorre o grafo a partir da célula de origem até o raio definido em número de nós, retornando todas as células que podem ser afetadas pela propagação imediata do fogo.

---

### `criar_grafo_exemplo(num_celulas)`
Gera um grafo de monitoramento com células aleatórias para fins de simulação. Cria células com dados ambientais, de vegetação, infraestrutura e satélite gerados aleatoriamente, e conecta células adjacentes com arestas ponderadas pelo vento e NDVI.

---

### `gerar_focos_exemplo(grafo, qtd)`
Gera uma lista de focos de calor simulados a partir das células do grafo. Os primeiros focos recebem temperaturas de brilho altas (450–850°C) para simular incêndios confirmados; os demais recebem temperaturas baixas (40–150°C) para simular suspeitos ou falsos positivos.

---

### `executar_simulacao()`
Executa o pipeline completo de detecção e alerta do PyroSat Global. Demonstra sequencialmente: construção do grafo, cálculo de risco, detecção de focos via satélite, escalonamento por fila de prioridade, propagação do fogo com Dijkstra, mapeamento de zona de risco com BFS e gerenciamento do histórico de ocorrências com pilha LIFO.

---

### `PilhaOcorrencias` — Métodos

| Método | Descrição |
|--------|-----------|
| `push(ocorrencia)` | Registra uma nova ocorrência no topo da pilha. |
| `pop()` | Remove e retorna a ocorrência mais recente (usado para cancelar alarmes falsos). |
| `peek()` | Retorna a ocorrência mais recente sem removê-la. |
| `listar_historico()` | Retorna todas as ocorrências do mais recente para o mais antigo. |
| `total()` | Retorna o número total de ocorrências na pilha. |
| `esta_vazia()` | Retorna `True` se a pilha não contiver nenhuma ocorrência. |

## ▶️ Como Executar

> O projeto utiliza **exclusivamente a biblioteca padrão do Python**. Nenhuma instalação de pacote externo é necessária.

**Requisito:** Python 3.7+

```bash
python PyroSat.py
```

### O que acontece na simulação?

A execução rodará a função `executar_simulacao()`, demonstrando o pipeline completo no terminal:

1. 🗺️ Geração de um grafo com 20 células aleatórias
2. 📊 Cálculo de risco para cada região mapeada
3. 🛰️ Geração de focos de calor com temperaturas aleatórias simulando captação via satélite
4. 📥 Triagem e inserção dos dados em uma Fila de Prioridade
5. 🔥 Propagação simulada do fogo principal usando o algoritmo de Dijkstra (previsão de 6h)
6. 🔍 Mapeamento da zona de risco (raio de 3 nós) utilizando BFS
7. 📚 Registro, listagem e cancelamento de eventos na estrutura de Pilha
