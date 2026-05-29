"""
PyroSat - Sistema de Detecção e Alerta Precoce de Incêndios Florestais

Estruturas utilizadas:
    - Grafo de adjacência (células de monitoramento 1km²)
    - Fila de prioridade (heapq) para escalonamento de alertas
    - Pilha (LIFO) para histórico de ocorrências
    - BFS/Dijkstra para propagação do fogo
    - 4+ funções def com lógica de domínio
"""

import heapq
import math
import random
from collections import deque
from dataclasses import dataclass, field
from typing import Optional


# CONSTANTES DO DOMÍNIO


CLASSIFICACAO_SUSPEITO   = "SUSPEITO"
CLASSIFICACAO_CONFIRMADO = "CONFIRMADO"
CLASSIFICACAO_FALSO      = "FALSO"
 
NIVEL_MONITORAMENTO = "MONITORAMENTO"
NIVEL_ATENCAO       = "ATENÇÃO"
NIVEL_ALERTA        = "ALERTA"
NIVEL_EMERGENCIA    = "EMERGÊNCIA"
 
BIOMAS = ["Cerrado", "Amazônia", "Pantanal", "Mata Atlântica", "Caatinga", "Pampa"]



# DATACLASSES 

 
@dataclass
class CelulaMonitoramento:
    """
    Representa uma célula de 1km² no grafo de monitoramento.
    Cada nó do grafo possui estes atributos (>30 no conjunto do sistema).
    """
    # Identificação
    id: int
    latitude: float
    longitude: float
    municipio: str
    estado: str
    bioma: str
 
    # Condições ambientais
    temperatura: float          # °C
    umidade: float              # % relativa
    velocidade_vento: float     # km/h
    direcao_vento: float        # graus (0-360)
    precipitacao_24h: float     # mm
    pressao_atmosferica: float  # hPa
    indice_calor: float         # °C — sensação térmica
    ponto_orvalho: float        # °C — temperatura de condensação
    radiacao_solar: float       # W/m² — irradiância solar
    visibilidade_km: float      # km — visibilidade atmosférica
 
    # Cobertura vegetal
    ndvi: float                 # -1.0 a 1.0 (índice vegetação)
    tipo_vegetacao: str
    densidade_florestal: float  # 0.0 a 1.0
    altura_media_vegetacao_m: float       # metros
    percentual_vegetacao_seca: float      # 0–100%
    carga_combustivel_ton_ha: float       # ton/ha de material combustível
    indice_umidade_combustivel: float     # 0–300 (FMC)
    especie_dominante: str                # espécie vegetal predominante
 
    # Risco calculado
    score_risco: float = 0.0                 # 0-100 (calculado por calcular_risco)
    nivel_risco: str = NIVEL_MONITORAMENTO
    indice_fwi: float = 0.0                  # Fire Weather Index (0–100)
    probabilidade_propagacao: float = 0.0    # 0.0–1.0
    velocidade_propagacao_kmh: float = 0.0   # km/h estimada da frente de fogo
 
    # Estado do foco
    tem_foco_ativo: bool = False
    classificacao_foco: Optional[str] = None
    timestamp_deteccao: Optional[str] = None
    area_queimada_ha: float = 0.0       # hectares já consumidos
    perimetro_fogo_km: float = 0.0      # km de perímetro ativo
 
    # Histórico
    ocorrencias_historicas: int = 0
    ultimo_incendio_anos: float = 0.0
    area_total_queimada_historica_ha: float = 0.0
    recorrencia_media_anos: float = 0.0
    maior_incendio_registrado_ha: float = 0.0
 
    # Infraestrutura
    distancia_brigada_km: float = 0.0
    tem_torre_observacao: bool = False
    tem_sensor_iot: bool = False
    distancia_estrada_km: float = 0.0
    distancia_corpo_hidrico_km: float = 0.0
    tem_aceiro: bool = False
    capacidade_tanque_agua_l: float = 0.0
    cobertura_satelite: str = "GOES-16"

    # Dados de satélite
    temperatura_superficie_k: float = 0.0
    reflectancia_banda_swir: float = 0.0
    anomalia_termica_mw: float = 0.0
    ultima_passagem_satelite: Optional[str] = None
    indice_nbr: float = 0.0
    indice_evi: float = 0.0
 
    def __repr__(self):
        return (
            f"Celula(id={self.id}, bioma={self.bioma}, "
            f"risco={self.score_risco:.1f}, nivel={self.nivel_risco})"
        )
 
 
@dataclass(order=True)
class FocoCalor:
    
    #Representa um foco de calor detectado.
    #Usado na fila de prioridade — order=True permite comparação direta.
    
    prioridade: float = field(compare=True)   # invertido: menor = maior urgência
    id: int = field(compare=False)
    celula_id: int = field(compare=False)
    latitude: float = field(compare=False)
    longitude: float = field(compare=False)
    temperatura_brilho: float = field(compare=False)   # Kelvin (GOES-16 FRP)
    frp: float = field(compare=False)                  # Fire Radiative Power (MW)
    classificacao: str = field(compare=False, default=CLASSIFICACAO_SUSPEITO)
    severidade_score: float = field(compare=False, default=0.0)
    nivel_alerta: str = field(compare=False, default=NIVEL_MONITORAMENTO)
    fonte_satelite: str = field(compare=False, default="GOES-16")
    timestamp: str = field(compare=False, default="")
    confirmado_operador: bool = field(compare=False, default=False)
    orgaos_acionados: list = field(compare=False, default_factory=list)
 
    def __repr__(self):
        return (
            f"Foco(id={self.id}, nivel={self.nivel_alerta}, "
            f"score={self.severidade_score:.1f}, class={self.classificacao})"
        )
 
 
@dataclass
class Ocorrencia:
    """Registro de ocorrência de incêndio para a pilha histórica."""
    id: int
    focos_ids: list
    area_afetada_ha: float
    nivel_maximo: str
    duracao_horas: float
    brigadas_envolvidas: list
    status: str                # ATIVA / ENCERRADA
    timestamp_inicio: str
    timestamp_fim: Optional[str] = None
    relatorio_gerado: bool = False


#  GRAFO DE MONITORAMENTO

 
class GrafoMonitoramento:
    """
    Grafo de adjacência onde cada nó é uma CelulaMonitoramento de 1km².
    Arestas conectam células vizinhas com peso = fator de propagação do fogo.
    """
 
    def __init__(self):
        self.nos: dict[int, CelulaMonitoramento] = {}
        self.arestas: dict[int, list[tuple[int, float]]] = {}  # {id: [(vizinho_id, peso)]}
 
    def adicionar_celula(self, celula: CelulaMonitoramento):
        self.nos[celula.id] = celula
        if celula.id not in self.arestas:
            self.arestas[celula.id] = []
 
    def adicionar_aresta(self, id_origem: int, id_destino: int, peso: float):
        """Adiciona aresta bidirecional entre células vizinhas."""
        self.arestas[id_origem].append((id_destino, peso))
        self.arestas[id_destino].append((id_origem, peso))
 
    def vizinhos(self, id_celula: int) -> list[tuple[int, float]]:
        return self.arestas.get(id_celula, [])
 
    def total_nos(self) -> int:
        return len(self.nos)
 
    def total_arestas(self) -> int:
        return sum(len(v) for v in self.arestas.values()) // 2
    

 #  FUNÇÕES DEF — LÓGICA DE DOMÍNIO
# ─────────────────────────────────────────────
 
def calcular_risco(celula: CelulaMonitoramento) -> float:
    """
    Calcula o score de risco de incêndio de uma célula (0-100).
 
    Considera temperatura, umidade, vento, NDVI, precipitação e histórico.
    Retorna o score e atualiza celula.score_risco e celula.nivel_risco.
 
    Args:
        celula: CelulaMonitoramento com atributos ambientais preenchidos
 
    Returns:
        float: score de risco entre 0 e 100
    """
    score = 0.0
 
    # Temperatura (peso 25): > 35°C começa a pontuar
    if celula.temperatura > 35:
        score += min(25, (celula.temperatura - 35) * 2.5)
 
    # Umidade relativa (peso 30): inversamente proporcional
    score += (1 - celula.umidade / 100) * 30
 
    # Velocidade do vento (peso 20): > 20 km/h acelera propagação
    if celula.velocidade_vento > 20:
        score += min(20, (celula.velocidade_vento - 20) * 0.5)
 
    # NDVI (peso 15): vegetação densa seca = maior risco
    if celula.ndvi > 0.3:
        score += celula.ndvi * 15
 
    # Precipitação últimas 24h (peso 10): chuva reduz risco
    if celula.precipitacao_24h < 5:
        score += (1 - celula.precipitacao_24h / 5) * 10
 
    # Bônus histórico: regiões com recorrência têm risco aumentado
    if celula.ocorrencias_historicas > 3:
        score = min(100, score * 1.15)
 
    score = round(min(100.0, max(0.0, score)), 2)
    celula.score_risco = score
 
    # Mapeia score para nível de risco
    if score >= 80:
        celula.nivel_risco = NIVEL_EMERGENCIA
    elif score >= 60:
        celula.nivel_risco = NIVEL_ALERTA
    elif score >= 40:
        celula.nivel_risco = NIVEL_ATENCAO
    else:
        celula.nivel_risco = NIVEL_MONITORAMENTO
 
    return score
 
 
def classificar_foco(temperatura_brilho: float, ndvi: float, umidade: float) -> str:
    """
    Classifica um foco de calor detectado por satélite.
 
    Lógica de decisão que simula o modelo de IA do PyroSat.
    Reproduz a regra RN01: foco só gera alerta se CONFIRMADO.
 
    Args:
        temperatura_brilho: temperatura de brilho em Kelvin (GOES-16 Band 7)
        ndvi:               índice de vegetação normalizado (-1.0 a 1.0)
        umidade:            umidade relativa do ar em percentual (0-100)
 
    Returns:
        str: "CONFIRMADO", "SUSPEITO" ou "FALSO"
    """
    # Foco falso: área sem vegetação (solo exposto, água, urbano)
    if ndvi < 0.1:
        return CLASSIFICACAO_FALSO
 
    # Foco confirmado: alta temperatura + vegetação + baixa umidade
    if temperatura_brilho > 340 and ndvi > 0.3 and umidade < 40:
        return CLASSIFICACAO_CONFIRMADO
 
    # Zona de incerteza: suspeito, aguarda confirmação do operador
    if temperatura_brilho > 310 and ndvi > 0.15:
        return CLASSIFICACAO_SUSPEITO
 
    return CLASSIFICACAO_FALSO
 
 
def propagar_fogo(
    grafo: GrafoMonitoramento,
    foco_inicial_id: int,
    horas: int = 6
) -> dict[int, float]:
    """
    Simula a propagação do fogo a partir de um foco usando Dijkstra.
 
    O peso das arestas representa o fator de propagação (vento + vegetação +
    umidade), então o caminho de menor custo = propagação mais provável.
    Retorna o tempo estimado (em horas) para o fogo atingir cada célula.
 
    Args:
        grafo:           GrafoMonitoramento com células e arestas configuradas
        foco_inicial_id: ID da célula onde o foco foi detectado
        horas:           janela de tempo máxima para simulação
 
    Returns:
        dict: {celula_id: horas_para_atingir} — células acessíveis na janela
    """
    if foco_inicial_id not in grafo.nos:
        raise ValueError(f"Célula {foco_inicial_id} não existe no grafo.")
 
    # distancias[id] = horas para o fogo chegar (Dijkstra)
    distancias: dict[int, float] = {foco_inicial_id: 0.0}
    heap = [(0.0, foco_inicial_id)]   # (tempo_acumulado, celula_id)
 
    while heap:
        tempo_atual, celula_id = heapq.heappop(heap)
 
        if tempo_atual > distancias.get(celula_id, math.inf):
            continue  # caminho obsoleto
 
        if tempo_atual > horas:
            continue  # fora da janela de simulação
 
        for vizinho_id, peso_aresta in grafo.vizinhos(celula_id):
            # Tempo para cruzar aresta = inverso do fator de propagação
            # Peso alto = propagação rápida; convertemos para horas
            tempo_propagacao = 1.0 / (peso_aresta + 0.01)
            novo_tempo = tempo_atual + tempo_propagacao
 
            if novo_tempo < distancias.get(vizinho_id, math.inf):
                distancias[vizinho_id] = novo_tempo
                heapq.heappush(heap, (novo_tempo, vizinho_id))
 
    # Retorna apenas células alcançáveis dentro da janela
    return {cid: t for cid, t in distancias.items() if t <= horas}
 
 
def escalonar_alertas(fila_focos: list[FocoCalor]) -> list[FocoCalor]:
    """
    Prioriza e escalona alertas usando fila de prioridade (heapq).
 
    Implementa o protocolo de acionamento em cascata (RN02):
    - Foco EMERGÊNCIA (score 80-100): topo da fila, aciona todos os órgãos
    - Foco ALERTA (score 60-79): aciona Brigada + IBAMA + Defesa Civil
    - Foco ATENÇÃO (score 40-59): aciona Brigada + ICMBio
    - Foco MONITORAMENTO (score < 40): apenas registro interno
 
    Args:
        fila_focos: lista de FocoCalor a ser priorizada
 
    Returns:
        list[FocoCalor]: focos ordenados por prioridade (mais urgente primeiro)
    """
    heap: list[FocoCalor] = []
 
    for foco in fila_focos:
        if foco.classificacao != CLASSIFICACAO_CONFIRMADO:
            continue  # RN01: só focos confirmados geram alertas
 
        # Define órgãos conforme severidade (RN02 — cascata)
        if foco.severidade_score >= 80:
            foco.nivel_alerta = NIVEL_EMERGENCIA
            foco.orgaos_acionados = ["ICMBio", "IBAMA", "Defesa Civil", "Bombeiros", "INPE"]
            foco.prioridade = -foco.severidade_score          # negativo = max-heap via min-heap
 
        elif foco.severidade_score >= 60:
            foco.nivel_alerta = NIVEL_ALERTA
            foco.orgaos_acionados = ["Brigada Local", "IBAMA", "Defesa Civil"]
            foco.prioridade = -foco.severidade_score
 
        elif foco.severidade_score >= 40:
            foco.nivel_alerta = NIVEL_ATENCAO
            foco.orgaos_acionados = ["Brigada Local", "ICMBio"]
            foco.prioridade = -foco.severidade_score
 
        else:
            foco.nivel_alerta = NIVEL_MONITORAMENTO
            foco.orgaos_acionados = []
            foco.prioridade = -foco.severidade_score
 
        heapq.heappush(heap, foco)
 
    # Extrai em ordem de prioridade (maior score primeiro)
    resultado = []
    while heap:
        resultado.append(heapq.heappop(heap))
 
    return resultado
 
 
def busca_bfs_area_risco(
    grafo: GrafoMonitoramento,
    celula_origem_id: int,
    raio_nos: int = 5
) -> list[int]:
    """
    BFS para encontrar todas as células dentro de um raio de nós a partir
    de uma célula de origem. Útil para delimitar área de risco ao redor
    de um foco confirmado.
 
    Args:
        grafo:            GrafoMonitoramento
        celula_origem_id: ID da célula central (foco)
        raio_nos:         quantos "saltos" de célula incluir
 
    Returns:
        list[int]: IDs das células na área de risco
    """
    visitados = {celula_origem_id}
    fila = deque([(celula_origem_id, 0)])
    area_risco = [celula_origem_id]
 
    while fila:
        celula_id, profundidade = fila.popleft()
 
        if profundidade >= raio_nos:
            continue
 
        for vizinho_id, _ in grafo.vizinhos(celula_id):
            if vizinho_id not in visitados:
                visitados.add(vizinho_id)
                fila.append((vizinho_id, profundidade + 1))
                area_risco.append(vizinho_id)
 
    return area_risco   
 

#  PILHA — HISTÓRICO DE OCORRÊNCIAS (LIFO)

 
class PilhaOcorrencias:
    """
    Pilha LIFO para gerenciar o histórico de ocorrências de uma área.
 
    Operações:
        push   — registra nova ocorrência
        pop    — remove a mais recente (usado para "desfazer alerta" / cancelar falso positivo)
        peek   — consulta a mais recente sem remover
        buscar — percorre a pilha para relatório
    """
 
    def __init__(self, area_id: int):
        self.area_id = area_id
        self._pilha: list[Ocorrencia] = []
 
    def push(self, ocorrencia: Ocorrencia):
        """Empilha nova ocorrência (push)."""
        self._pilha.append(ocorrencia)
        print(f"  [PILHA] Ocorrência {ocorrencia.id} registrada na área {self.area_id}.")
 
    def pop(self) -> Optional[Ocorrencia]:
        """Desempilha a ocorrência mais recente (pop — desfazer/cancelar)."""
        if not self._pilha:
            print("  [PILHA] Pilha vazia, nenhuma ocorrência para remover.")
            return None
        ocorrencia = self._pilha.pop()
        print(f"  [PILHA] Ocorrência {ocorrencia.id} removida (cancelada/falso positivo).")
        return ocorrencia
 
    def peek(self) -> Optional[Ocorrencia]:
        """Retorna a ocorrência mais recente sem remover."""
        return self._pilha[-1] if self._pilha else None
 
    def listar_historico(self) -> list[Ocorrencia]:
        """Retorna ocorrências em ordem LIFO (mais recente primeiro)."""
        return list(reversed(self._pilha))
 
    def total(self) -> int:
        return len(self._pilha)
 
    def esta_vazia(self) -> bool:
        return len(self._pilha) == 0
    

#  SIMULAÇÃO COMPLETA — DEMO

 
def criar_grafo_exemplo(num_celulas: int = 20) -> GrafoMonitoramento:
    """
    Gera um grafo de exemplo com num_celulas células interligadas
    simulando uma região monitorada pelo PyroSat.
    """
    random.seed(42)
    grafo = GrafoMonitoramento()
 
    for i in range(num_celulas):
        celula = CelulaMonitoramento(
            id=i,
            latitude=-12.0 + (i // 5) * 0.01,
            longitude=-47.0 + (i % 5) * 0.01,
            municipio=f"Município-{i % 5}",
            estado="TO",
            bioma=random.choice(BIOMAS),
            temperatura=random.uniform(28, 45),
            umidade=random.uniform(15, 80),
            velocidade_vento=random.uniform(5, 50),
            direcao_vento=random.uniform(0, 360),
            precipitacao_24h=random.uniform(0, 20),
            pressao_atmosferica=random.uniform(980, 1020),
            indice_calor=random.uniform(30, 50),
            ponto_orvalho=random.uniform(10, 25),
            radiacao_solar=random.uniform(200, 1000),
            visibilidade_km=random.uniform(5, 50),
            ndvi=random.uniform(-0.1, 0.8),
            tipo_vegetacao=random.choice(["Savana", "Floresta", "Campo", "Mata ciliar"]),
            densidade_florestal=random.uniform(0.1, 1.0),
            altura_media_vegetacao_m=random.uniform(0.5, 30.0),
            percentual_vegetacao_seca=random.uniform(10, 90),
            carga_combustivel_ton_ha=random.uniform(2, 25),
            indice_umidade_combustivel=random.uniform(5, 200),
            especie_dominante=random.choice(["Cerradão", "Buriti", "Ipê", "Aroeira", "Capim-colonião"]),
            ocorrencias_historicas=random.randint(0, 8),
            ultimo_incendio_anos=random.uniform(0, 10),
            area_total_queimada_historica_ha=random.uniform(0, 5000),
            recorrencia_media_anos=random.uniform(1, 15),
            maior_incendio_registrado_ha=random.uniform(100, 10000),
            distancia_brigada_km=random.uniform(5, 100),
            tem_torre_observacao=random.choice([True, False]),
            tem_sensor_iot=random.choice([True, False]),
            distancia_estrada_km=random.uniform(1, 50),
            distancia_corpo_hidrico_km=random.uniform(0.5, 30),
            tem_aceiro=random.choice([True, False]),
            capacidade_tanque_agua_l=random.uniform(0, 50000),
            cobertura_satelite=random.choice(["GOES-16", "Sentinel-2", "VIIRS"]),
            temperatura_superficie_k=random.uniform(290, 340),
            reflectancia_banda_swir=random.uniform(0.0, 0.5),
            anomalia_termica_mw=random.uniform(0, 200),
            ultima_passagem_satelite=f"2025-06-01 {6 + (i % 12):02d}:00:00",
            indice_nbr=random.uniform(-0.5, 0.8),
            indice_evi=random.uniform(0.0, 0.9),
        )
        grafo.adicionar_celula(celula)
 
    # Conecta células em grade (vizinhos ortogonais e diagonais)
    for i in range(num_celulas):
        for j in range(i + 1, num_celulas):
            if abs(i - j) in [1, 5]:  # vizinhos horizontais/verticais
                celula_i = grafo.nos[i]
                celula_j = grafo.nos[j]
                # Peso = fator de propagação baseado em vento e vegetação
                peso = (celula_i.velocidade_vento / 50 + celula_i.ndvi) / 2
                grafo.adicionar_aresta(i, j, round(peso, 3))
 
    return grafo
 
 
def gerar_focos_exemplo(grafo: GrafoMonitoramento, qtd: int = 8) -> list[FocoCalor]:
    """Gera focos de calor sintéticos para demonstração."""
    random.seed(7)
    focos = []
    celulas = list(grafo.nos.values())[:qtd]
 
    for i, celula in enumerate(celulas):
        # Primeiros 3 focos forçados como condições de incêndio real (didático)
        if i < 3:
            temp_brilho = random.uniform(345, 380)
            ndvi_val = random.uniform(0.4, 0.8)
            umidade_val = random.uniform(10, 35)
            celula.temperatura = random.uniform(38, 45)
            celula.umidade = umidade_val
            celula.ndvi = ndvi_val
        else:
            temp_brilho = random.uniform(295, 340)
            ndvi_val = celula.ndvi
            umidade_val = celula.umidade
 
        classificacao = classificar_foco(temp_brilho, ndvi_val, umidade_val)
        score = calcular_risco(celula)
 
        foco = FocoCalor(
            prioridade=0.0,
            id=i,
            celula_id=celula.id,
            latitude=celula.latitude,
            longitude=celula.longitude,
            temperatura_brilho=temp_brilho,
            frp=random.uniform(5, 500),
            classificacao=classificacao,
            severidade_score=score,
            nivel_alerta=celula.nivel_risco,
            fonte_satelite=celula.cobertura_satelite,
            timestamp=f"2025-06-01 {8 + i:02d}:00:00",
        )
        focos.append(foco)
 
    return focos
 
 
def executar_simulacao():
    """
    Simulação completa do PyroSat integrando todas as estruturas:
    grafo, fila de prioridade, pilha e funções def.
    """
    print("=" * 60)
    print("   PyroSat — Simulação de Detecção e Alerta de Incêndios")
    print("=" * 60)
 
    # 1. Constrói o grafo de monitoramento
    print("\n[1] Construindo grafo de monitoramento...")
    grafo = criar_grafo_exemplo(num_celulas=20)
    print(f"    Grafo criado: {grafo.total_nos()} células, {grafo.total_arestas()} arestas")
 
    # 2. Calcula risco de todas as células
    print("\n[2] Calculando score de risco para cada célula...")
    for celula in grafo.nos.values():
        calcular_risco(celula)
    celulas_alerta = [c for c in grafo.nos.values() if c.nivel_risco in [NIVEL_ALERTA, NIVEL_EMERGENCIA]]
    print(f"    Células em ALERTA ou EMERGÊNCIA: {len(celulas_alerta)}")
    for c in celulas_alerta:
        print(f"      → {c}")
 
    # 3. Detecta e classifica focos de calor
    print("\n[3] Detectando e classificando focos de calor (satélite)...")
    focos = gerar_focos_exemplo(grafo, qtd=8)
    confirmados = [f for f in focos if f.classificacao == CLASSIFICACAO_CONFIRMADO]
    suspeitos   = [f for f in focos if f.classificacao == CLASSIFICACAO_SUSPEITO]
    falsos      = [f for f in focos if f.classificacao == CLASSIFICACAO_FALSO]
    print(f"    Total detectado: {len(focos)} focos")
    print(f"    Confirmados: {len(confirmados)} | Suspeitos: {len(suspeitos)} | Falsos: {len(falsos)}")
 
    # 4. Escalonamento via fila de prioridade
    print("\n[4] Escalonando alertas por prioridade (fila heapq)...")
    fila_escalonada = escalonar_alertas(focos)
    print(f"    {len(fila_escalonada)} focos confirmados na fila:")
    for foco in fila_escalonada:
        print(f"      → {foco} | Órgãos: {foco.orgaos_acionados}")
 
    # 5. Simulação de propagação do fogo (Dijkstra)
    if confirmados:
        foco_principal = confirmados[0]
        print(f"\n[5] Simulando propagação do fogo a partir do foco {foco_principal.id} (Dijkstra, 6h)...")
        propagacao = propagar_fogo(grafo, foco_inicial_id=foco_principal.celula_id, horas=6)
        print(f"    Fogo pode atingir {len(propagacao)} células em até 6 horas:")
        for cid, t in sorted(propagacao.items(), key=lambda x: x[1])[:5]:
            print(f"      → Célula {cid}: ~{t:.2f}h")
 
        # 6. BFS — delimita área de risco
        print(f"\n[6] BFS: mapeando área de risco (raio 3 nós ao redor do foco)...")
        area = busca_bfs_area_risco(grafo, foco_principal.celula_id, raio_nos=3)
        print(f"    {len(area)} células na área de risco: {area}")
 
    # 7. Pilha de ocorrências (LIFO)
    print("\n[7] Gerenciando histórico de ocorrências com pilha LIFO...")
    pilha = PilhaOcorrencias(area_id=1)
 
    oc1 = Ocorrencia(
        id=1001, focos_ids=[0, 1], area_afetada_ha=120.5,
        nivel_maximo=NIVEL_ALERTA, duracao_horas=8.0,
        brigadas_envolvidas=["Brigada Norte", "Brigada Central"],
        status="ENCERRADA", timestamp_inicio="2025-06-01 08:00",
        timestamp_fim="2025-06-01 16:00", relatorio_gerado=True
    )
    oc2 = Ocorrencia(
        id=1002, focos_ids=[2], area_afetada_ha=45.0,
        nivel_maximo=NIVEL_EMERGENCIA, duracao_horas=3.5,
        brigadas_envolvidas=["Brigada Sul"],
        status="ATIVA", timestamp_inicio="2025-06-01 14:30"
    )
    oc3 = Ocorrencia(
        id=1003, focos_ids=[5], area_afetada_ha=0.0,
        nivel_maximo=NIVEL_ATENCAO, duracao_horas=0.5,
        brigadas_envolvidas=[],
        status="ENCERRADA", timestamp_inicio="2025-06-01 15:00",
        timestamp_fim="2025-06-01 15:30"
    )
 
    pilha.push(oc1)
    pilha.push(oc2)
    pilha.push(oc3)
 
    print(f"    Total na pilha: {pilha.total()} ocorrências")
    print(f"    Mais recente (peek): Ocorrência {pilha.peek().id}")
 
    print("\n    Cancelando última ocorrência (falso positivo — pop):")
    pilha.pop()
    print(f"    Total após remoção: {pilha.total()}")
 
    print("\n    Histórico LIFO (mais recente primeiro):")
    for oc in pilha.listar_historico():
        print(f"      → Ocorrência {oc.id} | Status: {oc.status} | Área: {oc.area_afetada_ha}ha")
 
    print("\n" + "=" * 60)
    print("   Simulação concluída com sucesso!")
    print("=" * 60)
 
 
#  ENTRYPOINT
 
if __name__ == "__main__":
    executar_simulacao()    