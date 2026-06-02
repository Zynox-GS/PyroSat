"""
PyroSat Global - Global Wildfire Detection & Early Warning System

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
import time
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

# Biomas Globais
BIOMAS = ["Savana", "Floresta Tropical", "Tundra", "Taiga", "Deserto", "Floresta Temperada"]


# DATACLASSES 

@dataclass
class CelulaMonitoramento:
    
    # Identificação
    id: int
    latitude: float
    longitude: float
    municipio: str  # Representará Cidade/Província globalmente
    estado: str     # Representará País/Região globalmente
    bioma: str

    # Condições ambientais
    temperatura: float       
    umidade: float           
    velocidade_vento: float     
    direcao_vento: float       
    precipitacao_24h: float    
    pressao_atmosferica: float  
    indice_calor: float         
    ponto_orvalho: float        
    radiacao_solar: float      
    visibilidade_km: float      

    # Cobertura vegetal
    ndvi: float               
    tipo_vegetacao: str
    densidade_florestal: float  
    altura_media_vegetacao_m: float      
    percentual_vegetacao_seca: float     
    carga_combustivel_ton_ha: float       
    indice_umidade_combustivel: float     
    especie_dominante: str                

    # Risco calculado
    score_risco: float = 0.0                 
    nivel_risco: str = NIVEL_MONITORAMENTO
    indice_fwi: float = 0.0                 
    probabilidade_propagacao: float = 0.0   
    velocidade_propagacao_kmh: float = 0.0   

    # Estado do foco
    tem_foco_ativo: bool = False
    classificacao_foco: Optional[str] = None
    timestamp_deteccao: Optional[str] = None
    area_queimada_ha: float = 0.0       
    perimetro_fogo_km: float = 0.0      

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
    temperatura_superficie_c: float = 0.0
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
    
    prioridade: float = field(compare=True)   
    id: int = field(compare=False)
    celula_id: int = field(compare=False)
    latitude: float = field(compare=False)
    longitude: float = field(compare=False)
    temperatura_brilho: float = field(compare=False)  # temperatura de brilho em °C
    frp: float = field(compare=False)                  
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
    id: int
    focos_ids: list
    area_afetada_ha: float
    nivel_maximo: str
    duracao_horas: float
    brigadas_envolvidas: list
    status: str
    timestamp_inicio: str
    timestamp_fim: Optional[str] = None
    relatorio_gerado: bool = False


# GRAFO DE MONITORAMENTO

class GrafoMonitoramento:
    
    def __init__(self):
        self.nos: dict[int, CelulaMonitoramento] = {}
        self.arestas: dict[int, list[tuple[int, float]]] = {}

    def adicionar_celula(self, celula: CelulaMonitoramento):
        self.nos[celula.id] = celula
        if celula.id not in self.arestas:
            self.arestas[celula.id] = []

    def adicionar_aresta(self, id_origem: int, id_destino: int, peso: float):
        self.arestas[id_origem].append((id_destino, peso))
        self.arestas[id_destino].append((id_origem, peso))

    def vizinhos(self, id_celula: int) -> list[tuple[int, float]]:
        return self.arestas.get(id_celula, [])

    def total_nos(self) -> int:
        return len(self.nos)

    def total_arestas(self) -> int:
        return sum(len(v) for v in self.arestas.values()) // 2
    

# FUNÇÕES DEF — LÓGICA DE DOMÍNIO
# ─────────────────────────────────────────────

def calcular_risco(celula: CelulaMonitoramento) -> float:
    
    score = 0.0

    if celula.temperatura > 35:
        score += min(25, (celula.temperatura - 35) * 2.5)

    score += (1 - celula.umidade / 100) * 30

    if celula.velocidade_vento > 20:
        score += min(20, (celula.velocidade_vento - 20) * 0.5)

    if celula.ndvi > 0.3:
        score += celula.ndvi * 15

    if celula.precipitacao_24h < 5:
        score += (1 - celula.precipitacao_24h / 5) * 10

    if celula.ocorrencias_historicas > 3:
        score = min(100, score * 1.15)

    score = round(min(100.0, max(0.0, score)), 2)
    celula.score_risco = score

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
    
    if ndvi < 0.1:
        return CLASSIFICACAO_FALSO

    # Ajustado para Celsius: > 200°C = Fogo Real
    if temperatura_brilho > 200 and ndvi > 0.3 and umidade < 40:
        return CLASSIFICACAO_CONFIRMADO

    # Ajustado para Celsius: > 60°C = Suspeito
    if temperatura_brilho > 60 and ndvi > 0.15:
        return CLASSIFICACAO_SUSPEITO

    return CLASSIFICACAO_FALSO


def propagar_fogo(
    grafo: GrafoMonitoramento,
    foco_inicial_id: int,
    horas: int = 6
) -> dict[int, float]:
    
    if foco_inicial_id not in grafo.nos:
        raise ValueError(f"Célula {foco_inicial_id} não existe no grafo.")

    distancias: dict[int, float] = {foco_inicial_id: 0.0}
    heap = [(0.0, foco_inicial_id)] 

    while heap:
        tempo_atual, celula_id = heapq.heappop(heap)

        if tempo_atual > distancias.get(celula_id, math.inf):
            continue  

        if tempo_atual > horas:
            continue 

        for vizinho_id, peso_aresta in grafo.vizinhos(celula_id):
            
            tempo_propagacao = 1.0 / (peso_aresta + 0.01)
            novo_tempo = tempo_atual + tempo_propagacao

            if novo_tempo < distancias.get(vizinho_id, math.inf):
                distancias[vizinho_id] = novo_tempo
                heapq.heappush(heap, (novo_tempo, vizinho_id))

    return {cid: t for cid, t in distancias.items() if t <= horas}


def escalonar_alertas(fila_focos: list[FocoCalor]) -> list[FocoCalor]:
    
    heap: list[FocoCalor] = []

    for foco in fila_focos:
        if foco.classificacao != CLASSIFICACAO_CONFIRMADO:
            continue

        if foco.severidade_score >= 80:
            foco.nivel_alerta = NIVEL_EMERGENCIA
            foco.orgaos_acionados = ["Agência Ambiental Global (UNEP)", "Defesa Civil Nacional", "Bombeiros Internacionais", "Agência Espacial"]
            foco.prioridade = -foco.severidade_score

        elif foco.severidade_score >= 60:
            foco.nivel_alerta = NIVEL_ALERTA
            foco.orgaos_acionados = ["Brigada Local", "Defesa Civil Regional", "Autoridade Florestal"]
            foco.prioridade = -foco.severidade_score

        elif foco.severidade_score >= 40:
            foco.nivel_alerta = NIVEL_ATENCAO
            foco.orgaos_acionados = ["Brigada Local", "Monitoramento Florestal Regional"]
            foco.prioridade = -foco.severidade_score

        else:
            foco.nivel_alerta = NIVEL_MONITORAMENTO
            foco.orgaos_acionados = []
            foco.prioridade = -foco.severidade_score

        heapq.heappush(heap, foco)

    resultado = []
    while heap:
        resultado.append(heapq.heappop(heap))

    return resultado


def busca_bfs_area_risco(
    grafo: GrafoMonitoramento,
    celula_origem_id: int,
    raio_nos: int = 5
) -> list[int]:
    
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
 

# PILHA — HISTÓRICO DE OCORRÊNCIAS (LIFO)

class PilhaOcorrencias:
    
    def __init__(self, area_id: int):
        self.area_id = area_id
        self._pilha: list[Ocorrencia] = []

    def push(self, ocorrencia: Ocorrencia):
        self._pilha.append(ocorrencia)
        print(f"  [PILHA] Ocorrência {ocorrencia.id} registrada na zona global {self.area_id}.")

    def pop(self) -> Optional[Ocorrencia]:
        if not self._pilha:
            print("  [PILHA] Pilha vazia, nenhuma ocorrência para remover.")
            return None
        ocorrencia = self._pilha.pop()
        print(f"  [PILHA] Ocorrência {ocorrencia.id} removida (cancelada/falso positivo).")
        return ocorrencia

    def peek(self) -> Optional[Ocorrencia]:
        return self._pilha[-1] if self._pilha else None

    def listar_historico(self) -> list[Ocorrencia]:
        return list(reversed(self._pilha))

    def total(self) -> int:
        return len(self._pilha)

    def esta_vazia(self) -> bool:
        return len(self._pilha) == 0
    

# SIMULAÇÃO COMPLETA — DEMO

def criar_grafo_exemplo(num_celulas: int = 20) -> GrafoMonitoramento:
    random.seed(42)
    grafo = GrafoMonitoramento()

    for i in range(num_celulas):
        celula = CelulaMonitoramento(
            id=i,
            latitude=-12.0 + (i // 5) * 0.01,
            longitude=-47.0 + (i % 5) * 0.01,
            municipio=f"City-{i % 5}",
            estado=random.choice(["Region-Alpha", "Region-Beta", "Region-Gamma"]),
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
            tipo_vegetacao=random.choice(["Savana", "Floresta Densa", "Pradaria", "Mata Temperada"]),
            densidade_florestal=random.uniform(0.1, 1.0),
            altura_media_vegetacao_m=random.uniform(0.5, 30.0),
            percentual_vegetacao_seca=random.uniform(10, 90),
            carga_combustivel_ton_ha=random.uniform(2, 25),
            indice_umidade_combustivel=random.uniform(5, 200),
            especie_dominante=random.choice(["Coníferas", "Eucaliptos", "Carvalhos", "Acácias", "Gramíneas Globais"]),
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
            temperatura_superficie_c=random.uniform(16.85, 66.85),
            reflectancia_banda_swir=random.uniform(0.0, 0.5),
            anomalia_termica_mw=random.uniform(0, 200),
            ultima_passagem_satelite=f"2025-06-01 {6 + (i % 12):02d}:00:00",
            indice_nbr=random.uniform(-0.5, 0.8),
            indice_evi=random.uniform(0.0, 0.9),
        )
        grafo.adicionar_celula(celula)

    for i in range(num_celulas):
        for j in range(i + 1, num_celulas):
            if abs(i - j) in [1, 5]:
                celula_i = grafo.nos[i]
                celula_j = grafo.nos[j]
                peso = (celula_i.velocidade_vento / 50 + celula_i.ndvi) / 2
                grafo.adicionar_aresta(i, j, round(peso, 3))

    return grafo


def gerar_focos_exemplo(grafo: GrafoMonitoramento, qtd: int = 8) -> list[FocoCalor]:
    random.seed(7)
    focos = []
    celulas = list(grafo.nos.values())[:qtd]

    for i, celula in enumerate(celulas):
        if i < 3:
            # Focos confirmados gerados entre 450°C e 850°C (Suficiente para disparar Alerta e Emergência no Java)
            temp_brilho = random.uniform(450.0, 850.0)
            ndvi_val = random.uniform(0.4, 0.8)
            umidade_val = random.uniform(10, 35)
            celula.temperatura = random.uniform(38, 45)
            celula.umidade = umidade_val
            celula.ndvi = ndvi_val
        else:
            # Focos suspeitos ou falsos gerados entre 40°C e 150°C
            temp_brilho = random.uniform(40.0, 150.0)
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
    print("=" * 60)
    print("   PyroSat GLOBAL — Simulação de Detecção e Alerta de Incêndios")
    print("=" * 60)

    print("\n[1] Construindo grafo de monitoramento global...")
    grafo = criar_grafo_exemplo(num_celulas=20)
    print(f"    Grafo criado: {grafo.total_nos()} células, {grafo.total_arestas()} arestas")
    time.sleep(2)

    print("\n[2] Calculando score de risco para cada célula...")
    for celula in grafo.nos.values():
        calcular_risco(celula)
    celulas_alerta = [c for c in grafo.nos.values() if c.nivel_risco in [NIVEL_ALERTA, NIVEL_EMERGENCIA]]
    print(f"    Células em ALERTA ou EMERGÊNCIA: {len(celulas_alerta)}")
    for c in celulas_alerta:
        print(f"      → {c}")
    time.sleep(2)

    print("\n[3] Detectando e classificando focos de calor (satélite)...")
    focos = gerar_focos_exemplo(grafo, qtd=8)
    confirmados = [f for f in focos if f.classificacao == CLASSIFICACAO_CONFIRMADO]
    suspeitos   = [f for f in focos if f.classificacao == CLASSIFICACAO_SUSPEITO]
    falsos      = [f for f in focos if f.classificacao == CLASSIFICACAO_FALSO]
    print(f"    Total detectado: {len(focos)} focos")
    print(f"    Confirmados: {len(confirmados)} | Suspeitos: {len(suspeitos)} | Falsos: {len(falsos)}")
    time.sleep(2)

    print("\n[4] Escalonando alertas por prioridade (fila heapq)...")
    fila_escalonada = escalonar_alertas(focos)
    print(f"    {len(fila_escalonada)} focos confirmados na fila:")
    for foco in fila_escalonada:
        print(f"      → {foco} | Órgãos/Agências Acionadas: {foco.orgaos_acionados}")
    time.sleep(2)

    if confirmados:
        foco_principal = confirmados[0]
        print(f"\n[5] Simulando propagação do fogo a partir do foco {foco_principal.id} (Dijkstra, 6h)...")
        propagacao = propagar_fogo(grafo, foco_inicial_id=foco_principal.celula_id, horas=6)
        print(f"    Fogo pode atingir {len(propagacao)} células em até 6 horas:")
        for cid, t in sorted(propagacao.items(), key=lambda x: x[1])[:5]:
            print(f"      → Célula {cid}: ~{t:.2f}h")
        time.sleep(2)

        print(f"\n[6] BFS: mapeando zona de risco global (raio 3 nós ao redor do foco)...")
        area = busca_bfs_area_risco(grafo, foco_principal.celula_id, raio_nos=3)
        print(f"    {len(area)} células na zona de risco: {area}")
        time.sleep(2)

    print("\n[7] Gerenciando histórico de ocorrências com pilha LIFO...")
    pilha = PilhaOcorrencias(area_id=1)

    oc1 = Ocorrencia(
        id=1001, focos_ids=[0, 1], area_afetada_ha=120.5,
        nivel_maximo=NIVEL_ALERTA, duracao_horas=8.0,
        brigadas_envolvidas=["Brigada Norte (Alpha)", "Brigada Central (Beta)"],
        status="ENCERRADA", timestamp_inicio="2025-06-01 08:00",
        timestamp_fim="2025-06-01 16:00", relatorio_gerado=True
    )
    oc2 = Ocorrencia(
        id=1002, focos_ids=[2], area_afetada_ha=45.0,
        nivel_maximo=NIVEL_EMERGENCIA, duracao_horas=3.5,
        brigadas_envolvidas=["Esquadrão de Resgate Sul"],
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
    time.sleep(2)

    print(f"    Total na pilha: {pilha.total()} ocorrências")
    print(f"    Mais recente (peek): Ocorrência {pilha.peek().id}")

    print("\n    Cancelando última ocorrência (falso positivo — pop):")
    pilha.pop()
    print(f"    Total após remoção: {pilha.total()}")

    print("\n    Histórico LIFO (mais recente primeiro):")
    for oc in pilha.listar_historico():
        print(f"      → Ocorrência {oc.id} | Status: {oc.status} | Área: {oc.area_afetada_ha}ha")

    print("\n" + "=" * 60)
    print("   Simulação global concluída com sucesso!")
    print("=" * 60)


if __name__ == "__main__":
    executar_simulacao()