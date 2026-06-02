PyroSat Global 🌍
Sistema de Detecção e Alerta Precoce de Incêndios Florestais

O PyroSat Global é um simulador avançado desenvolvido em Python que processa dados ambientais e de satélite para detectar, classificar e prever a propagação de incêndios florestais em escala global. O sistema utiliza estruturas de dados complexas para garantir uma resposta rápida e escalonada a emergências.

Funcionalidades e Estruturas Utilizadas
O motor lógico do sistema é construído sobre quatro estruturas fundamentais:

Grafos de Adjacência: Mapeamento de células de monitoramento (1 km²) com pesos dinâmicos baseados no vento e vegetação.

Busca em Largura (BFS): Delimitação rápida de zonas de risco globais para evacuação.

Algoritmo de Dijkstra: Previsão e simulação da propagação do fogo ao longo do tempo.

Fila de Prioridade (heapq): Escalonamento de alertas (Max-Heap), priorizando focos com maior severidade.

Pilha (LIFO): Gerenciamento do histórico de ocorrências, permitindo auditoria e reversão de falsos positivos.

 Como Executar
O projeto foi construído utilizando apenas bibliotecas nativas do Python, não exigindo instalações de pacotes externos.

Pré-requisitos: Python 3.9 ou superior.

Clone este repositório:

Bash
git clone https://github.com/SEU_USUARIO/pyrosat-global.git
Acesse o diretório do projeto:

Bash
cd pyrosat-global
Execute o simulador:

Bash
python pyrosat.py

Contexto do Projeto
Este projeto foi desenvolvido como parte da Global Solution 2026 da FIAP (Faculdade de Informática e Administração Paulista).

Equipe:

Arthur Serrano Veloso - RM 561542

Carlos Eduardo Goes - RM 562389

Hyann dos Santos Espindas - RM 563421

Israel Araujo Henriques de Moura - RM 559068

Walter Henrique Pereira de Toledo - RM 562476
