# Copilot Instructions - API de Web Scraping de Livros

## Contexto do Projeto

Este é um projeto de **API RESTful** com sistema de **Web Scraping** para extrair dados de livros de https://books.toscrape.com/. O projeto é estruturado como um pipeline de dados completo com foco em Machine Learning Engineering.

## Arquitetura e Estrutura

### Estrutura de Diretórios
```
scripts/     # Scripts de web scraping
api/         # Código da API REST
data/        # Arquivos CSV e dados processados
docs/        # Documentação
tests/       # Testes automatizados
```

### Stack Tecnológica
- **Framework API**: FastAPI ou Flask
- **Web Scraping**: BeautifulSoup, Scrapy ou Requests
- **Autenticação**: JWT
- **Documentação**: Swagger/OpenAPI
- **Deploy**: Heroku, Render, Vercel ou Fly.io
- **Monitoramento**: Streamlit Dashboard

## Endpoints da API

### Endpoints Core (Obrigatórios)
```
GET /api/v1/books                                    # Lista todos os livros
GET /api/v1/books/{id}                              # Detalhes de um livro específico
GET /api/v1/books/search?title={title}&category={category}  # Busca por título/categoria
GET /api/v1/categories                              # Lista todas as categorias
GET /api/v1/health                                  # Status da API
```

### Endpoints de Insights
```
GET /api/v1/stats/overview                          # Estatísticas gerais
GET /api/v1/stats/categories                        # Estatísticas por categoria
GET /api/v1/books/top-rated                         # Livros melhor avaliados
GET /api/v1/books/price-range?min={min}&max={max}   # Filtro por faixa de preço
```

### Endpoints de Autenticação (JWT)
```
POST /api/v1/auth/login                             # Obter token
POST /api/v1/auth/refresh                           # Renovar token
```

### Endpoints para ML
```
GET /api/v1/ml/features                             # Dados formatados para features
GET /api/v1/ml/training-data                        # Dataset para treinamento
POST /api/v1/ml/predictions                         # Endpoint para predições
```

### Endpoints Administrativos (Protegidos)
```
POST /api/v1/scraping/trigger                       # Disparar scraping manualmente
```

## Modelo de Dados

### Estrutura do Livro
```python
{
    "id": int,
    "title": str,
    "price": float,
    "rating": int,  # 1-5 estrelas
    "availability": str,
    "category": str,
    "image_url": str,
    "created_at": datetime,
    "updated_at": datetime
}
```

### Campos do Web Scraping
Extrair de https://books.toscrape.com/:
- Título do livro
- Preço
- Rating (1-5 estrelas)
- Disponibilidade
- Categoria
- URL da imagem

## Padrões de Código

### Convenções de Nomenclatura
- **Variáveis e funções**: snake_case
- **Classes**: PascalCase
- **Constantes**: UPPER_SNAKE_CASE
- **Endpoints**: kebab-case quando aplicável

### Estrutura de Response
```python
# Response de sucesso
{
    "success": true,
    "data": {...},
    "message": "Success message",
    "timestamp": "2025-08-09T10:30:00Z"
}

# Response de erro
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "Error description",
        "details": {...}
    },
    "timestamp": "2025-08-09T10:30:00Z"
}
```

### Tratamento de Erros
- Usar códigos HTTP apropriados (200, 201, 400, 401, 404, 500)
- Implementar middleware de tratamento global de erros
- Logs estruturados para todas as operações

## Implementações Específicas

### Web Scraping
- **Robustez**: Implementar retry logic e rate limiting
- **Headers**: User-Agent adequado para evitar bloqueios
- **Armazenamento**: Salvar dados em CSV com timestamp
- **Agendamento**: Considerar execução periódica

### Autenticação JWT
- **Rotas protegidas**: Todos os endpoints administrativos
- **Tempo de expiração**: Configurável via variável de ambiente
- **Refresh tokens**: Implementar rotação segura

### Performance
- **Paginação**: Implementar em endpoints de listagem
- **Cache**: Considerar cache para estatísticas
- **Índices**: Otimizar queries por categoria e preço

### Monitoramento
- **Logs estruturados**: JSON format com timestamp, level, message
- **Métricas**: Request count, response time, error rate
- **Dashboard**: Interface Streamlit para visualização

## Variáveis de Ambiente
```
API_HOST=localhost
API_PORT=8000
JWT_SECRET_KEY=your_secret_key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=sqlite:///./books.db
SCRAPING_USER_AGENT=Mozilla/5.0...
RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

## Testes
- **Unitários**: Para cada endpoint e função de scraping
- **Integração**: Testes end-to-end da API
- **Mock**: Simular responses do site para testes

## Deploy
- **Containerização**: Dockerfile para deploy
- **CI/CD**: GitHub Actions para testes e deploy automático
- **Environment**: Configuração específica para produção
- **Health checks**: Endpoints para monitoramento

## Documentação
- **README**: Instruções completas de instalação e uso
- **API Docs**: Swagger UI automático
- **Exemplos**: Requests/responses de exemplo para cada endpoint
- **Arquitetura**: Diagrama do pipeline de dados

## Considerações para ML
- **Feature Engineering**: Endpoints que retornem dados limpos e formatados
- **Training Data**: Formato adequado para modelos de ML
- **Predictions**: Interface para consumir modelos treinados
- **Data Pipeline**: Estrutura escalável para processamento

---

**Instruções Especiais para Copilot:**
1. Sempre seguir os padrões de response definidos
2. Implementar validação de dados em todos os endpoints
3. Priorizar código limpo e bem documentado
4. Considerar escalabilidade em todas as implementações
5. Focar em robustez para o sistema de scraping
6. Implementar logging detalhado para debugging
