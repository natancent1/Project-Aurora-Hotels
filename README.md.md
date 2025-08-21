Análise de Dados de Hotéis: Do Banco de Dados ao Dashboard
1. Introdução e Objetivo do Projeto
Contexto
Este projeto de análise de dados tem como objetivo fornecer uma visão 360° do negócio de uma rede de hotéis, transformando dados brutos em insights acionáveis para a gestão. Isso permite à liderança tomar decisões estratégicas e mais informadas sobre clientes, desempenho operacional e rentabilidade.

Ferramentas Utilizadas
Python (Pandas, Faker)

SQL Server (SQL Management Studio)

Power BI Desktop

HTML, CSS/Tailwind

React

VS Code

2. Geração e Estrutura dos Dados
Etapa: Geração de Dados Sintéticos com Python
A primeira etapa do projeto consistiu na criação de um conjunto de dados simulado e realista, uma habilidade crucial quando dados reais não estão disponíveis. Para isso, utilizei a linguagem Python com as bibliotecas Pandas para manipulação e Faker para gerar informações realistas, como nomes, endereços e telefones. O script foi projetado para simular o ecossistema de uma rede de hotéis, gerando 18 tabelas inter-relacionadas, incluindo Hoteis, Clientes, Quartos, Reservas, Pagamentos, Funcionários e Manutenções, refletindo a complexidade de uma operação de negócio real.

Python

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

# ... (código Python para geração de dados) ...

def export_csv(df, name):
    path = os.path.join(OUTPUT_DIR, f"{name}.csv")
    df.to_csv(path, index=False, encoding="utf-8")
    print(f"OK -> {path}")

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
Etapa: Estrutura do Banco de Dados em SQL Server
Após a geração dos dados com Python, a próxima etapa foi a estruturação do banco de dados no SQL Server. Utilizando comandos SQL DDL (Data Definition Language), as tabelas foram criadas com o uso de chaves primárias e estrangeiras. As chaves primárias (PRIMARY KEY) foram usadas para garantir que cada registro seja único, enquanto as chaves estrangeiras (FOREIGN KEY) foram essenciais para estabelecer os relacionamentos entre as tabelas, como a ligação entre a tabela Reservas e as tabelas Clientes, Hoteis e Quartos. Por fim, utilizei a instrução BULK INSERT para carregar de forma eficiente todos os dados dos arquivos CSV para o banco de dados.

SQL

-- Cria banco de dados
IF DB_ID('Aurora Hotels') IS NULL
    CREATE DATABASE Aurora_Hotels_DB;
GO

USE Aurora_Hotels_DB;
GO

-- ... (código SQL de criação de tabelas e bulk insert) ...
3. Análise e Extração de Dados com SQL
Objetivo: A importância do SQL para a Análise de Dados
Nesta fase, a linguagem SQL foi fundamental para conectar-se ao banco de dados e extrair informações relevantes para as análises. O SQL permitiu não apenas a consulta aos dados, mas também a sua transformação através de filtros, junções entre tabelas e agregações, criando as métricas e os datasets específicos necessários para responder às perguntas de negócio. Cada consulta a seguir foi desenvolvida para um propósito analítico, servindo como a base para os dashboards no Power BI.

Análise de Desempenho Hoteleiro (Métricas Principais)
SQL

/* Esta consulta consolida as principais métricas de performance hoteleira para análise no Power BI.
    Ela utiliza Common Table Expressions (CTEs) para segmentar a lógica e melhorar a legibilidade do código.
    Cada CTE calcula uma métrica de base, que é então agregada e combinada na consulta principal.
*/
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
O que ela faz passo a passo:

1. CTEs (Expressões de Tabela Comum): A consulta usa CTEs para organizar o cálculo das métricas-base, tornando o código mais limpo e fácil de ler.

DiariasReservadas: Calcula o número de diárias de cada reserva, subtraindo a data de check-in da de check-out.

ReceitaPorReserva: Soma o valor de todos os pagamentos de uma reserva, obtendo a receita total por reserva.

CapacidadeHotel: Conta o número total de quartos em cada hotel.

2. Consulta Principal: A consulta principal junta os resultados das CTEs com as tabelas de Hoteis, Reservas e Pagamentos para combinar as informações no nível de hotel, ano e mês.

3. Cálculo das Métricas:

ReceitaTotal: Soma a receita de todas as reservas no período.

DiariasOcupadas: Soma o número de diárias ocupadas de todas as reservas confirmadas.

DiariasDisponiveis: Multiplica a capacidade total de quartos de cada hotel pelo número de dias do mês. O DAY(EOMONTH(...)) garante que o número de dias seja exato para cada mês.

ADR (Average Daily Rate): Calcula a Receita Média por Diária Ocupada, dividindo a Receita Total pelas Diárias Ocupadas. O NULLIF é usado para evitar erro de divisão por zero.

Taxa de Ocupação: Calcula a porcentagem de ocupação, dividindo as Diárias Ocupadas pelas Diárias Disponíveis.

RevPAR (Revenue Per Available Room): Calcula a Receita por Diária Disponível, dividindo a Receita Total pelas Diárias Disponíveis. Esta é uma métrica chave que combina preço e ocupação.

4. Agrupamento e Ordenação: A consulta agrupa todos os cálculos por hotel, ano e mês, e por fim ordena o resultado para uma melhor visualização cronológica.

Análise de Temporalidade
SQL

-- Análise de Temporalidade: Receita Mensal Acima da Média
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
O que ela está fazendo passo a passo:

Agrupamento por mês/ano: Ela pega as reservas (Reservas) e junta com os pagamentos (Pagamentos) para somar o valor total recebido em cada mês.

Cálculo da Receita Mensal: Para cada mês (de cada ano), calcula SUM(pg.Valor) → isso é a ReceitaMensal.

Comparação com a média: No HAVING, a consulta filtra e mantém somente os meses em que a receita foi maior do que a média geral de todos os meses.

Ordenação: No fim, ela ordena o resultado por ano e mês (decrescente dentro do ano), para mostrar numa linha do tempo.

Análise de Clientes
SQL

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
O que a query faz:

Junta as tabelas: Reservas (res), Pagamentos (pg) e Clientes (tc).

Calcula o gasto total por cliente: Para cada cliente, soma (SUM(pg.Valor)) o valor de todos os pagamentos ligados às suas reservas.

Classifica os clientes em segmentos: Usa um CASE para segmentar o gasto total (Alto Valor, Médio Valor, Baixo Valor).

Agrupa por cliente: O GROUP BY garante que cada cliente apareça uma vez, já com o gasto total consolidado.

Ordena pelo segmento: No ORDER BY, ele organiza a saída de acordo com o segmento de valor.

Análise de Desempenho Operacional
SQL

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
O que a query faz:

Junta tabelas: Reservas (tr), Pagamentos (pg), Hoteis (th) e Quartos (tq).

Agrupa por tipo de quarto + hotel: Cada linha do resultado vai mostrar um tipo de quarto em um hotel específico.

Métricas calculadas: COUNT(tr.ReservaID) (Quantidade de Reservas) e SUM(pg.Valor) (Receita Total).

Filtro no HAVING: Só traz combinações (hotel + tipo de quarto) que tiveram mais de 100 reservas.

Ordenação: Ordena os resultados em ordem decrescente pela receita total (ReceitaTotal DESC), ou seja, mostra primeiro os tipos de quarto + hotel que mais faturaram.

4. Visualização e Dashboards (Power BI)
Dashboard: Visão Geral de Desempenho da Rede
[Inserir imagem do dashboard de visão geral aqui]

📊 Conclusões Principais

Receita Total da Rede: A rede como um todo gerou R$ 9,63 bilhões em receita no período analisado.

Hotéis que puxam o resultado: O Hotel Aurora Paulista é o líder, com R$ 3,3 bi, seguido pelo Aurora Ipanema (R$ 2,1 bi). Juntos, eles respondem por mais de 50% de toda a receita da rede, mostrando um risco de concentração.

Indicadores de Desempenho (KPIs): O ADR alto (R$ 45,1 mil) e a taxa de ocupação baixa (11,1%) indicam um modelo de negócio focado em luxo/exclusividade, mas com potencial de otimização da ocupação.

Performance ao longo do ano (sazonalidade): O gráfico mostra que o RevPAR sobe bastante entre junho e agosto, com pico no final de dezembro, enquanto setembro é um ponto fraco, indicando forte sazonalidade.

📌 Resumo Executivo: A rede fatura bem, mas depende de poucos ativos e tem um modelo de luxo com oportunidades para aumentar a ocupação em meses de baixa. Estratégias de marketing ou eventos em meses fracos poderiam suavizar a queda.

Dashboard: Análise de Temporalidade
[Inserir imagem do dashboard de análise de temporalidade aqui]

🎯 Decisões Tomadas no Dashboard

Uso do gráfico de linhas: O gráfico de linhas é o mais adequado para mostrar a evolução da receita ao longo do tempo, evidenciando picos e quedas.

KPIs principais em destaque: Os KPIs grandes no topo (Receita Total e Receita Média Mensal) resumem o painel, dando uma visão imediata dos números-chave.

Linha de referência da média: A linha horizontal no gráfico serve como um comparativo visual rápido, mostrando se um mês está acima ou abaixo da média.

📌 Resumo executivo: Este painel destaca os meses de melhor performance, mostrando a sazonalidade e pontos fora da curva. As visualizações e KPIs foram escolhidos para dar ao gestor uma visão rápida e clara das tendências de receita.

Dashboard: Segmentação de Clientes por Valor
[Inserir imagem do dashboard de segmentação de clientes aqui]

🎯 Decisões de Construção e Leitura do Painel

Gráfico de barras: Mostra a distribuição dos clientes por segmento de valor (Baixo, Médio e Alto Valor), deixando claro que a maioria está no segmento de baixo valor.

KPIs em destaque: Indicam o número total de clientes e o gasto total, fornecendo uma visão geral da base e seu impacto financeiro.

Tabela detalhada: Complementa o gráfico, trazendo os dados individuais dos clientes, o que é essencial para identificar e planejar ações para os clientes estratégicos de Alto Valor.

Botão "Limpar Filtros": Aumenta a agilidade e a usabilidade do painel, permitindo que o usuário redefina a visualização rapidamente.

📌 Resumo executivo: Este painel segmenta os clientes por valor, mostrando a concentração no segmento de Baixo Valor. Ele é crucial para a gestão identificar clientes estratégicos e planejar campanhas de fidelização ou promoções personalizadas.

Dashboard: Desempenho por Quarto e Hotel
[Inserir imagem do dashboard de desempenho por quarto e hotel aqui]

🎯 Decisões de Construção e Leitura do Painel

KPIs em destaque: Utilizei os KPIs para dar uma visão imediata do valor total das reservas e do volume de reservas, servindo como um resumo executivo para a liderança.

Gráfico de barras: Compara a receita entre as diferentes categorias de quartos e entre os hotéis da rede, facilitando a identificação dos maiores contribuidores de receita.

Botão "Limpar Filtros": Permite que o usuário redefina a visualização rapidamente após aplicar filtros.

📌 Resumo Executivo: O dashboard de Desempenho por Quarto e Hotel oferece uma visão clara e comparativa da operação. Ele destaca que a categoria de quartos Luxo e o Hotel Aurora Paulista são os principais motores de receita, fornecendo as informações necessárias para que a gestão possa tomar decisões estratégicas.

5. Conclusão e Habilidades Adquiridas
Habilidades
Através da construção deste projeto, demonstrei um conjunto de habilidades técnicas e analíticas fundamentais, aliadas à persistência necessária para transformar uma ideia em um produto final completo. As principais habilidades aplicadas incluem:

Geração e Engenharia de Dados: A capacidade de criar um conjunto de dados robusto e realista do zero usando Python (Pandas e Faker) para simular um cenário de negócio.

Modelagem de Banco de Dados: A habilidade de estruturar dados brutos de forma organizada e eficiente no SQL Server, definindo chaves primárias e relacionamentos para garantir a integridade dos dados.

Análise e Manipulação de Dados (SQL): A proficiência em escrever consultas SQL complexas para extrair, filtrar e agregar dados, transformando-os em informações prontas para a análise.

Visualização e Business Intelligence: A aptidão para utilizar o Power BI para criar dashboards interativos e intuitivos, traduzindo dados e insights complexos em visualizações de fácil entendimento para o público de negócio.

Resolução de Problemas: A capacidade de identificar e solucionar desafios técnicos, como a ordenação de eixos em gráficos temporais ou a correção de fontes de dados, mostrando resiliência e foco na conclusão do projeto.

Aprendizados e Próximos Passos
A conclusão deste projeto representou uma experiência valiosa e imersiva no ciclo de vida completo de um projeto de dados. O maior aprendizado foi a prática de transformar um problema de negócio, desde a ausência de dados até a entrega de dashboards interativos, o que solidificou meu entendimento sobre a importância de cada etapa do processo.

Como próximo passo, pretendo expandir meu 'cinto de utilidades' para explorar outras áreas da ciência de dados. A partir deste projeto, o foco agora é aprimorar o pipeline de dados com automação de ETL e avançar para análises mais preditivas, como a previsão de demanda por quartos ou a identificação de clientes com alto risco de churn. Meu objetivo é continuar a me aprofundar em novas tecnologias e metodologias, para me posicionar como um profissional de dados versátil e preparado para os desafios do mercado de trabalho.

6. Futuros Desenvolvimentos (Roadmap)
Para elevar a experiência da visualização, o próximo passo será a criação de dashboards totalmente interativos e personalizados para a web, usando um stack de tecnologias moderno e focado em usabilidade:

HTML & CSS/Tailwind: Para criar a estrutura e o design responsivo dos dashboards.

React: Para construir a interface de usuário de forma modular e dinâmica, garantindo a interatividade.

Python: Para atuar como o backend, processando os dados e servindo-os para a aplicação web em tempo real.

Este avanço permitirá a implementação de dashboards com layouts e funcionalidades que atendem a necessidades de negócio específicas, oferecendo uma solução de BI completa e personalizada.