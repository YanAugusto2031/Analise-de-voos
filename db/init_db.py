"""Prepara o SQLite a partir do schema.sql e cadastra os aeroportos.

Comandos:
    python db/init_db.py            # cria ou completa sem apagar registros
    python db/init_db.py --recriar  # APAGA o banco anterior e começa do zero
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "voos_brasil.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

# Catálogo inicial de aeroportos. Os códigos IATA são as chaves da tabela.
AEROPORTOS_BRASIL = [
    # iata, nome, cidade, uf, pais, lat, lon, fuso
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


def criar_banco(recriar: bool = False) -> None:
    """Cria a estrutura e insere aeroportos que ainda não estejam cadastrados."""
    if recriar and DB_PATH.exists():
        # Atenção: esta opção também remove os preços e voos já coletados.
        DB_PATH.unlink()
        print("Banco antigo removido.")

    with sqlite3.connect(DB_PATH) as conn:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())

        # INSERT OR IGNORE permite repetir a inicialização sem duplicar aeroportos.
        conn.executemany(
            """
            INSERT OR IGNORE INTO aeroportos
                (iata_code, nome, cidade, uf, pais, latitude, longitude, fuso_horario)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            AEROPORTOS_BRASIL,
        )
        conn.commit()

    print(f"Banco criado/atualizado em: {DB_PATH}")
    print(f"{len(AEROPORTOS_BRASIL)} aeroportos inseridos (ou já existentes).")


if __name__ == "__main__":
    # --recriar é destrutivo: use somente quando quiser descartar o histórico.
    criar_banco(recriar="--recriar" in sys.argv)