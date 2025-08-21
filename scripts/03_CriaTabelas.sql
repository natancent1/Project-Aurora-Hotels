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