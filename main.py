"""Ponto de entrada da coleta de voos e de preços de passagens.

Consulta as duas APIs e salva os resultados no banco SQLite do projeto.
Para executar: python main.py
"""

import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

from extract.aviationstack import buscar_voos_por_aeroporto, voos_para_dataframe
from extract.ignav import buscar_precos, precos_para_dataframe

DB_PATH = Path(__file__).parent / "voos_brasil.db"

# Cada aeroporto gera uma consulta à AviationStack. Ajuste a lista de acordo
# com a cota de requisições disponível na conta da equipe.
AEROPORTOS_AVIATIONSTACK = ["GRU", "GIG", "SSA"]

# Rotas pesquisadas na Ignav: cada par representa origem e destino (IATA).
# Cada rota consome uma chamada da API por execução.
ROTAS_PRECO = [
    ("GRU", "SSA"),
    ("GRU", "GIG"),
    ("GRU", "BSB"),
    ("SSA", "GIG"),
]
DATA_PARTIDA_PRECO = "2026-12-31"  # Data pesquisada; atualize antes da coleta, se necessário.


def coletar_aviationstack(conn: sqlite3.Connection, api_key: str) -> None:
    """Consulta os aeroportos configurados e acrescenta os voos ao histórico."""
    for aeroporto in AEROPORTOS_AVIATIONSTACK:
        try:
            voos = buscar_voos_por_aeroporto(aeroporto, api_key)
            df = voos_para_dataframe(voos)
            if not df.empty:
                # append mantém as coletas anteriores para análise histórica.
                df.to_sql("voos_status", conn, if_exists="append", index=False)
            print(f"[AviationStack] {aeroporto}: {len(df)} voos gravados.")
        except Exception as exc:
            # Um aeroporto com erro não impede a consulta dos seguintes.
            print(f"[AviationStack] Erro em {aeroporto}: {exc}")


def coletar_ignav(conn: sqlite3.Connection, api_key: str) -> None:
    """Consulta preços por rota e os acrescenta ao banco existente."""
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
    """Carrega as chaves, verifica o banco e executa as duas coletas."""
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