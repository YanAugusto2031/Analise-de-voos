"""
Free tier: 100 requisicoes/mes -> use com moderacao (ex: 1 aeroporto por
execucao, revezando ao longo da semana).
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))
from common.common.aeroportos import distancia_km  # noqa: E402

BASE_URL = "http://api.aviationstack.com/v1/flights"


def buscar_voos_por_aeroporto(iata_code: str, api_key: str, limit: int = 100) -> list[dict]:
    """Busca voos com partida no aeroporto informado (chegadas: use dep_iata -> arr_iata)."""
    params = {
        "access_key": api_key,
        "dep_iata": iata_code,
        "limit": limit,
    }
    resp = requests.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        raise RuntimeError(f"Erro da API AviationStack: {data['error']}")

    return data.get("data", [])


def _diferenca_min(inicio: str | None, fim: str | None) -> int | None:
    """Diferenca em minutos entre dois horarios ISO 8601. Usado tanto para
    atraso (previsto vs real) quanto para duracao (partida vs chegada)."""
    if not inicio or not fim:
        return None
    try:
        t_inicio = datetime.fromisoformat(inicio.replace("Z", "+00:00"))
        t_fim = datetime.fromisoformat(fim.replace("Z", "+00:00"))
        return int((t_fim - t_inicio).total_seconds() / 60)
    except (ValueError, TypeError):
        return None


def voos_para_dataframe(voos_raw: list[dict]) -> pd.DataFrame:
    """Converte a resposta bruta da API em um DataFrame ja tratado."""
    agora = datetime.now(timezone.utc).isoformat()
    registros = []

    for voo in voos_raw:
        dep = voo.get("departure", {}) or {}
        arr = voo.get("arrival", {}) or {}
        aeronave = voo.get("aircraft") or {}
        airline = voo.get("airline", {}) or {}
        flight = voo.get("flight", {}) or {}

        origem = dep.get("iata")
        destino = arr.get("iata")

        horario_previsto_partida = dep.get("scheduled")
        horario_real_partida = dep.get("actual")
        horario_previsto_chegada = arr.get("scheduled")
        horario_real_chegada = arr.get("actual")

        data_partida = horario_previsto_partida or ""
        dia_semana = None
        if data_partida:
            try:
                dia_semana = datetime.fromisoformat(
                    data_partida.replace("Z", "+00:00")
                ).strftime("%A")
            except ValueError:
                dia_semana = None

        # Duracao: usa horarios reais quando disponiveis, senao os previstos
        duracao_min = _diferenca_min(
            horario_real_partida or horario_previsto_partida,
            horario_real_chegada or horario_previsto_chegada,
        )

        registros.append(
            {
                "data_coleta": agora,
                "numero_voo": flight.get("iata"),
                "companhia": airline.get("iata"),
                "origem": origem,
                "destino": destino,
                "terminal_origem": dep.get("terminal"),
                "portao_origem": dep.get("gate"),
                "terminal_destino": arr.get("terminal"),
                "portao_destino": arr.get("gate"),
                "horario_previsto_partida": horario_previsto_partida,
                "horario_real_partida": horario_real_partida,
                "horario_previsto_chegada": horario_previsto_chegada,
                "horario_real_chegada": horario_real_chegada,
                "atraso_partida_min": _diferenca_min(horario_previsto_partida, horario_real_partida),
                "atraso_chegada_min": _diferenca_min(horario_previsto_chegada, horario_real_chegada),
                "status": voo.get("flight_status"),
                "duracao_min": duracao_min,
                "distancia_km": distancia_km(origem, destino),
                "dia_semana": dia_semana,
                "modelo_aeronave": aeronave.get("iata"),
                "aeronave_icao24": aeronave.get("icao24"),
                "aeronave_fabricante": None,  # AviationStack nao traz o fabricante separado
            }
        )

    return pd.DataFrame(registros)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    key = os.environ["AVIATIONSTACK_API_KEY"]

    voos = buscar_voos_por_aeroporto("GRU", key)
    df = voos_para_dataframe(voos)
    print(df.head())
    print(f"\n{len(df)} voos coletados.")