PyroSat Global 🌍🔥
Sistema de Detecção e Alerta Precoce de Incêndios Florestais Globais.

Visão Geral
O PyroSat Global é uma simulação computacional construída em Python que utiliza estruturas de dados clássicas para monitorar, detectar, escalonar e prever a propagação de incêndios florestais. O sistema processa dados simulados de satélites, condições climáticas e cobertura vegetal para classificar riscos, alertar órgãos competentes e prever o avanço do fogo no terreno.

Problema
Incêndios florestais se propagam rapidamente, mas os sistemas de alertas atuais são lentos e fragmentados. O PyroSat resolve isso integrando dados de satélite, condições climáticas e histórico de ocorrências para detectar focos, classificar riscos e acionar os órgãos competentes de forma automatizada e priorizada.

👥 Equipe Desenvolvedora

Arthur Serrano Veloso – RM 561542
Carlos Eduardo Goes – RM 562389
Hyann dos Santos Espindas – RM 563421
Israel Araujo Henriques de Moura – RM 559068
Walter Henrique Pereira de Toledo – RM 562476


Estruturas de Dados e Algoritmos
Estrutura / AlgoritmoAplicação no SistemaGrafo de AdjacênciaMapeamento das células territoriais de monitoramento (1km²) e suas conexões baseadas no vento e vegetação.Fila de Prioridade (Heapq)Escalonamento de alertas ambientais para priorizar automaticamente os focos de incêndio de maior severidade.Algoritmo de DijkstraSimulação da propagação do fogo, calculando o tempo estimado que as chamas levarão para atingir células vizinhas.Busca em Largura (BFS)Mapeamento de zonas de risco globais imediatas ao redor de um foco confirmado.Pilha (LIFO)Gerenciamento do histórico de ocorrências, facilitando a reversão e o cancelamento rápido de alarmes falsos.

Entidades Principais

CelulaMonitoramento: Representa um fragmento de área. Armazena dados climáticos (temperatura, umidade, vento), geográficos, infraestrutura de combate e índices de vegetação (NDVI).
FocoCalor: Representa uma anomalia térmica capturada por satélites (ex: GOES-16). É classificada por temperatura de brilho, severidade e nível de alerta.
Ocorrencia: Evento consolidado que agrupa focos de calor, calcula área afetada e gerencia o acionamento de brigadas e o status da emergência.


Regras de Negócio Implementadas

Cálculo de Risco: Avalia a probabilidade de incêndio cruzando variáveis como temperatura acima de 35°C, baixa umidade, ventos fortes e histórico de ocorrências.
Classificação Automática: Filtra ruídos térmicos avaliando a temperatura de brilho e os índices de vegetação, descartando falsos positivos.
Acionamento Inteligente: Direciona os alertas para diferentes instâncias (Brigada Local, Defesa Civil, Agência Espacial) de acordo com a gravidade do foco escalonado.


Como Executar
O projeto utiliza exclusivamente a biblioteca padrão do Python (heapq, math, random, time, collections, dataclasses, typing). Nenhuma instalação de pacote externo é necessária.
Requisito: Python 3.7+
Execute o arquivo diretamente via terminal:
bashpython pyrosat.py
O que acontece na simulação?
A execução rodará a função executar_simulacao(), demonstrando o pipeline completo no terminal:

Geração de um grafo com 20 células aleatórias.
Cálculo de risco para cada região mapeada.
Geração de focos de calor com temperaturas aleatórias simulando captação via satélite.
Triagem e inserção dos dados em uma Fila de Prioridade.
Propagação simulada do fogo principal usando o algoritmo de Dijkstra (previsão de 6h).
Mapeamento da zona de risco (raio de 3 nós) utilizando BFS.
Registro, listagem e cancelamento de eventos na estrutura de Pilha.
