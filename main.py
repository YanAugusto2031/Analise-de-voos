"""
Extracao de dados de status e pontualidade de voos via AviationStack, OpenSky e Ignav.
Docs: https://aviationstack.com/documentation
Free tier: 100 requisicoes/mes -> use com moderacao (ex: 1 aeroporto por execucao, revezando ao longo da semana).
Uso:
    python main.py
"""

import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

from extract.aviationstack import buscar_voos_por_aeroporto, voos_para_dataframe
from extract.opensky import buscar_trafego_brasil
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


def limpar_coleta_do_dia(conn: sqlite3.Connection, tabela: str) -> None:
    """Remove linhas cuja data_coleta seja de hoje, para a proxima insercao
    substituir (e nao duplicar) a coleta do dia."""
    conn.execute(f"DELETE FROM {tabela} WHERE DATE(data_coleta) = DATE('now')")
    conn.commit()


def upsert_aeronaves(conn: sqlite3.Connection, df) -> None:
    """Extrai icao24/modelo de voos_status e grava (ou atualiza) na tabela
    aeronaves. Aeronaves sem icao24 conhecido sao ignoradas."""
    if "aeronave_icao24" not in df.columns:
        return

    aeronaves = df[["aeronave_icao24", "modelo_aeronave", "companhia"]].dropna(
        subset=["aeronave_icao24"]
    )
    for _, linha in aeronaves.iterrows():
        conn.execute(
            """
            INSERT INTO aeronaves (icao24, modelo, fabricante, companhia)
            VALUES (?, ?, NULL, ?)
            ON CONFLICT(icao24) DO UPDATE SET
                modelo = excluded.modelo,
                companhia = excluded.companhia
            """,
            (linha["aeronave_icao24"], linha["modelo_aeronave"], linha["companhia"]),
        )
    conn.commit()


def coletar_aviationstack(conn: sqlite3.Connection, api_key: str) -> None:
    limpar_coleta_do_dia(conn, "voos_status")

    for aeroporto in AEROPORTOS_AVIATIONSTACK:
        try:
            voos = buscar_voos_por_aeroporto(aeroporto, api_key)
            df = voos_para_dataframe(voos)
            if not df.empty:
                upsert_aeronaves(conn, df)
                df_voos = df.drop(columns=["aeronave_icao24", "aeronave_fabricante"])
                df_voos.to_sql("voos_status", conn, if_exists="append", index=False)
            print(f"[AviationStack] {aeroporto}: {len(df)} voos gravados.")
        except Exception as exc:
            print(f"[AviationStack] Erro em {aeroporto}: {exc}")


def coletar_opensky(conn: sqlite3.Connection) -> None:
    client_id = os.environ.get("OPENSKY_CLIENT_ID") or None
    client_secret = os.environ.get("OPENSKY_CLIENT_SECRET") or None
    try:
        df = buscar_trafego_brasil(client_id, client_secret)
        if not df.empty:
            df.to_sql("trafego", conn, if_exists="append", index=False)
        print(f"[OpenSky] {len(df)} aeronaves gravadas.")
    except Exception as exc:
        print(f"[OpenSky] Erro: {exc}")


def coletar_ignav(conn: sqlite3.Connection, api_key: str) -> None:
    limpar_coleta_do_dia(conn, "precos")

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
        coletar_opensky(conn)
        coletar_ignav(conn, os.environ["IGNAV_API_KEY"])

    print("\nColeta concluida.")


if __name__ == "__main__":
    main()