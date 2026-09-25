# Análise de Voos no Brasil — Big Data em Python

Projeto de ETL em Python que combina 3 fontes de dados sobre voos no Brasil
(status/pontualidade, tráfego aéreo e preços), grava tudo em SQLite e
alimenta um relatório no Power BI.

## Fontes de dados

- **AviationStack** — status de voos, atrasos, rotas (100 req/mês grátis)
- **OpenSky Network** — tráfego aéreo em tempo real (grátis, sem chave obrigatória)
- **Ignav** — preços de passagens (1.000 requisições grátis, uso único)

## Como rodar (VS Code)

1. Clone o repositório e abra a pasta no VS Code.
2. Crie e ative um ambiente virtual:
```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
```
3. Instale as dependências:
```bash
   pip install -r requirements.txt
```
4. Copie `.env.example` para `.env` e preencha com suas chaves reais:
```bash
   cp .env.example .env
```
   O OpenSky funciona sem chave (limite menor); se quiser o limite maior,
   crie uma conta OAuth2 em opensky-network.org e preencha
   `OPENSKY_CLIENT_ID` / `OPENSKY_CLIENT_SECRET`.
5. Crie o banco de dados (só precisa rodar uma vez):
```bash
   python db/init_db.py
```
6. Rode a coleta:
```bash
   python main.py
```

Isso vai popular `voos_brasil.db` (SQLite) com os dados das três fontes.
Rodando o `main.py` periodicamente (ex: 1x por dia, manualmente ou via
Agendador de Tarefas / cron), você acumula histórico ao longo do tempo.
Sempre que coletar dados novos, clique em **Atualizar** no Power BI Desktop
pra trazer as linhas novas pro relatório.

## Estrutura

```
analise-voos-brasil/
├── .env.example               # modelo de variáveis de ambiente (sem chaves reais)
├── .gitignore
├── requirements.txt
├── tema-aviacao-brasil.json    # tema visual do Power BI
├── common/
│   └── aeroportos.py            # coordenadas dos aeroportos + cálculo de distância
├── db/
│   ├── schema.sql              # schema do banco
│   └── init_db.py              # cria o banco + popula aeroportos
├── extract/
│   ├── aviationstack.py        # status/pontualidade
│   ├── opensky.py              # tráfego aéreo
│   └── ignav.py                 # preços
├── main.py                     # orquestra a coleta e grava no SQLite
└── voos_brasil.db              # gerado localmente (não versionado)
```

> `.env` e `voos_brasil.db` ficam de fora do Git (veja `.gitignore`) — o
> primeiro por conter chaves de API, o segundo por ser gerado localmente a
> cada máquina.

## Conectando ao Power BI

Recomendado: **Obter Dados → Script Python**, usando `sqlite3` + `pandas`
para ler as tabelas direto — sem precisar instalar driver ODBC em nenhuma
máquina:

```python
import sqlite3
import pandas as pd

caminho_db = r"localizar na maquina a pasta \voos_brasil.db"
conn = sqlite3.connect(caminho_db)

voos_status = pd.read_sql("SELECT * FROM voos_status", conn)
trafego = pd.read_sql("SELECT * FROM trafego", conn)
precos = pd.read_sql("SELECT * FROM precos", conn)
aeroportos = pd.read_sql("SELECT * FROM aeroportos", conn)
companhias = pd.read_sql("SELECT * FROM companhias", conn)

conn.close()
```

Ajuste `caminho_db` para o caminho real em cada máquina. Em
**Arquivo → Opções e Configurações → Opções → Script Python**, aponte o
Power BI para o `python.exe` da sua `venv` (ex:
`analise-voos-brasil\venv\Scripts\python.exe`) — assim ele usa o ambiente
que já tem `pandas` instalado.

### Tema visual



## Observações importantes

- **AviationStack**: free tier tem só 100 req/mês — o `main.py` já está
  configurado para consultar poucos aeroportos por execução. Ajuste a lista
  `AEROPORTOS_AVIATIONSTACK` conforme sua cota.
- **Ignav**: as 1.000 requisições grátis **não renovam mensalmente** (é uma
  cota única). Use com moderação — ideal para uma amostragem inicial de
  preços, não para coleta contínua e ilimitada.
- **OpenSky**: sem autenticação, o limite é menor (~400 créditos/dia), mas
  já é suficiente para capturas periódicas de tráfego.
- **Visuais de mapa no Power BI**: vêm desativados por padrão. Habilite em
  Arquivo → Opções e Configurações → Opções → Global → Segurança.
- **`duracao_min` e `distancia_km`**: calculados automaticamente a partir dos
  horários (duração) e das coordenadas dos aeroportos brasileiros conhecidos
  em `common/aeroportos.py` (distância). Ficam em branco se origem ou
  destino não estiverem nessa lista.
- **Tabela `aeronaves`**: populada automaticamente pelo `main.py` sempre que
  a AviationStack retorna um `icao24` de aeronave.
- **Coleta duplicada no mesmo dia**: `voos_status` e `precos` são "limpos"
  (linhas do dia atual removidas) antes de cada nova inserção, então rodar
  `main.py` várias vezes no mesmo dia atualiza a coleta em vez de duplicar.
  `trafego` não passa por essa limpeza de propósito — várias capturas no
  mesmo dia mostram a evolução do tráfego ao longo do dia.