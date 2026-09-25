import os
from datetime import datetime, timezone

import requests
import pandas as pd

BASE_URL = "https://ignav.com/api/fares/one-way"


def buscar_precos(origem: str, destino: str, data_partida: str, api_key: str) -> dict:
    """
    origem/destino: codigos IATA (ex: 'GRU', 'SSA')
    data_partida: 'YYYY-MM-DD'
    """
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    body = {
        "origin": origem,
        "destination": destino,
        "departure_date": data_partida,
        "market": "BR",
    }
    resp = requests.post(BASE_URL, headers=headers, json=body, timeout=30)
    resp.raise_for_status()
    return resp.json()


def precos_para_dataframe(resposta: dict) -> pd.DataFrame:
    agora = datetime.now(timezone.utc).isoformat()
    registros = []

    for itinerario in resposta.get("itineraries", []):
        preco = itinerario.get("price", {}) or {}
        outbound = itinerario.get("outbound", {}) or {}
        segmentos = outbound.get("segments", []) or []
        primeiro_segmento = segmentos[0] if segmentos else {}

        registros.append(
            {
                "data_coleta": agora,
                "origem": resposta.get("origin"),
                "destino": resposta.get("destination"),
                "data_partida": resposta.get("departure_date"),
                "companhia_nome": outbound.get("carrier"),
                "companhia_code": primeiro_segmento.get("marketing_carrier_code"),
                "cabin_class": itinerario.get("cabin_class"),
                "numero_escalas": max(len(segmentos) - 1, 0),
                "duracao_min": outbound.get("duration_minutes"),
                "preco": preco.get("amount"),
                "moeda": preco.get("currency"),
                "ignav_id": itinerario.get("ignav_id"),
            }
        )

    return pd.DataFrame(registros)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    key = os.environ["IGNAV_API_KEY"]

    resposta = buscar_precos("GRU", "SSA", "2026-11-01", key)
    df = precos_para_dataframe(resposta)
    print(df.head())
    print(f"\n{len(df)} tarifas encontradas.")
