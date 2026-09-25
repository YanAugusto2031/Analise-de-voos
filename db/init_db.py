import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from common.common.aeroportos import AEROPORTOS_BRASIL  # noqa: E402

DB_PATH = Path(__file__).parent.parent / "voos_brasil.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def criar_banco() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())

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
    criar_banco()