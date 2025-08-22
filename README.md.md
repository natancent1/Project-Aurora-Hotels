# 📊 Análise de Dados de Hotéis: Do Banco de Dados ao Dashboard

## 📝 Descrição do Projeto
Este projeto de análise de dados demonstra o ciclo completo de um projeto de **Business Intelligence**.  
Utilizando **Python 🐍** para geração de dados sintéticos e **SQL 💻** para manipulação e extração de insights, o projeto culmina em **dashboards interativos no Power BI 📈** que oferecem uma visão 360° do desempenho de uma rede de hotéis, incluindo análises de performance, sazonalidade e segmentação de clientes.

---

## 📂 Estrutura do Repositório
A seguir, a estrutura de pastas do projeto para facilitar a navegação e o entendimento:

```tree
.

├── README.md

├── dashboards/

│ └── aurora_hotels_report.pbix

├── data/

│ └── raw/

│ ├── ADR_e_OCUPACAOcsv

│ ├── Analise_Temporalidade.csv

│ ├── ClientesPorSegmento.csv

│ └── Performance_Categoria_Quarto.csv

├── images/

│ ├── view1.png

│ ├── view2.png

│ ├── view3.png

│ └── view4.png

├── scripts/

│ ├── 01_hotel_portfolio_generator_.py

│ ├── 02_CriaDB.sql

│ └── 03_CriaTabelas.sql

└── web_app/

└── ... (futuros arquivos)
```


---

## 1. 🚀 Introdução e Objetivo do Projeto

### Contexto
Este projeto de análise de dados tem como objetivo fornecer uma **visão 360° do negócio de uma rede de hotéis**, transformando dados brutos em insights acionáveis para a gestão.  
Isso permite à liderança tomar decisões estratégicas e mais informadas sobre clientes, desempenho operacional e rentabilidade.

### Ferramentas Utilizadas
- **Python** (Pandas, Faker)  
- **SQL Server** (SQL Management Studio)  
- **Power BI Desktop**  
- **HTML, CSS/Tailwind**  
- **React**  
- **VS Code**

---

## 2. 📁 Geração e Estrutura dos Dados

### 🔹 Etapa: Geração de Dados Sintéticos com Python
A primeira etapa do projeto consistiu na **criação de um conjunto de dados simulado e realista**, uma habilidade crucial quando dados reais não estão disponíveis.  

Para isso, utilizei **Python** com as bibliotecas:
- **Pandas** → manipulação de dados  
- **Faker** → geração de informações realistas (nomes, endereços, telefones, etc.)

O script foi projetado para **simular o ecossistema de uma rede de hotéis**, gerando **18 tabelas inter-relacionadas**, incluindo:

- Hoteis
- Clientes
- Quartos
- Reservas
- Pagamentos
- Funcionários
- Manutenções  
*(entre outras)*

Refletindo a complexidade de uma operação de negócio real.

```python
# Criado e implementado por Natan Vicente
# https://github.com/natancent1
# LinkedIn: https://www.linkedin.com/in/natanael-vicente-4b3b0a97/
# =========================

import os
import math
import random
import numpy as np
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta

# =========================
# PARÂMETROS GERAIS
# =========================
SEED = 42
np.random.seed(SEED)
random.seed(SEED)
fake = Faker("pt_BR")

OUTPUT_DIR = r"C:\Users\natan\OneDrive\Desktop\HotelDB\hoteldb_rede_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Horizonte temporal
DATE_START = pd.Timestamp("2019-01-01")
DATE_END   = pd.Timestamp("2025-12-31")

# Volumes (ajuste se quiser)
N_HOTEIS            = 5
QUARTOS_POR_HOTEL   = 150
N_CLIENTES          = 20000
N_RESERVAS          = 60000     # 60k reservas
PCT_CANCEL          = 0.12
PCT_NOSHOW          = 0.03
NOITES_MAX          = 14
N_FUNCIONARIOS_POR_HOTEL = 80

# Ocupação Diária: fração de reservas confirmadas a amostrar (para não explodir linhas)
OCUPACAO_SAMPLE_FRAC      = 0.60

# =========================
# HELPERS ROBUSTOS
# =========================
def norm_weights(weights):
    """Normaliza pesos para somar 1 de forma estável."""
    w = np.array(weights, dtype=float)
    s = w.sum()
    if s <= 0 or not np.isfinite(s):
        # fallback: uniforme
        return np.ones_like(w) / len(w)
    return w / s

def safe_choice(vals, weights=None):
    """Escolha com pesos normalizados. Evita erro de soma != 1."""
    if weights is None:
        return random.choice(vals)
    p = norm_weights(weights)
    # numpy exige mesmo comprimento
    if len(p) != len(vals):
        # fallback uniforme
        return random.choice(vals)
    return np.random.choice(vals, p=p)

def to_iso(df, cols):
    """Converte colunas de data para ISO YYYY-MM-DD (string)."""
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce").dt.strftime("%Y-%m-%d")

def add_year_month(df, date_col, prefix=""):
    """Adiciona Ano, Mes, AnoMes a partir de uma coluna de data (string ou datetime)."""
    s = pd.to_datetime(df[date_col], errors="coerce")
    df[f"{prefix}Ano"] = s.dt.year
    df[f"{prefix}Mes"] = s.dt.month
    df[f"{prefix}AnoMes"] = s.dt.strftime("%Y-%m")

def export_csv(df, name):
    path = os.path.join(OUTPUT_DIR, f"{name}.csv")
    df.to_csv(path, index=False, encoding="utf-8")
    print(f"OK -> {path}")

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

# =========================
# DIMENSÕES BÁSICAS
# =========================
rede_nome = "Rede Aurora Hotels"
hoteis_cidades = [
    ("Hotel Aurora Ipanema",      "Rio de Janeiro", "RJ", "Brasil"),
    ("Hotel Aurora Paulista",     "São Paulo",      "SP", "Brasil"),
    ("Hotel Aurora Beira-Mar",    "Fortaleza",      "CE", "Brasil"),
    ("Hotel Aurora Pampulha",     "Belo Horizonte", "MG", "Brasil"),
    ("Hotel Aurora Cambuí",       "Campinas",       "SP", "Brasil"),
]

# Sazonalidade por mês (fator de demanda/preço)
seasonality = {
    1: 0.95, 2: 0.98, 3: 1.00, 4: 1.03, 5: 1.05, 6: 1.08,
    7: 1.12, 8: 1.10, 9: 1.02, 10: 1.00, 11: 0.98, 12: 1.20
}
# Fim de semana pressão de preço
weekday_factor = {0: 0.98, 1: 0.98, 2: 1.00, 3: 1.00, 4: 1.05, 5: 1.12, 6: 1.10}

# Canais de venda
canais = [
    ("Site Próprio",  0.28),
    ("Balcão",        0.10),
    ("Agência",       0.12),
    ("OTA - Booking", 0.32),
    ("OTA - Expedia", 0.12),
    ("Corporativo",   0.06),
]
canal_pesos = norm_weights([w for _, w in canais])

# Formas de pagamento
formas_pagto = ["Cartão Crédito", "Cartão Débito", "Pix", "Boleto", "Dinheiro"]
fp_pesos = norm_weights([0.55, 0.12, 0.22, 0.06, 0.05])

# Tipos de quarto e tarifa base
room_types = ["Standard", "Casal", "Executivo", "Luxo", "Suíte"]
base_rates = {"Standard": 220, "Casal": 320, "Executivo": 420, "Luxo": 600, "Suíte": 900}
capacidade_map = {"Standard": 2, "Casal": 2, "Executivo": 2, "Luxo": 3, "Suíte": 4}
tipo_quarto_pesos = norm_weights([0.35, 0.24, 0.18, 0.15, 0.08])

# Serviços extras
servicos_dim = [
    {"ServicoID": 1, "NomeServico": "Room Service",   "Descricao": "Serviço de quarto 24h", "Preco": 60.0},
    {"ServicoID": 2, "NomeServico": "Spa",            "Descricao": "Massagens e tratamentos", "Preco": 180.0},
    {"ServicoID": 3, "NomeServico": "Lavanderia",     "Descricao": "Lavagem de roupas", "Preco": 35.0},
    {"ServicoID": 4, "NomeServico": "Estacionamento","Descricao": "Diária estacionamento", "Preco": 30.0},
    {"ServicoID": 5, "NomeServico": "Bar",            "Descricao": "Consumo no bar", "Preco": 75.0},
    {"ServicoID": 6, "NomeServico": "Transfer",       "Descricao": "Traslado aeroporto-hotel", "Preco": 120.0},
]
df_servicos = pd.DataFrame(servicos_dim)

# Departamentos
departamentos_dim = [
    {"DepartamentoID": 1, "NomeDepartamento": "Recepção"},
    {"DepartamentoID": 2, "NomeDepartamento": "Governança"},
    {"DepartamentoID": 3, "NomeDepartamento": "Manutenção"},
    {"DepartamentoID": 4, "NomeDepartamento": "Alimentos e Bebidas"},
    {"DepartamentoID": 5, "NomeDepartamento": "Comercial"},
    {"DepartamentoID": 6, "NomeDepartamento": "Administrativo/Financeiro"},
]
df_departamentos = pd.DataFrame(departamentos_dim)

# =========================
# HOTÉIS
# =========================
hoteis = []
for i, (nome, cidade, uf, pais) in enumerate(hoteis_cidades[:N_HOTEIS], start=1):
    hoteis.append({
        "HotelID": i,
        "Rede": rede_nome,
        "NomeHotel": nome,
        "Cidade": cidade,
        "UF": uf,
        "Pais": pais,
        "Categoria": safe_choice(["4 estrelas","5 estrelas"], [0.7,0.3]),
        "Telefone": fake.phone_number(),
        "Email": f"contato@{nome.lower().replace(' ', '').replace('í','i').replace('ã','a')}.com",
        "DataAbertura": fake.date_between(start_date="-15y", end_date="-5y"),
        "TotalQuartos": QUARTOS_POR_HOTEL
    })
df_hoteis = pd.DataFrame(hoteis)
to_iso(df_hoteis, ["DataAbertura"])

# =========================
# QUARTOS
# =========================
quartos = []
global_quarto_id = 1
for h in df_hoteis.itertuples(index=False):
    for i in range(1, QUARTOS_POR_HOTEL + 1):
        t = safe_choice(room_types, tipo_quarto_pesos)
        andar = 1 + (i // 10)
        tarifa = base_rates[t] * np.random.normal(1.0, 0.06)
        quartos.append({
            "QuartoID": global_quarto_id,
            "HotelID": h.HotelID,
            "Numero": f"{andar:02d}{(i%100):02d}",
            "Tipo": t,
            "PrecoBase": round(max(tarifa, base_rates[t]*0.8), 2),
            "Andar": andar,
            "Capacidade": capacidade_map[t],
            "Status": "Ativo"
        })
        global_quarto_id += 1
df_quartos = pd.DataFrame(quartos)

quartos_por_hotel = {
    hid: df_quartos.loc[df_quartos["HotelID"] == hid, "QuartoID"].values
    for hid in df_hoteis["HotelID"].tolist()
}

# =========================
# CANAIS DE VENDA
# =========================
df_canais = pd.DataFrame([{"CanalID": i+1, "NomeCanal": c} for i, (c, _) in enumerate(canais)])

# =========================
# CLIENTES
# =========================
domains = ["gmail.com", "hotmail.com", "outlook.com", "yahoo.com.br", "uol.com.br"]
clientes = []
for i in range(1, N_CLIENTES + 1):
    first = fake.first_name()
    last  = fake.last_name()
    email = f"{first}.{last}{np.random.randint(0,9999)}@{safe_choice(domains)}".lower().replace(" ", "")
    clientes.append({
        "ClienteID": i,
        "Nome": first,
        "Sobrenome": last,
        "Email": email,
        "Telefone": fake.phone_number(),
        "Cidade": fake.city(),
        "UF": fake.estado_sigla(),
        "Pais": "Brasil",
        "DataNascimento": fake.date_of_birth(minimum_age=18, maximum_age=85),
        "Genero": safe_choice(["M","F"], [0.49,0.51]),
        "Documento": fake.cpf(),
        "DataCadastro": fake.date_between(start_date="-8y", end_date="today")
    })
df_clientes = pd.DataFrame(clientes)
to_iso(df_clientes, ["DataNascimento", "DataCadastro"])

# =========================
# FUNÇÕES DE TARIFA E DATAS
# =========================
def nightly_rate(date_ts: pd.Timestamp, base: float) -> float:
    f_season = seasonality[int(date_ts.month)]
    f_weekday = weekday_factor[int(date_ts.weekday())]
    noise = np.random.normal(1.0, 0.03)
    return max(100.0, base * f_season * f_weekday * noise)

noites_vals = list(range(1, NOITES_MAX+1))
noites_pesos = norm_weights([0.22,0.20,0.15,0.10,0.07,0.06,0.05,0.04,0.03,0.03,0.02,0.015,0.015,0.01])

def sample_booking_dates():
    """Retorna (data_reserva, checkin, checkout) coerentes."""
    # A CORREÇÃO ESTÁ AQUI: garantindo que 'checkout' seja um Timestamp
    checkout = pd.Timestamp(fake.date_between_dates(date_start=DATE_START, date_end=DATE_END))
    los = safe_choice(noites_vals, noites_pesos)
    checkin = checkout - timedelta(days=int(los))
    
    if checkin < DATE_START:  # A comparação agora funciona
        checkin = DATE_START
        checkout = checkin + timedelta(days=int(los))
    
    # lead time ~ gamma com teto 120 dias
    lead = int(np.clip(np.random.gamma(shape=2.0, scale=10.0), 0, 120))
    data_reserva = checkin - timedelta(days=lead)
    if data_reserva < DATE_START:
        data_reserva = DATE_START
        
    return data_reserva, checkin, checkout, int(los)

# =========================
# RESERVAS, PAGAMENTOS, SERVIÇOS, FEEDBACK
# =========================
reservas = []
pagamentos = []
reserva_servicos = []
feedback = []

status_choices = ["Confirmada", "Cancelada", "No-Show"]
status_pesos   = norm_weights([1 - PCT_CANCEL - PCT_NOSHOW, PCT_CANCEL, PCT_NOSHOW])

pay_id = 1
fb_id  = 1

for res_id in range(1, N_RESERVAS + 1):
    hotel_id = int(safe_choice(df_hoteis["HotelID"].tolist(), [0.22,0.33,0.16,0.14,0.15][:N_HOTEIS]))
    quarto_id = int(safe_choice(quartos_por_hotel[hotel_id]))
    cliente_id = int(np.random.randint(1, N_CLIENTES + 1))

    data_reserva, checkin, checkout, noites = sample_booking_dates()
    status = safe_choice(status_choices, status_pesos)
    canal_id = int(safe_choice(df_canais["CanalID"].tolist(), canal_pesos))

    base = float(df_quartos.loc[df_quartos["QuartoID"] == quarto_id, "PrecoBase"].iloc[0])
    dates = pd.date_range(checkin, periods=noites, freq="D")
    valor_estadia = float(np.sum([nightly_rate(d, base) for d in dates]))

    reservas.append({
        "ReservaID": res_id,
        "HotelID": hotel_id,
        "QuartoID": quarto_id,
        "ClienteID": cliente_id,
        "CanalID": canal_id,
        "DataReserva": data_reserva,
        "DataCheckIn": checkin,
        "DataCheckOut": checkout,
        "Noites": noites,
        "Status": status
    })

    if status == "Confirmada":
        # Consumos de serviços (prob ~55%)
        extras = 0.0
        if np.random.rand() < 0.55:
            n_itens = safe_choice([1,2,3], [0.65,0.27,0.08])
            serv_ids = np.random.choice(df_servicos["ServicoID"].values, size=int(n_itens), replace=True)
            for sid in serv_ids:
                qtd = int(safe_choice([1,2,3,4], [0.6,0.25,0.1,0.05]))
                preco = float(df_servicos.loc[df_servicos["ServicoID"] == sid, "Preco"].iloc[0])
                total = float(preco * qtd)
                reserva_servicos.append({
                    "ReservaID": res_id,
                    "ServicoID": int(sid),
                    "Quantidade": qtd,
                    "ValorTotal": round(total, 2)
                })
                extras += total

        valor_total = valor_estadia + extras
        # Data de pagamento: no dia do check-in ou alguns dias depois
        dt_pag = pd.Timestamp(checkin) + pd.Timedelta(days=int(safe_choice([0,0,0,1,1,2,3], [0.35,0.25,0.15,0.12,0.07,0.04,0.02])))
        pagamentos.append({
            "PagamentoID": pay_id,
            "ReservaID": res_id,
            "Valor": round(valor_total, 2),
            "FormaPagamento": safe_choice(formas_pagto, fp_pesos),
            "DataPagamento": dt_pag
        })
        pay_id += 1

        # Feedback (prob ~35%)
        if np.random.rand() < 0.35:
            nota = int(clamp(round(np.random.normal(4.3, 0.7)), 1, 5))
            feedback.append({
                "FeedbackID": fb_id,
                "ReservaID": res_id,
                "Nota": nota,
                "Comentario": fake.sentence(nb_words=12),
                "DataFeedback": pd.Timestamp(checkout) + pd.Timedelta(days=int(np.random.randint(0,7)))
            })
            fb_id += 1

    elif status == "No-Show":
        # multa 1 diária em ~40%
        if np.random.rand() < 0.40:
            multa = float(nightly_rate(pd.Timestamp(checkin), base))
            pagamentos.append({
                "PagamentoID": pay_id,
                "ReservaID": res_id,
                "Valor": round(multa, 2),
                "FormaPagamento": safe_choice(formas_pagto, fp_pesos),
                "DataPagamento": checkin
            })
            pay_id += 1

df_reservas = pd.DataFrame(reservas)
df_pagamentos = pd.DataFrame(pagamentos)
df_reserva_servicos = pd.DataFrame(reserva_servicos)
df_feedback = pd.DataFrame(feedback)

to_iso(df_reservas, ["DataReserva","DataCheckIn","DataCheckOut"])
to_iso(df_pagamentos, ["DataPagamento"])
to_iso(df_feedback, ["DataFeedback"])

add_year_month(df_pagamentos, "DataPagamento", prefix="")
add_year_month(df_reservas, "DataCheckIn",   prefix="CheckIn")
add_year_month(df_reservas, "DataReserva",   prefix="Reserva")

# =========================
# FUNCIONÁRIOS
# =========================
cargos = ["Recepcionista","Supervisor Recepção","Camareira","Governanta",
          "Técnico Manutenção","Cozinheiro","Garçom","Bartender",
          "Gerente A&B","Comercial","Controller","Gerente Geral"]
# pesos coerentes por distribuição
cargos_pesos = norm_weights([0.14,0.04,0.22,0.03,0.08,0.06,0.08,0.05,0.02,0.06,0.06,0.016])
salarios = {
    "Recepcionista":2600, "Supervisor Recepção":3800, "Camareira":2300, "Governanta":3400,
    "Técnico Manutenção":3000, "Cozinheiro":3200, "Garçom":2400, "Bartender":2800,
    "Gerente A&B":6800, "Comercial":5200, "Controller":7200, "Gerente Geral":12000
}

def cargo_to_dep(cg):
    if "Recep" in cg: return 1
    if "Camareira" in cg or "Governanta" in cg: return 2
    if "Manutenção" in cg: return 3
    if cg in ["Cozinheiro","Garçom","Bartender","Gerente A&B"]: return 4
    if "Comercial" in cg: return 5
    return 6

funcionarios = []
fid = 1
for h in df_hoteis.itertuples(index=False):
    for _ in range(N_FUNCIONARIOS_POR_HOTEL):
        cg = safe_choice(cargos, cargos_pesos)
        funcionarios.append({
            "FuncionarioID": fid,
            "HotelID": h.HotelID,
            "Nome": fake.first_name(),
            "Sobrenome": fake.last_name(),
            "Cargo": cg,
            "DepartamentoID": cargo_to_dep(cg),
            "DataAdmissao": fake.date_between(start_date="-7y", end_date="today"),
            "Salario": salarios[cg]
        })
        fid += 1
df_funcionarios = pd.DataFrame(funcionarios)
to_iso(df_funcionarios, ["DataAdmissao"])

# =========================
# FORNECEDORES
# =========================
forn_categorias = ["Alimentos","Bebidas","Lavanderia","Limpeza","Manutenção","TI/Sistemas","Eventos"]
fornecedores = []
fornid = 1
for h in df_hoteis.itertuples(index=False):
    n = np.random.randint(8, 12)  # 8 a 11 fornecedores por hotel
    for _ in range(n):
        cat = safe_choice(forn_categorias)
        fornecedores.append({
            "FornecedorID": fornid,
            "HotelID": h.HotelID,
            "RazaoSocial": f"{fake.company()} Ltda",
            "Categoria": cat,
            "Telefone": fake.phone_number(),
            "Email": f"contato@{fake.domain_name()}",
            "Cidade": h.Cidade,
            "UF": h.UF,
            "Pais": "Brasil",
        })
        fornid += 1
df_fornecedores = pd.DataFrame(fornecedores)

# =========================
# ESTOQUE (CATÁLOGO DE PRODUTOS) & MOVIMENTOS
# =========================
prod_categorias = ["Bebidas","Alimentos","Amenities","Rouparia","Limpeza"]
unidades = {"Bebidas":"UN","Alimentos":"KG","Amenities":"UN","Rouparia":"UN","Limpeza":"LT"}

produtos = []
movimentos = []
prod_id = 1
mov_id = 1
for h in df_hoteis.itertuples(index=False):
    # Catálogo por hotel (30 itens)
    for _ in range(30):
        cat = safe_choice(prod_categorias)
        produtos.append({
            "ProdutoID": prod_id,
            "HotelID": h.HotelID,
            "NomeProduto": f"{cat} {fake.word().capitalize()}",
            "Categoria": cat,
            "Unidade": unidades[cat],
            "CustoMedio": round(abs(np.random.normal(20 if cat!='Rouparia' else 80, 10)), 2)
        })
        # Movimentos mensais por 2019-2025
        meses = pd.period_range(DATE_START, DATE_END, freq="M")
        for p in meses:
            # entrada e saída controladas
            entrada_qt = int(np.clip(round(abs(np.random.normal(50, 20))), 5, 200))
            saida_qt   = int(np.clip(round(abs(np.random.normal(45, 18))), 5, 200))
            data_ent = pd.Timestamp(p.start_time) + pd.Timedelta(days=int(np.random.randint(0,10)))
            data_sai = pd.Timestamp(p.end_time)   - pd.Timedelta(days=int(np.random.randint(0,10)))

            movimentos.append({
                "MovimentoID": mov_id,
                "HotelID": h.HotelID,
                "ProdutoID": prod_id,
                "TipoMovimento": "Entrada",
                "Quantidade": entrada_qt,
                "DataMovimento": data_ent
            })
            mov_id += 1
            movimentos.append({
                "MovimentoID": mov_id,
                "HotelID": h.HotelID,
                "ProdutoID": prod_id,
                "TipoMovimento": "Saida",
                "Quantidade": saida_qt,
                "DataMovimento": data_sai
            })
            mov_id += 1
        prod_id += 1

df_estoque = pd.DataFrame(produtos)
df_movimentos = pd.DataFrame(movimentos)
to_iso(df_movimentos, ["DataMovimento"])

# =========================
# MANUTENÇÕES
# =========================
tipos_manut = ["Preventiva","Corretiva","Inspeção"]
status_manut = ["Aberta","Em Andamento","Concluída"]
manutencoes = []
man_id = 1
for h in df_hoteis.itertuples(index=False):
    quartos_h = df_quartos.loc[df_quartos["HotelID"]==h.HotelID, "QuartoID"].values
    # 8-12 manutenções por mês por hotel (volume razoável)
    meses = pd.period_range(DATE_START, DATE_END, freq="M")
    for p in meses:
        n_m = np.random.randint(8, 13)
        for _ in range(n_m):
            qid = int(safe_choice(quartos_h))
            dt_ini = pd.Timestamp(p.start_time) + pd.Timedelta(days=int(np.random.randint(0,20)))
            dur = int(np.clip(round(abs(np.random.normal(2,1))), 1, 7))
            dt_fim = dt_ini + pd.Timedelta(days=dur)
            custo = round(abs(np.random.normal(350, 180)), 2)
            manutencoes.append({
                "ManutencaoID": man_id,
                "HotelID": h.HotelID,
                "QuartoID": qid,
                "Tipo": safe_choice(tipos_manut, [0.5,0.35,0.15]),
                "DataInicio": dt_ini,
                "DataFim": dt_fim,
                "Status": safe_choice(status_manut, [0.1,0.2,0.7]),
                "Custo": custo
            })
            man_id += 1
df_manutencoes = pd.DataFrame(manutencoes)
to_iso(df_manutencoes, ["DataInicio","DataFim"])

# =========================
# EVENTOS (receita adicional)
# =========================
tipos_evento = ["Conferência","Casamento","Workshop","Lançamento","Reunião Executiva"]
eventos = []
evt_id = 1
for h in df_hoteis.itertuples(index=False):
    # 2-6 eventos por mês
    meses = pd.period_range(DATE_START, DATE_END, freq="M")
    for p in meses:
        n_e = np.random.randint(2, 7)
        for _ in range(n_e):
            dt_ini = pd.Timestamp(p.start_time) + pd.Timedelta(days=int(np.random.randint(0,20)))
            dur = int(np.clip(round(abs(np.random.normal(1.5,0.8))), 1, 5))
            dt_fim = dt_ini + pd.Timedelta(days=dur)
            receita = round(abs(np.random.normal(25000, 12000)), 2)
            eventos.append({
                "EventoID": evt_id,
                "HotelID": h.HotelID,
                "TipoEvento": safe_choice(tipos_evento),
                "DataInicio": dt_ini,
                "DataFim": dt_fim,
                "ReceitaEvento": receita
            })
            evt_id += 1
df_eventos = pd.DataFrame(eventos)
to_iso(df_eventos, ["DataInicio","DataFim"])

# =========================
# AVALIAÇÕES (REVIEWS) já geradas parcialmente; reforço por eventos/épocas?
# (Mantemos as de reservas confirmadas; já está ok para o portfólio)
# =========================

# =========================
# PROGRAMA DE FIDELIDADE
# =========================
# Pontos ~ 1 ponto a cada R$10 pagos; Nível por faixas
if not df_pagamentos.empty:
    pag_por_cliente = df_reservas.merge(df_pagamentos[["ReservaID","Valor"]], on="ReservaID", how="inner") \
                                     .groupby("ClienteID", as_index=False)["Valor"].sum()
    pag_por_cliente["Pontos"] = (pag_por_cliente["Valor"] / 10.0).round().astype(int)
    def nivel(p):
        if p >= 20000: return "Diamante"
        if p >= 10000: return "Ouro"
        if p >= 4000:  return "Prata"
        return "Bronze"
    pag_por_cliente["Nivel"] = pag_por_cliente["Pontos"].apply(nivel)
    df_fidelidade = pag_por_cliente.rename(columns={"Valor":"ValorAcumulado"})
else:
    df_fidelidade = pd.DataFrame(columns=["ClienteID","ValorAcumulado","Pontos","Nivel"])

# =========================
# RECLAMAÇÕES
# =========================
motivos = ["Atraso no check-in","Quarto sujo","Barulho","Ar-condicionado com problema","Atendimento demorado","Cobrança indevida"]
reclamacoes = []
rec_id = 1
# ~6% das reservas geram reclamação
if not df_reservas.empty:
    sample_recs = df_reservas.sample(frac=0.06, random_state=SEED)
    for r in sample_recs.itertuples(index=False):
        reclamacoes.append({
            "ReclamacaoID": rec_id,
            "ReservaID": r.ReservaID,
            "HotelID": r.HotelID,
            "DataReclamacao": r.DataCheckOut,  # geralmente após a estadia
            "Motivo": safe_choice(motivos, [0.18,0.22,0.15,0.16,0.17,0.12]),
            "Status": safe_choice(["Aberta","Em Tratativa","Resolvida"], [0.15,0.25,0.60])
        })
        rec_id += 1
df_reclamacoes = pd.DataFrame(reclamacoes)
to_iso(df_reclamacoes, ["DataReclamacao"])

# =========================
# OCUPAÇÃO DIÁRIA (amostrada)
# =========================
print("Gerando OcupacaoDiaria (amostra controlada para manter performance)...")
occ_rows = []
confirmadas = df_reservas[df_reservas["Status"]=="Confirmada"]
if not confirmadas.empty:
    confirmadas = confirmadas.sample(frac=OCUPACAO_SAMPLE_FRAC, random_state=SEED)
    for r in confirmadas.itertuples(index=False):
        start = pd.to_datetime(r.DataCheckIn)
        end   = pd.to_datetime(r.DataCheckOut)
        base  = float(df_quartos.loc[df_quartos["QuartoID"]==r.QuartoID, "PrecoBase"].iloc[0])
        for d in pd.date_range(start, end - pd.Timedelta(days=1), freq="D"):
            tarifa = nightly_rate(d, base)
            occ_rows.append({
                "HotelID": r.HotelID,
                "QuartoID": r.QuartoID,
                "Data": d.strftime("%Y-%m-%d"),
                "TarifaEfetiva": round(tarifa, 2)
            })
df_ocupacao = pd.DataFrame(occ_rows)

# =========================
# CANAIS & SERVIÇOS (dimensões já prontas)
# =========================

# =========================
# EXPORTA TUDO
# =========================
print("\n=== EXPORTANDO ARQUIVOS ===")
export_csv(df_hoteis,          "Hoteis")
export_csv(df_quartos,         "Quartos")
export_csv(df_canais,          "CanaisVenda")
export_csv(df_servicos,        "Servicos")
export_csv(df_departamentos,   "Departamentos")
export_csv(df_clientes,        "Clientes")
export_csv(df_reservas,        "Reservas")
export_csv(df_pagamentos,      "Pagamentos")
export_csv(df_reserva_servicos,"ReservaServicos")
export_csv(df_feedback,        "Feedback")
export_csv(df_funcionarios,    "Funcionarios")
export_csv(df_fornecedores,    "Fornecedores")
export_csv(df_estoque,         "EstoqueProdutos")
export_csv(df_movimentos,      "MovimentosEstoque")
export_csv(df_manutencoes,     "Manutencoes")
export_csv(df_eventos,         "Eventos")
export_csv(df_fidelidade,      "Fidelidade")
export_csv(df_reclamacoes,     "Reclamacoes")
export_csv(df_ocupacao,        "OcupacaoDiaria")

# =========================
# RESUMO FINAL (sanidade)
# =========================
print("\n=== RESUMO ===")
def count(df, name): print(f"{name:22s}: {len(df):>8,d}")
count(df_hoteis, "Hoteis")
count(df_quartos, "Quartos")
count(df_clientes, "Clientes")
count(df_reservas, "Reservas")
count(df_pagamentos, "Pagamentos")
count(df_reserva_servicos, "ReservaServicos")
count(df_feedback, "Feedback")
count(df_funcionarios, "Funcionarios")
count(df_fornecedores, "Fornecedores")
count(df_estoque, "EstoqueProdutos")
count(df_movimentos, "MovimentosEstoque")
count(df_manutencoes, "Manutencoes")
count(df_eventos, "Eventos")
count(df_fidelidade, "Fidelidade")
count(df_reclamacoes, "Reclamacoes")
count(df_ocupacao, "OcupacaoDiaria")
print(f"\nArquivos gerados em: {OUTPUT_DIR}")
print("Pronto para BULK INSERT no SQL Server e modelagem no Power BI.")
```

### 🔹 Etapa: Estrutura do Banco de Dados em SQL Server  

Após a geração dos dados com **Python**, a próxima etapa foi a **estruturação do banco de dados no SQL Server**.  

- Utilizando comandos **DDL**, as tabelas foram criadas com **PRIMARY KEY** e **FOREIGN KEY**, estabelecendo relacionamentos como:  
  - **Reservas → Clientes**  
  - **Reservas → Hoteis**  
  - **Reservas → Quartos**  

- A carga dos dados foi feita via **BULK INSERT**, garantindo rapidez e eficiência no processo.  

## Cria banco de dados

```sql
IF DB_ID('Aurora Hotels') IS NULL
    CREATE DATABASE Aurora_Hotels_DB;
GO

USE Aurora_Hotels_DB;
GO
```

## Cria Tabelas

```sql
USE Aurora_Hotels_DB;
GO

-- Hoteis (Tabela central)
CREATE TABLE Hoteis (
    HotelID INT PRIMARY KEY,
    Rede NVARCHAR(50),
    NomeHotel NVARCHAR(100),
    Cidade NVARCHAR(100),
    UF NVARCHAR(2),
    Pais NVARCHAR(50),
    Categoria NVARCHAR(50),
    Telefone NVARCHAR(20),
    Email NVARCHAR(100),
    DataAbertura DATE,
    TotalQuartos INT
);
GO

-- Canais de Venda (Tabela de dimensão)
CREATE TABLE CanaisVenda (
    CanalID INT PRIMARY KEY,
    NomeCanal NVARCHAR(100)
);
GO

-- Clientes (Tabela de dimensão)
CREATE TABLE Clientes (
    ClienteID INT PRIMARY KEY,
    Nome NVARCHAR(100),
    Sobrenome NVARCHAR(100),
    Email NVARCHAR(150),
    Telefone NVARCHAR(20),
    Cidade NVARCHAR(100),
    UF NVARCHAR(2),
    Pais NVARCHAR(50),
    DataNascimento DATE,
    Genero CHAR(1),
    Documento NVARCHAR(20),
    DataCadastro DATE
);
GO

-- Servicos (Tabela de dimensão)
CREATE TABLE Servicos (
    ServicoID INT PRIMARY KEY,
    NomeServico NVARCHAR(100),
    Descricao NVARCHAR(250),
    Preco DECIMAL(10,2)
);
GO

-- Departamentos (Tabela de dimensão)
CREATE TABLE Departamentos (
    DepartamentoID INT PRIMARY KEY,
    NomeDepartamento NVARCHAR(50)
);
GO

-- Quartos (Depende de Hoteis)
CREATE TABLE Quartos (
    QuartoID INT PRIMARY KEY,
    HotelID INT FOREIGN KEY REFERENCES Hoteis(HotelID),
    Numero NVARCHAR(10),
    Tipo NVARCHAR(50),
    PrecoBase DECIMAL(10,2),
    Andar INT,
    Capacidade INT,
    Status NVARCHAR(20)
);
GO

-- Funcionários (Depende de Hoteis e Departamentos)
CREATE TABLE Funcionarios (
    FuncionarioID INT PRIMARY KEY,
    HotelID INT FOREIGN KEY REFERENCES Hoteis(HotelID),
    Nome NVARCHAR(100),
    Sobrenome NVARCHAR(100),
    Cargo NVARCHAR(50),
    DepartamentoID INT FOREIGN KEY REFERENCES Departamentos(DepartamentoID),
    DataAdmissao DATE,
    Salario DECIMAL(10,2)
);
GO

-- Fornecedores (Depende de Hoteis)
CREATE TABLE Fornecedores (
    FornecedorID INT PRIMARY KEY,
    HotelID INT FOREIGN KEY REFERENCES Hoteis(HotelID),
    RazaoSocial NVARCHAR(200),
    Categoria NVARCHAR(100),
    Telefone NVARCHAR(20),
    Email NVARCHAR(100),
    Cidade NVARCHAR(100),
    UF NVARCHAR(2),
    Pais NVARCHAR(50)
);
GO

-- EstoqueProdutos (Depende de Hoteis)
CREATE TABLE EstoqueProdutos (
    ProdutoID INT PRIMARY KEY,
    HotelID INT FOREIGN KEY REFERENCES Hoteis(HotelID),
    NomeProduto NVARCHAR(100),
    Categoria NVARCHAR(100),
    Unidade NVARCHAR(10),
    CustoMedio DECIMAL(10,2)
);
GO

-- Eventos (Depende de Hoteis)
CREATE TABLE Eventos (
    EventoID INT PRIMARY KEY,
    HotelID INT FOREIGN KEY REFERENCES Hoteis(HotelID),
    TipoEvento NVARCHAR(100),
    DataInicio DATE,
    DataFim DATE,
    ReceitaEvento DECIMAL(10,2)
);
GO

-- Fidelidade (Depende de Clientes)
CREATE TABLE Fidelidade (
    ClienteID INT PRIMARY KEY FOREIGN KEY REFERENCES Clientes(ClienteID),
    ValorAcumulado DECIMAL(12,2),
    Pontos INT,
    Nivel NVARCHAR(50)
);
GO

-- Reservas (Depende de Clientes, Quartos, CanaisVenda)
CREATE TABLE Reservas (
    ReservaID INT PRIMARY KEY,
    HotelID INT FOREIGN KEY REFERENCES Hoteis(HotelID),
    QuartoID INT FOREIGN KEY REFERENCES Quartos(QuartoID),
    ClienteID INT FOREIGN KEY REFERENCES Clientes(ClienteID),
    CanalID INT FOREIGN KEY REFERENCES CanaisVenda(CanalID),
    DataReserva DATE,
    DataCheckIn DATE,
    DataCheckOut DATE,
    Noites INT,
    Status NVARCHAR(20)
);
GO

-- Pagamentos (Depende de Reservas)
CREATE TABLE Pagamentos (
    PagamentoID INT PRIMARY KEY,
    ReservaID INT FOREIGN KEY REFERENCES Reservas(ReservaID),
    Valor DECIMAL(12,2),
    FormaPagamento NVARCHAR(50),
    DataPagamento DATE,
    Ano INT,
    Mes INT,
    AnoMes NVARCHAR(7)
);
GO

-- ReservaServicos (Depende de Reservas e Serviços)
CREATE TABLE ReservaServicos (
    ReservaID INT FOREIGN KEY REFERENCES Reservas(ReservaID),
    ServicoID INT FOREIGN KEY REFERENCES Servicos(ServicoID),
    Quantidade INT,
    ValorTotal DECIMAL(10,2),
    PRIMARY KEY (ReservaID, ServicoID)
);
GO

-- Feedback (Depende de Reservas)
CREATE TABLE Feedback (
    FeedbackID INT PRIMARY KEY,
    ReservaID INT FOREIGN KEY REFERENCES Reservas(ReservaID),
    Nota INT,
    Comentario NVARCHAR(500),
    DataFeedback DATE
);
GO

-- Manutencoes (Depende de Hoteis e Quartos)
CREATE TABLE Manutencoes (
    ManutencaoID INT PRIMARY KEY,
    HotelID INT FOREIGN KEY REFERENCES Hoteis(HotelID),
    QuartoID INT FOREIGN KEY REFERENCES Quartos(QuartoID),
    Tipo NVARCHAR(50),
    DataInicio DATE,
    DataFim DATE,
    Status NVARCHAR(50),
    Custo DECIMAL(10,2)
);
GO

-- Reclamacoes (Depende de Hoteis e Reservas)
CREATE TABLE Reclamacoes (
    ReclamacaoID INT PRIMARY KEY,
    ReservaID INT FOREIGN KEY REFERENCES Reservas(ReservaID),
    HotelID INT FOREIGN KEY REFERENCES Hoteis(HotelID),
    DataReclamacao DATE,
    Motivo NVARCHAR(200),
    Status NVARCHAR(50)
);
GO

-- MovimentosEstoque (Depende de Hoteis e EstoqueProdutos)
CREATE TABLE MovimentosEstoque (
    MovimentoID INT PRIMARY KEY,
    HotelID INT FOREIGN KEY REFERENCES Hoteis(HotelID),
    ProdutoID INT FOREIGN KEY REFERENCES EstoqueProdutos(ProdutoID),
    TipoMovimento NVARCHAR(10),
    Quantidade INT,
    DataMovimento DATE
);
GO

-- OcupacaoDiaria (Tabela de fatos para análise de ocupação)
CREATE TABLE OcupacaoDiaria (
    HotelID INT FOREIGN KEY REFERENCES Hoteis(HotelID),
    QuartoID INT FOREIGN KEY REFERENCES Quartos(QuartoID),
    Data DATE,
    TarifaEfetiva DECIMAL(10,2)
);
GO

```

## Popula Tabelas em Massa
```sql
USE HotelDB_Rede;
GO

-- 1?? Clientes
BULK INSERT Clientes
FROM 'C:\Users\natan\OneDrive\Desktop\HotelDB\hoteldb_rede_output\Clientes.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    CODEPAGE = '65001'
);
GO

-- 2?? Quartos
BULK INSERT Quartos
FROM 'C:\Users\natan\OneDrive\Desktop\HotelDB\hoteldb_rede_output\Quartos.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    CODEPAGE = '65001'
);
GO

-- 3?? Servi�os
BULK INSERT Servicos
FROM 'C:\Users\natan\OneDrive\Desktop\HotelDB\hoteldb_rede_output\Servicos.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    CODEPAGE = '65001'
);
GO

-- 4?? Departamentos
BULK INSERT Departamentos
FROM 'C:\Users\natan\OneDrive\Desktop\HotelDB\hoteldb_rede_output\Departamentos.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    CODEPAGE = '65001'
);
GO

-- 5?? Funcion�rios
BULK INSERT Funcionarios
FROM 'C:\Users\natan\OneDrive\Desktop\HotelDB\hoteldb_rede_output\Funcionarios.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    CODEPAGE = '65001'
);
GO

-- 6?? Reservas
BULK INSERT Reservas
FROM 'C:\Users\natan\OneDrive\Desktop\HotelDB\hoteldb_rede_output\Reservas.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    CODEPAGE = '65001'
);
GO

-- 7?? Pagamentos
BULK INSERT Pagamentos
FROM 'C:\Users\natan\OneDrive\Desktop\HotelDB\hoteldb_rede_output\Pagamentos.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    CODEPAGE = '65001'
);
GO

-- 8?? ReservaServicos
BULK INSERT ReservaServicos
FROM 'C:\Users\natan\OneDrive\Desktop\HotelDB\hoteldb_rede_output\ReservaServicos.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    CODEPAGE = '65001'
);
GO

-- 9?? Feedback
BULK INSERT Feedback
FROM 'C:\Users\natan\OneDrive\Desktop\HotelDB\hoteldb_rede_output\Feedback.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    CODEPAGE = '65001'
);
GO

PRINT 'Todos os CSVs foram importados com sucesso!';

```

## 3. 🔍 Análise e Extração de Dados com SQL  

### 🎯 Objetivo  
O **SQL** foi fundamental para conectar-se ao banco de dados e extrair informações relevantes para as análises.  

Foram feitas consultas com **filtros**, **junções** e **agregações**, criando datasets específicos para os **dashboards no Power BI**. 



### 📌 Análise de Desempenho Hoteleiro (Métricas Principais)  

```sql
WITH DiariasReservadas AS (
    SELECT 
        R.HotelID,
        R.ReservaID,
        DATEDIFF(DAY, R.DataCheckIn, R.DataCheckOut) AS DiariasOcupadas
    FROM Reservas R
),
ReceitaPorReserva AS (
    SELECT 
        R.HotelID,
        R.ReservaID,
        SUM(P.Valor) AS ReceitaReserva
    FROM Reservas R
    INNER JOIN Pagamentos P ON R.ReservaID = P.ReservaID
    GROUP BY R.HotelID, R.ReservaID
),
CapacidadeHotel AS (
    SELECT 
        H.HotelID,
        COUNT(Q.QuartoID) AS QtdeQuartos
    FROM Hoteis H
    INNER JOIN Quartos Q ON H.HotelID = Q.HotelID
    GROUP BY H.HotelID
)
SELECT 
    H.NomeHotel,
    YEAR(P.DataPagamento) AS Ano,
    MONTH(P.DataPagamento) AS Mes,
    CAST(SUM(RPR.ReceitaReserva) AS DECIMAL(10,2)) AS ReceitaTotal,
    CAST(SUM(DR.DiariasOcupadas) AS INT) AS DiariasOcupadas,
    (MAX(CH.QtdeQuartos) * DAY(EOMONTH(MAX(P.DataPagamento)))) AS DiariasDisponiveis,
    CAST(SUM(RPR.ReceitaReserva) / NULLIF(SUM(DR.DiariasOcupadas),0) AS DECIMAL(10,2)) AS ADR,
    CAST(SUM(DR.DiariasOcupadas) * 1.0 / 
             NULLIF((MAX(CH.QtdeQuartos) * DAY(EOMONTH(MAX(P.DataPagamento)))),0) * 100 AS DECIMAL(5,2)) 
             AS TaxaOcupacao,
    CAST(SUM(RPR.ReceitaReserva) / NULLIF((MAX(CH.QtdeQuartos) * DAY(EOMONTH(MAX(P.DataPagamento)))),0) AS DECIMAL(10,2)) 
             AS RevPAR
FROM ReceitaPorReserva RPR
INNER JOIN DiariasReservadas DR ON RPR.ReservaID = DR.ReservaID
INNER JOIN Reservas R ON R.ReservaID = DR.ReservaID
INNER JOIN Pagamentos P ON R.ReservaID = P.ReservaID
INNER JOIN Hoteis H ON R.HotelID = H.HotelID
INNER JOIN CapacidadeHotel CH ON H.HotelID = CH.HotelID
GROUP BY H.NomeHotel, YEAR(P.DataPagamento), MONTH(P.DataPagamento)
ORDER BY Ano, Mes, H.NomeHotel;

```

###📌 Análise de Temporalidade

```sql
SELECT
    YEAR(res.DataCheckIn) AS Ano,
    MONTH(res.DataCheckIn) AS Mes,
    SUM(pg.Valor) AS ReceitaMensal
FROM
    Reservas AS res
JOIN
    Pagamentos AS pg ON res.ReservaID = pg.ReservaID
GROUP BY
    YEAR(res.DataCheckIn),
    MONTH(res.DataCheckIn)
HAVING
    SUM(pg.Valor) > (
        SELECT AVG(ReceitaTotal_Mes)
        FROM (
            SELECT
                YEAR(res_sub.DataCheckIn) AS Ano,
                MONTH(res_sub.DataCheckIn) AS Mes,
                SUM(pg_sub.Valor) AS ReceitaTotal_Mes
            FROM
                Reservas AS res_sub
            JOIN 
                Pagamentos AS pg_sub ON res_sub.ReservaID = pg_sub.ReservaID
            GROUP BY
                YEAR(res_sub.DataCheckIn), MONTH(res_sub.DataCheckIn)
        ) AS ReceitaPorMes
    )
ORDER BY
    Ano, Mes DESC;
 ```
###📌 Análise de Clientes

```sql
SELECT
    tc.ClienteID,
    tc.Nome + ' ' + tc.Sobrenome AS NomeCliente,
    SUM(pg.Valor) AS GastoTotal,
    CASE
        WHEN SUM(pg.Valor) >= 10000 THEN 'Alto Valor'
        WHEN SUM(pg.Valor) >= 5000 AND SUM(pg.Valor) < 10000 THEN 'Médio Valor'
        ELSE 'Baixo Valor'
    END AS SegmentoDeValor
FROM
    Reservas AS res
JOIN
    Pagamentos AS pg ON res.ReservaID = pg.ReservaID
JOIN
    Clientes AS tc ON res.ClienteID = tc.ClienteID
GROUP BY
    tc.ClienteID,
    tc.Nome,
    tc.Sobrenome
ORDER BY
    SegmentoDeValor ;
```

###📌 Análise de Desempenho Operacional

```sql
SELECT
    tq.Tipo AS CategoriaQuarto,
    th.NomeHotel,
    count(tr.ReservaID) AS QuantidadeReservas,
    SUM(pg.Valor) AS ReceitaTotal
FROM
    Reservas AS tr
JOIN Pagamentos AS pg ON tr.ReservaID = pg.ReservaID
JOIN
    Hoteis AS th ON tr.HotelID = th.HotelID
JOIN
    Quartos AS tq ON tr.QuartoID = tq.QuartoID
GROUP BY
    tq.Tipo,
    th.NomeHotel
HAVING
    COUNT(tr.ReservaID) > 100
ORDER BY
    ReceitaTotal DESC;
```
---
## 4. 📈 Visualização e Dashboards (Power BI)  

### 🔹 Dashboard: Visão Geral de Desempenho da Rede

<img width="468" height="322" alt="view1" src="https://github.com/user-attachments/assets/519add2b-13e5-4405-93b8-ebbfb86af29d" />




### 📊 Conclusões Principais  
- **Receita Total da Rede:** R$ 9,63 bilhões  
- **Hotel Aurora Paulista** lidera com **R$ 3,3 bi**  
- **ADR alto:** R$ 45,1 mil e **taxa de ocupação baixa:** 11,1%  
- Forte **sazonalidade** (junho–agosto e dezembro com pico)  



### 📌 Resumo Executivo  
A rede fatura bem, mas depende de poucos ativos.  
O modelo de luxo gera boas receitas, porém há **oportunidade de otimizar a ocupação nos meses de baixa**.  

---

### 🔹 Dashboard: Análise de Temporalidade 

<img width="577" height="326" alt="view2" src="https://github.com/user-attachments/assets/408582e9-7bf4-45a2-a5dd-9b52a2c44f65" />



### 📊 Decisões Tomadas  
- Uso de **gráfico de linhas** para evolução mensal  
- **KPIs no topo** com Receita Total e Receita Média Mensal  
- Inclusão de **linha de referência da média** no gráfico  



### 📌 Resumo Executivo  
Mostra a **sazonalidade** e evidencia os **meses acima da média**.  

---

### 🔹 Dashboard: Segmentação de Clientes por Valor  

<img width="579" height="329" alt="view3" src="https://github.com/user-attachments/assets/b731a811-ac57-492f-a8ef-d51b5264609b" />




### 📊 Decisões  
- **Gráfico de barras** para distribuição  
- **KPIs** de clientes e gasto total  
- **Tabela detalhada** de clientes  
- Botão **"Limpar Filtros"**  



### 📌 Resumo Executivo  
A maioria dos clientes está em **baixo valor**, mas o painel destaca os **clientes de alto valor** para **ações estratégicas**.  

---

### 🔹 Dashboard: Desempenho por Quarto e Hotel  

<img width="580" height="323" alt="view4" src="https://github.com/user-attachments/assets/f806066c-612b-4372-a3a9-edd7fab24f68" />



### 📊 Decisões  
- **KPIs** de reservas e receita  
- **Gráfico de barras** comparando receita por categoria de quarto e hotel  
- Botão **"Limpar Filtros"**  



### 📌 Resumo Executivo  
A **Categoria Luxo** e o **Hotel Aurora Paulista** são os principais **motores de receita**.  


---
## 5. 🧑‍💻 Conclusão e Habilidades Adquiridas  

### 🔹 Habilidades  
- **Geração e Engenharia de Dados** (Python, Pandas, Faker)  
- **Modelagem de Banco de Dados** (SQL Server, PK/FK)  
- **Consultas SQL avançadas** (CTEs, joins, agregações)  
- **Dashboards em Power BI**  
- **Resolução de problemas técnicos e visuais**  

---

### 🔹 Aprendizados e Próximos Passos  
- Experiência no **ciclo completo de dados**  

**Próximos passos:**  
- Automatização **ETL**  
- **Análises preditivas** (demanda, churn)  
- **Dashboards web** com React + Tailwind  

---

## 6. 🛣️ Futuros Desenvolvimentos (Roadmap)  

**Próxima etapa:** criação de **dashboards interativos para web**.  

- **HTML & CSS/Tailwind** → layout responsivo  
- **React** → interface modular e dinâmica  
- **Python (backend)** → servir dados em tempo real  

📌 **Objetivo:** Uma solução de **BI web completa e personalizada**.  


### CONTATO
#### LinkedIn: https://www.linkedin.com/in/natanael-vicente-4b3b0a97/
#### Email: natancent@outlook.com
#### Phone: +55 (41)996807851
#### https://github.com/natancent1









 
