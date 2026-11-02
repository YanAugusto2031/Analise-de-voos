"""Consulta tarifas de ida (one-way) na API Ignav.

Documentação: https://ignav.com/docs/one-way
Cada consulta corresponde a uma rota e uma data de partida.
"""

import os
from datetime import datetime, timezone

import requests
import pandas as pd

BASE_URL = "https://ignav.com/api/fares/one-way"


def buscar_precos(origem: str, destino: str, data_partida: str, api_key: str) -> dict:
    """Busca opções de ida usando códigos IATA e data no formato AAAA-MM-DD."""
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


DIAS_SEMANA = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]

status_preco = {
    "verified": "Verificado",
    "unverified": "Não verificado",
    "unavailable": "Indisponível",
}

CLASSE_CABINE = {
    "economy": "Econômica",
    "premium_economy": "Econômica Premium",
    "business": "Executiva",
    "first": "Primeira Classe",
}

def _periodo_do_dia(hora: int) -> str:
    """Agrupa o horário em faixas para facilitar os filtros do relatório."""
    if hora < 6:
        return "Madrugada"
    if hora < 12:
        return "Manha"
    if hora < 18:
        return "Tarde"
    return "Noite"


def _formatar_duracao(minutos) -> str | None:
    """Apresenta a duração em horas e minutos (ex.: 5h35)."""
    if minutos is None:
        return None
    return f"{int(minutos) // 60}h{int(minutos) % 60:02d}"


def _formatar_preco(valor: float | None, moeda: str | None) -> str | None:
    """Gera uma versão textual do preço para exibir sem erro de separador."""
    if valor is None:
        return None
    br = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {br}" if (moeda or "BRL") == "BRL" else f"{moeda} {br}"


def _sim_nao(valor) -> str | None:
    """Traduz um indicador booleano da API para Sim, Não ou valor ausente."""
    if valor is None:
        return None
    return "Sim" if valor else "Não"

def _to_dt(valor: str | None) -> datetime | None:
    """Lê um horário ISO; devolve None para valores ausentes ou inválidos."""
    try:
        return datetime.fromisoformat(valor) if valor else None
    except ValueError:
        return None


def precos_para_dataframe(resposta: dict) -> pd.DataFrame:
    """Transforma itinerários da API nas colunas esperadas pela tabela precos."""
    agora = datetime.now(timezone.utc)
    registros = []

    for itinerario in resposta.get("itineraries", []):
        preco = itinerario.get("price", {}) or {}
        outbound = itinerario.get("outbound", {}) or {}
        # Uma passagem pode ter vários trechos; o primeiro e o último
        # fornecem os horários do itinerário completo.
        segmentos = outbound.get("segments", []) or []
        primeiro = segmentos[0] if segmentos else {}
        ultimo = segmentos[-1] if segmentos else {}

        # Guardamos o valor numérico para cálculos e outro formatado para exibição.
        valor = preco.get("amount")
        valor = round(float(valor), 2) if valor is not None else None
        moeda = preco.get("currency")

        partida = _to_dt(primeiro.get("departure_time_local"))
        chegada = _to_dt(ultimo.get("arrival_time_local"))
        data_partida = resposta.get("departure_date")
        try:
            d_partida = datetime.fromisoformat(data_partida).date()
        except (TypeError, ValueError):
            d_partida = None

        numeros_voo = [
            f"{s.get('marketing_carrier_code') or ''}{s.get('flight_number') or ''}"
            for s in segmentos
        ]

        registros.append(
            {
                "data_coleta": agora.isoformat(),
                "origem": resposta.get("origin"),
                "destino": resposta.get("destination"),
                "data_partida": data_partida,
                "dias_antecedencia": (d_partida - agora.date()).days if d_partida else None,
                "dia_semana_partida": DIAS_SEMANA[d_partida.weekday()] if d_partida else None,
                "companhia_nome": outbound.get("carrier"),
                "companhia_code": primeiro.get("marketing_carrier_code"),
                "numero_voo": " + ".join(n for n in numeros_voo if n) or None,
                "horario_partida": partida.strftime("%H:%M") if partida else None,
                "horario_chegada": chegada.strftime("%H:%M") if chegada else None,
                "periodo_partida": _periodo_do_dia(partida.hour) if partida else None,
                "chegada_dia_seguinte": int(chegada.date() > partida.date()) if partida and chegada else None,
                "cabin_class": CLASSE_CABINE.get(itinerario.get("cabin_class"), itinerario.get("cabin_class")),
                "numero_escalas": max(len(segmentos) - 1, 0),
                "aeroportos_escala": "/".join(s.get("arrival_airport") for s in segmentos[:-1]) or None,
                "duracao_min": outbound.get("duration_minutes"),
                "duracao_formatada": _formatar_duracao(outbound.get("duration_minutes")),
                "bilhetes_separados": _sim_nao(itinerario.get("requires_self_transfer")),
                "preco": valor,
                "preco_formatado": _formatar_preco(valor, moeda),
                "moeda": moeda,
                "status_preco": status_preco.get(preco.get("status"), preco.get("status")),
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