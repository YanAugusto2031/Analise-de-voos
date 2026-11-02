"""Busca informações de status de voos na API AviationStack.

Documentação: https://aviationstack.com/documentation
Confira os limites do plano antes de aumentar a quantidade de aeroportos.
"""

import os
from datetime import datetime, timezone

import requests
import pandas as pd

BASE_URL = "http://api.aviationstack.com/v1/flights"
DIAS_SEMANA = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]

# Os rótulos em português são usados diretamente nos relatórios.
STATUS_VOO = {
    "scheduled": "Programado",
    "active": "Em voo",
    "landed": "Pousou",
    "cancelled": "Cancelado",
    "incident": "Incidente",
    "diverted": "Desviado",
}

def buscar_voos_por_aeroporto(iata_code: str, api_key: str, limit: int = 100) -> list[dict]:
    """Busca voos que partem do aeroporto informado pelo código IATA."""
    params = {
        "access_key": api_key,
        "dep_iata": iata_code,
        "limit": limit,
    }
    resp = requests.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    # Algumas falhas da API chegam dentro do JSON, mesmo com resposta HTTP válida.
    if "error" in data:
        raise RuntimeError(f"Erro da API AviationStack: {data['error']}")

    return data.get("data", [])


def voos_para_dataframe(voos_raw: list[dict]) -> pd.DataFrame:
    """Seleciona e organiza as informações usadas pela tabela voos_status."""
    agora = datetime.now(timezone.utc).isoformat()
    registros = []

    for voo in voos_raw:
        dep = voo.get("departure", {}) or {}
        arr = voo.get("arrival", {}) or {}
        airline = voo.get("airline", {}) or {}
        flight = voo.get("flight", {}) or {}

        previsto_partida = dep.get("scheduled")
        previsto_chegada = arr.get("scheduled")

        dia_semana = None
        duracao_min = None
        t_partida = t_chegada = None
        # Datas incompletas ou inválidas não devem impedir o restante da coleta.
        try:
            if previsto_partida:
                t_partida = datetime.fromisoformat(previsto_partida.replace("Z", "+00:00"))
                dia_semana = DIAS_SEMANA[t_partida.weekday()]
            if previsto_chegada:
                t_chegada = datetime.fromisoformat(previsto_chegada.replace("Z", "+00:00"))
            if t_partida and t_chegada:
                duracao_min = int((t_chegada - t_partida).total_seconds() / 60)
        except ValueError:
            pass

        registros.append(
            {
                "data_coleta": agora,
                "numero_voo": flight.get("iata"),
                "companhia": airline.get("iata"),
                "origem": dep.get("iata"),
                "destino": arr.get("iata"),
                "horario_previsto_partida": previsto_partida,
                "horario_previsto_chegada": previsto_chegada,
                "status": STATUS_VOO.get(voo.get("flight_status"), voo.get("flight_status")),
                "duracao_min": duracao_min,
                "dia_semana": dia_semana,
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