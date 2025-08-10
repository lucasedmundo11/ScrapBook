Entregáveis Obrigatórios

1. Repositório do GitHub Organizado
• Código estruturado em módulos (scripts/, api/, data/, etc.).
• README completo contendo:
o Descrição do projeto e arquitetura.
o Instruções de instalação e configuração.
o Documentação das rotas da API.
o Exemplos de chamadas com requests/responses.
o Instruções para execução.

2. Sistema de Web Scraping
• Script automatizado para extrair dados de https://books.toscrape.com/
• Dados armazenados localmente em um arquivo CSV.
• Script executável e bem documentado.

3. API RESTful Funcional
• API implementada em Flask ou FastAPI.
• Endpoints obrigatórios (listados a seguir).
• Documentação da API (Swagger).

4. Deploy Público
• API deployada em Heroku, Render, Vercel, Fly.io ou similar.
• Link compartilhável funcional.
• API totalmente operacional no ambiente de produção.

5. Plano Arquitetural
• Diagrama ou documento detalhando:
o Pipeline desde ingestão → processamento → API → consumo.
o Arquitetura pensada para escalabilidade futura.
o Cenário de uso para cientistas de dados/ML.
o Plano de integração com modelos de ML.

Objetivos Técnicos Core
Web Scraping Robusto
• Extrair todos os livros disponíveis no site.
• Capturar: título, preço, rating, disponibilidade, categoria, imagem.
Endpoints Obrigatórios da API
Endpoints Core
• GET /api/v1/books: Lista todos os livros disponíveis na base de dados.
• GET /api/v1/books/{id}: Retorna detalhes completos de um livro
específico pelo ID.
• GET /api/v1/books/search?title={title}&category={category}: Busca
livros por título e/ou categoria.
• GET /api/v1/categories: Lista todas as categorias de livros disponíveis.
• GET /api/v1/health: Verifica status da API e conectividade com os
dados.
Endpoints de Insights
• GET /api/v1/stats/overview: Estatísticas gerais da coleção (total de
livros, preço médio, distribuição de ratings).
• GET /api/v1/stats/categories: Estatísticas detalhadas por categoria
(quantidade de livros, preços por categoria).
• GET /api/v1/books/top-rated: Lista os livros com melhor avaliação
(rating mais alto).
• GET /api/v1/books/price-range?min={min}&max={max}: Filtra livros dentro de uma faixa de preço específica.

Implementar JWT Authentication para proteger rotas sensíveis:
• POST /api/v1/auth/login - Obter token.
• POST /api/v1/auth/refresh - Renovar token.
• Proteger endpoints de admin como /api/v1/scraping/trigger.

Criar endpoints pensados para consumo de modelos ML:
• GET /api/v1/ml/features - Dados formatados para features.
• GET /api/v1/ml/training-data - Dataset para treinamento.
• POST /api/v1/ml/predictions - Endpoint para receber predições.

Monitoramento & Analytics
• Logs estruturados de todas as chamadas.
• Métricas de performance da API.
• Dashboard simples de uso (Streamlit).