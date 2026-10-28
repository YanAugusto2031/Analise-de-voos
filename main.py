"""
Orquestra a coleta diaria: AviationStack (status dos voos) e
Ignav (precos de passagens), gravando tudo no SQLite.

Uso:
    python main.py
"""

import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

from extract.aviationstack import buscar_voos_por_aeroporto, voos_para_dataframe
from extract.ignav import buscar_precos, precos_para_dataframe

DB_PATH = Path(__file__).parent / "voos_brasil.db"

# Aeroportos consultados no AviationStack. Como o free tier tem so 100
# req/mes, revezar 2-3 aeroportos por dia e suficiente pra nao estourar.
AEROPORTOS_AVIATIONSTACK = ["GRU", "GIG", "SSA"]

# Rotas consultadas na Ignav (origem, destino). Ajuste conforme o
# universo de aeroportos que te interessa.
ROTAS_PRECO = [
    ("GRU", "SSA"),
    ("GRU", "GIG"),
    ("GRU", "BSB"),
    ("SSA", "GIG"),
]
DATA_PARTIDA_PRECO = "2026-11-01"  # ajuste para uma data futura fixa ou dinamica


def coletar_aviationstack(conn: sqlite3.Connection, api_key: str) -> None:
    for aeroporto in AEROPORTOS_AVIATIONSTACK:
        try:
            voos = buscar_voos_por_aeroporto(aeroporto, api_key)
            df = voos_para_dataframe(voos)
            if not df.empty:
                df.to_sql("voos_status", conn, if_exists="append", index=False)
            print(f"[AviationStack] {aeroporto}: {len(df)} voos gravados.")
        except Exception as exc:
            print(f"[AviationStack] Erro em {aeroporto}: {exc}")


def coletar_ignav(conn: sqlite3.Connection, api_key: str) -> None:
    for origem, destino in ROTAS_PRECO:
        try:
            resposta = buscar_precos(origem, destino, DATA_PARTIDA_PRECO, api_key)
            df = precos_para_dataframe(resposta)
            if not df.empty:
                df.to_sql("precos", conn, if_exists="append", index=False)
            print(f"[Ignav] {origem}->{destino}: {len(df)} tarifas gravadas.")
        except Exception as exc:
            print(f"[Ignav] Erro em {origem}->{destino}: {exc}")


def main() -> None:
    load_dotenv()

    if not DB_PATH.exists():
        raise SystemExit(
            "Banco nao encontrado. Rode primeiro: python db/init_db.py"
        )

    with sqlite3.connect(DB_PATH) as conn:
        coletar_aviationstack(conn, os.environ["AVIATIONSTACK_API_KEY"])
        coletar_ignav(conn, os.environ["IGNAV_API_KEY"])

    print("\nColeta concluida.")


if __name__ == "__main__":
    main()