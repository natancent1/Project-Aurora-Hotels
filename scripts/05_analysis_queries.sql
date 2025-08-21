-------------------------------------------------------------------------------
-- 1. ANÁLISE DE DESEMPENHO HOTELEIRO (MÉTRICAS PRINCIPAIS)
-- Objetivo: Consolidar métricas de performance como RevPAR, ADR e Taxa de Ocupação
-------------------------------------------------------------------------------

/*
Esta consulta utiliza Common Table Expressions (CTEs) para segmentar a lógica,
calculando métricas de base para então agregá-las na consulta principal.
Isso melhora a legibilidade e a manutenção do código.
*/

-- CTE 1: Calcula o número de diárias ocupadas para cada reserva.
WITH DiariasReservadas AS (
    SELECT 
        R.HotelID,
        R.ReservaID,
        DATEDIFF(DAY, R.DataCheckIn, R.DataCheckOut) AS DiariasOcupadas
    FROM Reservas R
),

-- CTE 2: Agrega o valor total de pagamentos para cada reserva, obtendo a receita por reserva.
ReceitaPorReserva AS (
    SELECT 
        R.HotelID,
        R.ReservaID,
        SUM(P.Valor) AS ReceitaReserva
    FROM Reservas R
    INNER JOIN Pagamentos P ON R.ReservaID = P.ReservaID
    GROUP BY R.HotelID, R.ReservaID
),

-- CTE 3: Determina a capacidade total de quartos de cada hotel.
CapacidadeHotel AS (
    SELECT 
        H.HotelID,
        COUNT(Q.QuartoID) AS QtdeQuartos
    FROM Hoteis H
    INNER JOIN Quartos Q ON H.HotelID = Q.HotelID
    GROUP BY H.HotelID
)

-- Consulta Principal: Agrega todas as métricas por hotel, ano e mês.
SELECT 
    H.NomeHotel,
    YEAR(P.DataPagamento) AS Ano,
    MONTH(P.DataPagamento) AS Mes,
    
    -- Métrica: Receita Total (Soma da receita de todas as reservas no período)
    CAST(SUM(RPR.ReceitaReserva) AS DECIMAL(10,2)) AS ReceitaTotal,
    
    -- Métrica: Diárias Ocupadas (Soma de todas as diárias ocupadas no período)
    CAST(SUM(DR.DiariasOcupadas) AS INT) AS DiariasOcupadas,
    
    -- Métrica: Diárias Disponíveis (Capacidade total de quartos * número de dias do mês)
    (MAX(CH.QtdeQuartos) * DAY(EOMONTH(MAX(P.DataPagamento)))) AS DiariasDisponiveis,
    
    -- Métrica: ADR (Average Daily Rate) - Receita Média por Diária Ocupada
    CAST(SUM(RPR.ReceitaReserva) / NULLIF(SUM(DR.DiariasOcupadas),0) AS DECIMAL(10,2)) AS ADR,
    
    -- Métrica: Taxa de Ocupação (%) - Diárias Ocupadas em relação às Disponíveis
    CAST(SUM(DR.DiariasOcupadas) * 1.0 / 
             NULLIF((MAX(CH.QtdeQuartos) * DAY(EOMONTH(MAX(P.DataPagamento)))),0) * 100 AS DECIMAL(5,2)) 
             AS TaxaOcupacao,
    
    -- Métrica: RevPAR (Revenue Per Available Room) - Receita por Diária Disponível
    CAST(SUM(RPR.ReceitaReserva) / NULLIF((MAX(CH.QtdeQuartos) * DAY(EOMONTH(MAX(P.DataPagamento)))),0) AS DECIMAL(10,2)) 
             AS RevPAR
FROM ReceitaPorReserva RPR
-- Junções para vincular todas as CTEs e tabelas.
INNER JOIN DiariasReservadas DR ON RPR.ReservaID = DR.ReservaID
INNER JOIN Reservas R ON R.ReservaID = DR.ReservaID
INNER JOIN Pagamentos P ON R.ReservaID = P.ReservaID
INNER JOIN Hoteis H ON R.HotelID = H.HotelID
INNER JOIN CapacidadeHotel CH ON H.HotelID = CH.HotelID
GROUP BY H.NomeHotel, YEAR(P.DataPagamento), MONTH(P.DataPagamento)
ORDER BY Ano, Mes, H.NomeHotel;


-------------------------------------------------------------------------------
-- 2. ANÁLISE DE TEMPORALIDADE
-- Objetivo: Identificar meses de alta receita, comparando-os com a média geral.
-------------------------------------------------------------------------------

-- Seleciona o ano, o mês e a receita total mensal.
SELECT
    YEAR(res.DataCheckIn) AS Ano,
    MONTH(res.DataCheckIn) AS Mes,
    SUM(pg.Valor) AS ReceitaMensal
FROM
    Reservas AS res
-- Junta a tabela de Pagamentos para acessar o valor de cada reserva.
JOIN
    Pagamentos AS pg ON res.ReservaID = pg.ReservaID
-- Agrupa os dados por ano e mês para calcular a receita mensal.
GROUP BY
    YEAR(res.DataCheckIn),
    MONTH(res.DataCheckIn)
-- Filtra os grupos (meses) cuja receita total seja maior que a receita média de todos os meses.
HAVING
    SUM(pg.Valor) > (
        -- Subconsulta para calcular a receita média mensal.
        SELECT AVG(ReceitaTotal_Mes)
        FROM (
            -- Subconsulta interna que calcula a receita total para cada mês.
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
-- Ordena o resultado por ano e mês para ter uma visualização cronológica.
ORDER BY
    Ano, Mes DESC;


-------------------------------------------------------------------------------
-- 3. ANÁLISE DE CLIENTES
-- Objetivo: Segmentar clientes com base em seu gasto total para identificar grupos de valor.
-------------------------------------------------------------------------------

SELECT
    tc.ClienteID,
    tc.Nome + ' ' + tc.Sobrenome AS NomeCliente,
    SUM(pg.Valor) AS GastoTotal,
    -- Classifica o cliente em Alto, Médio ou Baixo valor com base no Gasto Total
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
    Clientes AS tc ON res.ClienteID = tc.ClienteID  -- Liga a tabela de Clientes
GROUP BY
    tc.ClienteID,
    tc.Nome,
    tc.Sobrenome
ORDER BY
    SegmentoDeValor;


-------------------------------------------------------------------------------
-- 4. ANÁLISE DE DESEMPENHO OPERACIONAL
-- Objetivo: Avaliar o desempenho de cada tipo de quarto e hotel em termos de reservas e receita.
-------------------------------------------------------------------------------

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
-- Filtra apenas as combinações de quarto/hotel com mais de 100 reservas.
HAVING
    COUNT(tr.ReservaID) > 100
-- Ordena os resultados para mostrar os mais lucrativos primeiro.
ORDER BY
    ReceitaTotal DESC;