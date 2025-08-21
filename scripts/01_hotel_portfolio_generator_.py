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