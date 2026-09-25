import os
from datetime import datetime, timezone

import requests
import pandas as pd

STATES_URL = "https://opensky-network.org/api/states/all"
TOKEN_URL = (
    "https://auth.opensky-network.org/auth/realms/opensky-network/"
    "protocol/openid-connect/token"
)

# Bounding box aproximado cobrindo o territorio brasileiro
BRASIL_BBOX = {
    "lamin": -34.0,
    "lomin": -74.0,
    "lamax": 5.5,
    "lomax": -34.0,
}

COLUNAS_STATE_VECTOR = [
    "icao24", "callsign", "origin_country", "time_position", "last_contact",
    "longitude", "latitude", "baro_altitude", "on_ground", "velocity",
    "true_track", "vertical_rate", "sensors", "geo_altitude", "squawk",
    "spi", "position_source",
]


def _obter_token(client_id: str, client_secret: str) -> str:
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def buscar_trafego_brasil(client_id: str | None = None, client_secret: str | None = None) -> pd.DataFrame:
    headers = {}
    if client_id and client_secret:
        token = _obter_token(client_id, client_secret)
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(STATES_URL, params=BRASIL_BBOX, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    states = data.get("states") or []
    df = pd.DataFrame(states, columns=COLUNAS_STATE_VECTOR)

    agora = datetime.now(timezone.utc).isoformat()
    df_tratado = pd.DataFrame(
        {
            "data_coleta": agora,
            "icao24": df["icao24"].str.strip(),
            "callsign": df["callsign"].str.strip(),
            "origem_estimada": None,   # OpenSky nao informa rota diretamente
            "destino_estimado": None,
            "latitude": df["latitude"],
            "longitude": df["longitude"],
            "altitude_m": df["geo_altitude"],
            "velocidade_kmh": df["velocity"] * 3.6,  # m/s -> km/h
            "direcao_graus": df["true_track"],
            "em_solo": df["on_ground"].astype(int),
            "squawk": df["squawk"],
        }
    )

    return df_tratado


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    cid = os.environ.get("OPENSKY_CLIENT_ID") or None
    csecret = os.environ.get("OPENSKY_CLIENT_SECRET") or None

    df = buscar_trafego_brasil(cid, csecret)
    print(df.head())
    print(f"\n{len(df)} aeronaves detectadas sobre o Brasil neste instante.")
