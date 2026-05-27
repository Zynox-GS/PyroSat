import heapq
import math
import random
from collections import deque
from dataclasses import dataclass, field
from typing import Optional


CLASSIFICACAO_SUSPEITO   = "SUSPEITO"
CLASSIFICACAO_CONFIRMADO = "CONFIRMADO"
CLASSIFICACAO_FALSO      = "FALSO"
 
NIVEL_MONITORAMENTO = "MONITORAMENTO"
NIVEL_ATENCAO       = "ATENÇÃO"
NIVEL_ALERTA        = "ALERTA"
NIVEL_EMERGENCIA    = "EMERGÊNCIA"
 
BIOMAS = ["Cerrado", "Amazônia", "Pantanal", "Mata Atlântica", "Caatinga", "Pampa"]