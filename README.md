# Teste de Nivelamento ANS

## 📌 Visão Geral

Este projeto implementa uma solução para o teste de nivelamento da ANS, com foco na importação e análise de dados de operadoras de saúde e suas demonstrações contábeis.

## 🚀 Funcionalidades Implementadas

### ✅ Parte 1 - Web Scraping
- Download automatizado dos anexos I e II do site da ANS
- Compactação dos arquivos em formato ZIP

### ✅ Parte 2 - Transformação de Dados
- Extração de dados das tabelas em PDF
- Conversão para formato CSV estruturado
- Substituição de abreviações pelas descrições completas

### ✅ Parte 3 - Banco de Dados
- Importação de dados de operadoras ativas
- Processamento de demonstrações contábeis
- Consultas analíticas:
  - Top 10 operadoras com maiores despesas por trimestre
  - Top 10 operadoras com maiores despesas por ano

### ✅ Parte 4 - API e Frontend
- Interface web desenvolvida com Vite.js
- Servidor Python para busca de operadoras
- Integração web-server

## 🛠️ Tecnologias Utilizadas

- **Frontend**: Vite, React
- **Backend**: Python, FastAPI, SQLAlchemy
- **Banco de Dados**: PostgreSQL, Neon
- **Processamento de Dados**: Pandas, pdfplumber
- **Web Scraping**: BeautifulSoup, requests

## ⚙️ Configuração do Ambiente

1. Clone o repositório:
```bash
git clone https://github.com/joaovictor-sm/ans-test-project
```

2. Instale as dependências do web:
```bash
cd web
npm install
```

3. Configure o ambiente Python:
```bash
cd server
python -m venv venv
source venv/bin/activate  # Linux/Mac)
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

4. Configure o arquivo `.env` com suas credenciais de banco de dados

## 🏃 Execução

1. Inicie o servidor server:
```bash
cd server
python main.py
```

2. Inicie o web:
```bash
cd web
npm run dev
```

## 📊 Estrutura do Projeto

```
ans-test-project/
├── server/                   # Código Python
│   ├── data_transformation/  # Transformação de dados
│   ├── database/             # Modelos de banco de dados
│   ├── main.py               # Servidor principal
│   ├── web_scraping/         # Rotinas de web scraping
│   ├── data/                 # Dados e arquivos estáticos
│   └── test_connection.py    # Teste de conexão
├── web/                      # Aplicação Vite.js
│   ├── public/               # Arquivos públicos
│   ├── src/                  # Código fonte do frontend
│   └── vite.config.js        # Configuração do Vite
└── README.md                 # Documentação do projeto
```

## 🤝 Contribuição

Este projeto foi desenvolvido como parte de um teste técnico. Para quaisquer dúvidas, entre em contato com o autor.
