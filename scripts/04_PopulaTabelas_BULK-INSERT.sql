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

-- 3?? Serviços
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

-- 5?? Funcionários
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
