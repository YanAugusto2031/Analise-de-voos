"""
Dados e funcoes compartilhadas entre db/init_db.py e extract/aviationstack.py:
lista de aeroportos brasileiros (com coordenadas) e calculo de distancia
entre dois pontos (formula de haversine).
"""

import math

# iata, nome, cidade, uf, pais, lat, lon, fuso
AEROPORTOS_BRASIL = [
    ("GRU", "Aeroporto Internacional de Guarulhos", "Guarulhos", "SP", "Brasil", -23.4356, -46.4731, "America/Sao_Paulo"),
    ("CGH", "Aeroporto de Congonhas", "São Paulo", "SP", "Brasil", -23.6266, -46.6553, "America/Sao_Paulo"),
    ("GIG", "Aeroporto Internacional do Galeão", "Rio de Janeiro", "RJ", "Brasil", -22.8099, -43.2505, "America/Sao_Paulo"),
    ("SDU", "Aeroporto Santos Dumont", "Rio de Janeiro", "RJ", "Brasil", -22.9105, -43.1631, "America/Sao_Paulo"),
    ("BSB", "Aeroporto Internacional de Brasília", "Brasília", "DF", "Brasil", -15.8697, -47.9208, "America/Sao_Paulo"),
    ("SSA", "Aeroporto Internacional de Salvador", "Salvador", "BA", "Brasil", -12.9086, -38.3225, "America/Bahia"),
    ("CNF", "Aeroporto Internacional de Confins", "Belo Horizonte", "MG", "Brasil", -19.6244, -43.9719, "America/Sao_Paulo"),
    ("POA", "Aeroporto Internacional Salgado Filho", "Porto Alegre", "RS", "Brasil", -29.9944, -51.1714, "America/Sao_Paulo"),
    ("REC", "Aeroporto Internacional do Recife", "Recife", "PE", "Brasil", -8.1264, -34.9236, "America/Recife"),
    ("CWB", "Aeroporto Internacional Afonso Pena", "Curitiba", "PR", "Brasil", -25.5285, -49.1758, "America/Sao_Paulo"),
    ("FOR", "Aeroporto Internacional Pinto Martins", "Fortaleza", "CE", "Brasil", -3.7763, -38.5326, "America/Fortaleza"),
    ("BEL", "Aeroporto Internacional de Belém", "Belém", "PA", "Brasil", -1.3792, -48.4761, "America/Belem"),
    ("MAO", "Aeroporto Internacional Eduardo Gomes", "Manaus", "AM", "Brasil", -3.0386, -60.0497, "America/Manaus"),
    ("VCP", "Aeroporto Internacional de Viracopos", "Campinas", "SP", "Brasil", -23.0074, -47.1345, "America/Sao_Paulo"),
]

# Lookup rapido: iata -> (lat, lon)
COORDENADAS = {linha[0]: (linha[5], linha[6]) for linha in AEROPORTOS_BRASIL}


def distancia_km(origem_iata: str | None, destino_iata: str | None) -> float | None:
    """Distancia em linha reta (haversine) entre dois aeroportos conhecidos.
    Retorna None se algum dos codigos IATA nao estiver no dicionario COORDENADAS
    (ex: aeroporto fora do Brasil, ainda nao cadastrado)."""
    if not origem_iata or not destino_iata:
        return None
    if origem_iata not in COORDENADAS or destino_iata not in COORDENADAS:
        return None

    lat1, lon1 = COORDENADAS[origem_iata]
    lat2, lon2 = COORDENADAS[destino_iata]

    R = 6371.0  # raio da Terra em km
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return round(R * c, 1)