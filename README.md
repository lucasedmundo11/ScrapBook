# ScrapBook API

Uma API RESTful completa para web scraping de livros com foco em Machine Learning Engineering. Este projeto extrai dados de livros do site [books.toscrape.com](http://books.toscrape.com/) e disponibiliza através de uma API robusta construída com Flask e SQLAlchemy.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Funcionalidades](#funcionalidades)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Execução](#execução)
- [Documentação da API](#documentação-da-api)
- [Endpoints](#endpoints)
- [Exemplos de Uso](#exemplos-de-uso)
- [Autenticação](#autenticação)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Contribuição](#contribuição)

## 🚀 Visão Geral

O ScrapBook API é um sistema completo de web scraping e análise de dados de livros, projetado com as melhores práticas de Machine Learning Engineering. O projeto inclui:

- **Web Scraping Robusto**: Sistema de extração de dados com retry logic e rate limiting
- **API RESTful Completa**: 20+ endpoints para gerenciamento de dados
- **Autenticação JWT**: Sistema seguro de autenticação e autorização
- **Documentação Swagger**: Interface interativa para explorar a API
- **Gerenciamento de Usuários**: Sistema completo de CRUD para usuários
- **Pipeline de ML**: Endpoints específicos para features de Machine Learning
- **Monitoramento**: Sistema de logs estruturados e métricas

## 🏗️ Arquitetura

```
ScrapBook/
├── src/
│   ├── api/              # API Flask com endpoints RESTful
│   ├── scripts/          # Sistema de web scraping
│   ├── config/           # Configurações centralizadas
├── data/
│   ├── csv/              # Dados extraídos em CSV
│   ├── json/             # Dados em formato JSON
│   └── logs/             # Logs do sistema
├── docs/
│   └── resources/        # Documentação de Funcionalidades e Requisitos Funcionais
│   └── swagger/          # Documentação Swagger YAML
└── tests/                # Testes automatizados
```

### Componentes Principais

1. **Web Scraper**: Sistema baseado em BeautifulSoup para extração de dados
2. **API REST**: Flask + SQLAlchemy para endpoints RESTful
3. **Banco de Dados**: SQLAlchemy com suporte a SQLite/PostgreSQL
4. **Autenticação**: JWT com Flask-JWT-Extended
5. **Documentação**: Swagger/OpenAPI com Flasgger

## ✨ Funcionalidades

### Core Features
- ✅ Listagem paginada de livros
- ✅ Busca avançada por título, categoria, preço e rating
- ✅ Estatísticas e insights dos dados
- ✅ Filtros por faixa de preço
- ✅ Top livros mais bem avaliados

### Sistema de Usuários
- ✅ Registro e login de usuários
- ✅ Gerenciamento completo de usuários (CRUD)
- ✅ Controle de acesso baseado em roles (admin/user)
- ✅ Alteração de senha segura

### Web Scraping
- ✅ Execução manual de scraping via API
- ✅ Monitoramento de jobs de scraping
- ✅ Histórico de execuções
- ✅ Rate limiting e retry logic

### Machine Learning
- ✅ Endpoints para features engineering
- ✅ Datasets formatados para treinamento
- ✅ Interface para predições de modelos

## 🔧 Instalação

### Pré-requisitos

- Python 3.11+
- pip
- virtualenv (recomendado)

### Passo a Passo

1. **Clone o repositório**
```bash
git clone <repository-url>
cd ScrapBook
```

2. **Crie e ative o ambiente virtual**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Configure as variáveis de ambiente**
```bash
cp .env.example .env  # Se disponível
# ou crie um arquivo .env com as configurações necessárias
```

## ⚙️ Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# API Settings
API_HOST=localhost
API_PORT=8000

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite:///./data/books.db

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Configuração do Banco de Dados

O sistema criará automaticamente:
- Banco de dados SQLite em `data/books.db`
- Usuário admin padrão: `admin`/`admin123`
- Usuário comum padrão: `user`/`user123`

## 🚀 Execução

### Iniciar a API

```bash
# Método 1: Via módulo
python -m src.api.main

# Método 2: Executar diretamente
cd src/api && python main.py

# Método 3: Com script personalizado (se disponível)
./start_api.sh
```

A API estará disponível em: `http://localhost:8000`

### Acessar Documentação

- **Swagger UI**: http://localhost:8000/docs
- **API Spec**: http://localhost:8000/apispec.json
- **Health Check**: http://localhost:8000/api/v1/health

## 📚 Documentação da API

### Base URL
```
http://localhost:8000/api/v1
```

### Autenticação
A API usa JWT Bearer tokens. Para endpoints protegidos, inclua o header:
```
Authorization: Bearer <seu-jwt-token>
```

### Response Format
Todas as respostas seguem o padrão:

```json
{
  "success": true,
  "data": { ... },
  "message": "Success message",
  "timestamp": "2025-08-10T10:30:00Z"
}
```

Para erros:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description",
    "details": { ... }
  },
  "timestamp": "2025-08-10T10:30:00Z"
}
```

## 🛣️ Endpoints

### 🔍 Core Endpoints

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/health` | Status da API | ❌ |
| `GET` | `/books` | Lista todos os livros | ❌ |
| `GET` | `/books/{id}` | Detalhes de um livro | ❌ |
| `GET` | `/books/search` | Busca livros | ❌ |
| `GET` | `/categories` | Lista categorias | ❌ |

### 📊 Endpoints de Insights

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/stats/overview` | Estatísticas gerais | ❌ |
| `GET` | `/stats/categories` | Stats por categoria | ❌ |
| `GET` | `/books/top-rated` | Top livros avaliados | ❌ |
| `GET` | `/books/price-range` | Filtro por preço | ❌ |

### 🔐 Autenticação

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `POST` | `/auth/login` | Login do usuário | ❌ |
| `POST` | `/auth/refresh` | Renovar token | ❌ |

### 👥 Gerenciamento de Usuários

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/users` | Listar usuários | ✅ Admin |
| `POST` | `/users` | Criar usuário | ✅ Admin |
| `PUT` | `/users/{id}` | Atualizar usuário | ✅ Admin/Own |
| `PUT` | `/users/{id}/password` | Alterar senha | ✅ Admin/Own |
| `GET` | `/users/me` | Perfil atual | ✅ |

### 🤖 Machine Learning

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `GET` | `/ml/features` | Features para ML | ❌ |
| `GET` | `/ml/training-data` | Dataset treinamento | ❌ |
| `POST` | `/ml/predictions` | Fazer predições | ❌ |

### 🕷️ Web Scraping

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| `POST` | `/scraping/trigger` | Iniciar scraping | ✅ Admin |
| `GET` | `/scraping/status/{job_id}` | Status do job | ✅ Admin |
| `GET` | `/scraping/jobs` | Listar jobs | ✅ Admin |

## 📖 Exemplos de Uso

### 1. Login e Obtenção de Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 1800
  },
  "message": "Login successful",
  "timestamp": "2025-08-10T15:30:00Z"
}
```

### 2. Listar Livros com Paginação

```bash
curl -X GET "http://localhost:8000/api/v1/books?page=1&limit=5&sort_by=price&sort_order=desc"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "books": [
      {
        "id": 1,
        "title": "A Light in the Attic",
        "price": 51.77,
        "rating": 3,
        "availability": "In stock",
        "category": "Poetry",
        "image_url": "catalogue/images/products/51/51.jpg"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 200,
      "total_books": 1000,
      "has_next": true,
      "has_prev": false
    }
  },
  "message": "Retrieved 5 books",
  "timestamp": "2025-08-10T15:30:00Z"
}
```

### 3. Buscar Livros

```bash
curl -X GET "http://localhost:8000/api/v1/books/search?title=Light&category=Poetry&min_price=30&max_price=60"
```

### 4. Criar Usuário (Admin)

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <seu-token>" \
  -d '{
    "username": "newuser",
    "email": "user@example.com",
    "password": "password123",
    "is_admin": false
  }'
```

### 5. Executar Scraping

```bash
curl -X POST http://localhost:8000/api/v1/scraping/trigger \
  -H "Authorization: Bearer <seu-token>"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "scraping_job_20250810_153045",
    "status": "started",
    "message": "Scraping job started successfully"
  },
  "message": "Scraping process started",
  "timestamp": "2025-08-10T15:30:45Z"
}
```

### 6. Verificar Status do Scraping

```bash
curl -X GET http://localhost:8000/api/v1/scraping/status/scraping_job_20250810_153045 \
  -H "Authorization: Bearer <seu-token>"
```

### 7. Obter Estatísticas

```bash
curl -X GET http://localhost:8000/api/v1/stats/overview
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_books": 1000,
    "total_categories": 50,
    "average_price": 35.67,
    "average_rating": 3.2,
    "most_expensive_book": {
      "title": "Expensive Book",
      "price": 58.99
    },
    "cheapest_book": {
      "title": "Cheap Book", 
      "price": 10.00
    }
  },
  "message": "Overview statistics retrieved successfully",
  "timestamp": "2025-08-10T15:30:00Z"
}
```

## 🔐 Autenticação

### Usuários Padrão

O sistema vem com usuários pré-configurados:

| Username | Password | Role | Descrição |
|----------|----------|------|-----------|
| `admin` | `admin123` | Admin | Acesso completo ao sistema |
| `user` | `user123` | User | Acesso limitado aos endpoints públicos |

### Criação de Novos Usuários

Apenas administradores podem criar novos usuários através do endpoint `/users`.

### Expiração de Tokens

- **Access Token**: 30 minutos (configurável)
- **Refresh Token**: 7 dias (configurável)

## 🗂️ Estrutura do Projeto

```
ScrapBook/
├── .venv/                          # Ambiente virtual Python
├── data/                           # Dados extraídos e logs
│   ├── csv/                        # Arquivos CSV dos livros
│   │   ├── books_detailed_*.csv    # Dados detalhados dos livros
│   │   └── categories_*.csv        # Lista de categorias
│   ├── json/                       # Dados em formato JSON
│   └── logs/                       # Logs do sistema
├── docs/                           # Documentação
│   └── swagger/                    # Specs Swagger YAML
│       ├── auth_*.yaml            # Endpoints de autenticação
│       ├── books_*.yaml           # Endpoints de livros
│       ├── users_*.yaml           # Endpoints de usuários
│       └── *.yaml                 # Outros endpoints
├── src/                            # Código fonte principal
│   ├── api/                        # API Flask
│   │   ├── main.py                # Aplicação principal
│   │   ├── auth.py                # Sistema de autenticação
│   │   ├── database.py            # Gerenciador do banco
│   │   └── models.py              # Modelos SQLAlchemy/Pydantic
│   ├── config/                     # Configurações
│   │   ├── api.py                 # Config da API
│   │   └── Scrapper.py            # Config do scraper
│   └── scripts/                    # Sistema de scraping
│       ├── main_scraper.py        # Orquestrador principal
│       ├── book_scraper.py        # Scraper de livros
│       ├── category_scraper.py    # Scraper de categorias
│       └── utils/                 # Utilitários
├── tests/                          # Testes automatizados
├── requirements.txt                # Dependências Python
├── .env.example                    # Exemplo de variáveis de ambiente
└── README.md                       # Este arquivo
```

## 🧪 Testes

### Executar Testes

```bash
# Todos os testes
pytest

# Testes específicos
pytest tests/test_api.py
pytest tests/test_scraper.py

# Com cobertura
pytest --cov=src tests/
```

### Health Check

Verifique se a API está funcionando:

```bash
curl http://localhost:8000/api/v1/health
```

## 🔄 Pipeline de Dados

### Fluxo do Scraping

1. **Trigger Manual**: Via endpoint `/scraping/trigger`
2. **Extração**: Scraping do site books.toscrape.com
3. **Processamento**: Limpeza e validação dos dados
4. **Armazenamento**: Salvamento em CSV e banco de dados
5. **Notificação**: Job status disponível via API

### Estrutura dos Dados

Os dados extraídos incluem:
- **Title**: Título do livro
- **Price**: Preço em GBP
- **Rating**: Avaliação (1-5 estrelas)
- **Availability**: Status de disponibilidade
- **Category**: Categoria/gênero
- **Image URL**: URL da imagem da capa
- **Description**: Descrição do livro

## 📊 Monitoramento e Logs

### Sistema de Logs

- **Structured Logging**: Logs em formato JSON
- **Diferentes Níveis**: INFO, WARNING, ERROR
- **Rotação Automática**: Para evitar arquivos grandes
- **Localização**: `data/logs/`

### Métricas Disponíveis

- Tempo de resposta dos endpoints
- Número de requisições por minuto
- Erros e exceções
- Status dos jobs de scraping

## 🚀 Deploy

### Desenvolvimento Local

```bash
python -m src.api.main
```

### Produção

O sistema está preparado para deploy em:
- **Heroku**
- **Render**
- **AWS**
- **Docker**

### Variáveis de Ambiente para Produção

```env
API_HOST=0.0.0.0
API_PORT=5000
JWT_SECRET_KEY=<strong-secret-key>
DATABASE_URL=postgresql://user:pass@host:port/db
CORS_ORIGINS=https://yourdomain.com
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

- **Documentação**: http://localhost:8000/docs
- **Issues**: GitHub Issues
- **Email**: support@scrapbook-api.com

---

**Desenvolvido com ❤️ para Machine Learning Engineering**
