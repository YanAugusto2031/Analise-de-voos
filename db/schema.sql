-- Dados de referência: aeroportos e companhias usados nas análises.

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

-- Histórico das consultas: uma linha por voo ou opção de passagem coletada.

CREATE TABLE IF NOT EXISTS voos_status (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    data_coleta              TEXT,
    numero_voo               TEXT,
    companhia                TEXT REFERENCES companhias(iata_code),
    origem                   TEXT REFERENCES aeroportos(iata_code),
    destino                  TEXT REFERENCES aeroportos(iata_code),
    horario_previsto_partida TEXT,
    horario_previsto_chegada TEXT,
    status                   TEXT,   -- Programado, Em voo, Pousou, Cancelado, Incidente, Desviado
    duracao_min              INTEGER,
    dia_semana               TEXT
);

CREATE TABLE IF NOT EXISTS precos (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    data_coleta             TEXT,
    origem                  TEXT REFERENCES aeroportos(iata_code),
    destino                 TEXT REFERENCES aeroportos(iata_code),
    data_partida            TEXT,
    dias_antecedencia       INTEGER,  -- quantos dias antes do voo o preco foi coletado
    dia_semana_partida      TEXT,
    companhia_nome          TEXT,
    companhia_code          TEXT,
    numero_voo              TEXT,     -- ex: LA3040 (conexoes: LA3040 + LA2100)
    horario_partida         TEXT,     -- hora local, HH:MM
    horario_chegada         TEXT,     -- hora local, HH:MM
    periodo_partida         TEXT,     -- Madrugada / Manha / Tarde / Noite
    chegada_dia_seguinte    INTEGER,  -- 1 se chega no dia seguinte
    cabin_class             TEXT,
    numero_escalas          INTEGER,
    aeroportos_escala       TEXT,     -- ex: BSB/CNF (vazio se voo direto)
    duracao_min             INTEGER,
    duracao_formatada       TEXT,     -- ex: 2h35
    bilhetes_separados      TEXT,     -- Sim/Não: conexao em bilhetes separados (mais risco)
    preco                   REAL,     -- valor decimal em reais, ex: 2387.65
    preco_formatado         TEXT,     -- ex: R$ 2.387,65 (texto, nao sofre com separador)
    moeda                   TEXT DEFAULT 'BRL',
    status_preco            TEXT,
    ignav_id                TEXT
);

-- Tabela de apoio para futuros resumos por rota e período.

CREATE TABLE IF NOT EXISTS resumo_rotas (
    origem           TEXT REFERENCES aeroportos(iata_code),
    destino          TEXT REFERENCES aeroportos(iata_code),
    periodo          TEXT,
    total_voos       INTEGER,
    pct_pontualidade REAL,
    atraso_medio_min REAL,
    preco_medio      REAL,
    preco_minimo     REAL,
    PRIMARY KEY (origem, destino, periodo)
);

-- Índices para agilizar filtros por data e rota.

CREATE INDEX IF NOT EXISTS idx_voos_status_data ON voos_status(data_coleta);
CREATE INDEX IF NOT EXISTS idx_voos_status_rota ON voos_status(origem, destino);
CREATE INDEX IF NOT EXISTS idx_precos_rota_data ON precos(origem, destino, data_partida);

-- Consulta pronta para o Power BI: mantém a coleta mais recente de cada
-- combinação de origem, destino e data de partida, ordenada por preço.

CREATE VIEW IF NOT EXISTS vw_passagens_atuais AS
SELECT
    p.origem, p.destino, p.data_partida, p.dia_semana_partida, p.dias_antecedencia,
    p.companhia_nome, p.numero_voo, p.horario_partida, p.horario_chegada,
    p.periodo_partida, p.chegada_dia_seguinte, p.numero_escalas, p.aeroportos_escala,
    p.duracao_formatada, p.duracao_min,p.bilhetes_separados, p.cabin_class, p.preco, p.preco_formatado, p.moeda
FROM precos p
WHERE p.data_coleta = (
    SELECT MAX(p2.data_coleta) FROM precos p2
    WHERE p2.origem = p.origem AND p2.destino = p.destino AND p2.data_partida = p.data_partida
)
ORDER BY p.origem, p.destino, p.preco;