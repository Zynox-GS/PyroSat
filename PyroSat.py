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
 
    # Cobertura vegetal
    ndvi: float                 # -1.0 a 1.0 (índice vegetação)
    tipo_vegetacao: str
    densidade_florestal: float  # 0.0 a 1.0
 
    # Risco calculado
    score_risco: float = 0.0    # 0-100 (calculado por calcular_risco)
    nivel_risco: str = NIVEL_MONITORAMENTO
 
    # Estado do foco
    tem_foco_ativo: bool = False
    classificacao_foco: Optional[str] = None
    timestamp_deteccao: Optional[str] = None
 
    # Histórico
    ocorrencias_historicas: int = 0
    ultimo_incendio_anos: float = 0.0
 
    # Infraestrutura
    distancia_brigada_km: float = 0.0
    tem_torre_observacao: bool = False
    tem_sensor_iot: bool = False
    cobertura_satelite: str = "GOES-16"
 
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