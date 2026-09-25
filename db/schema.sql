-- ========== TABELAS DE DIMENSAO ==========

CREATE TABLE IF NOT EXISTS aeroportos (
    iata_code    TEXT PRIMARY KEY,
    nome         TEXT,
    cidade       TEXT,
    uf           TEXT,
    pais         TEXT DEFAULT 'Brasil',
    latitude     REAL,
    longitude    REAL,
    fuso_horario TEXT
);

CREATE TABLE IF NOT EXISTS companhias (
    iata_code   TEXT PRIMARY KEY,
    nome        TEXT,
    pais_origem TEXT,
    tipo        TEXT
);

CREATE TABLE IF NOT EXISTS aeronaves (
    icao24     TEXT PRIMARY KEY,
    modelo     TEXT,
    fabricante TEXT,
    companhia  TEXT REFERENCES companhias(iata_code)
);

-- ========== TABELAS DE FATO ==========

CREATE TABLE IF NOT EXISTS voos_status (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    data_coleta              TEXT,
    numero_voo               TEXT,
    companhia                TEXT REFERENCES companhias(iata_code),
    origem                   TEXT REFERENCES aeroportos(iata_code),
    destino                  TEXT REFERENCES aeroportos(iata_code),
    terminal_origem          TEXT,
    portao_origem            TEXT,
    terminal_destino         TEXT,
    portao_destino           TEXT,
    horario_previsto_partida TEXT,
    horario_real_partida     TEXT,
    horario_previsto_chegada TEXT,
    horario_real_chegada     TEXT,
    atraso_partida_min       INTEGER,
    atraso_chegada_min       INTEGER,
    status                   TEXT,
    duracao_min              INTEGER,
    distancia_km              REAL,
    dia_semana               TEXT,
    modelo_aeronave          TEXT
);

CREATE TABLE IF NOT EXISTS trafego (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    data_coleta      TEXT,
    icao24           TEXT REFERENCES aeronaves(icao24),
    callsign         TEXT,
    origem_estimada  TEXT REFERENCES aeroportos(iata_code),
    destino_estimado TEXT REFERENCES aeroportos(iata_code),
    latitude         REAL,
    longitude        REAL,
    altitude_m       REAL,
    velocidade_kmh   REAL,
    direcao_graus    REAL,
    em_solo          INTEGER,
    squawk           TEXT
);

CREATE TABLE IF NOT EXISTS precos (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    data_coleta    TEXT,
    origem         TEXT REFERENCES aeroportos(iata_code),
    destino        TEXT REFERENCES aeroportos(iata_code),
    data_partida   TEXT,
    companhia_nome TEXT,
    companhia_code TEXT,
    cabin_class    TEXT,
    numero_escalas INTEGER,
    duracao_min    INTEGER,
    preco          REAL,
    moeda          TEXT DEFAULT 'USD',
    ignav_id       TEXT
);

-- ========== TABELA DE APOIO ==========

CREATE TABLE IF NOT EXISTS resumo_rotas (
    origem           TEXT REFERENCES aeroportos(iata_code),
    destino          TEXT REFERENCES aeroportos(iata_code),
    periodo          TEXT,
    total_voos       INTEGER,
    pct_pontualidade REAL,
    atraso_medio_min REAL,
    preco_medio      REAL,
    PRIMARY KEY (origem, destino, periodo)
);

-- ========== INDICES ==========

CREATE INDEX IF NOT EXISTS idx_voos_status_data ON voos_status(data_coleta);
CREATE INDEX IF NOT EXISTS idx_voos_status_rota ON voos_status(origem, destino);
CREATE INDEX IF NOT EXISTS idx_trafego_data ON trafego(data_coleta);
CREATE INDEX IF NOT EXISTS idx_precos_rota_data ON precos(origem, destino, data_partida);
