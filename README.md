# Facebook Web Scraper

Aplicação completa de web scraping do Facebook desenvolvida com Flask seguindo os princípios da Clean Architecture.

## 🚀 Características

- **Clean Architecture**: Estrutura modular e bem organizada
- **Interface Web**: Dashboard intuitivo com Bootstrap
- **Scraping Inteligente**: Extração de posts, comentários e dados de perfil
- **Exportação Excel**: Relatórios detalhados com gráficos
- **Sistema de Logs**: Monitoramento completo das operações
- **Banco SQLite**: Armazenamento local eficiente
- **Testes Automatizados**: Cobertura de testes com pytest

## 📋 Pré-requisitos

- Python 3.8+
- pip (gerenciador de pacotes Python)
- Google Chrome (para Selenium WebDriver)

## 🛠️ Instalação

### 1. Clone o repositório
```bash
git clone <url-do-repositorio>
cd web-scraping-facebook
```

### 2. Crie um ambiente virtual
```bash
python -m venv venv

# No Windows
venv\Scripts\activate

# No macOS/Linux
source venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente
```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas configurações:
```env
FLASK_ENV=development
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
SECRET_KEY=sua-chave-secreta-aqui
DATABASE_URL=sqlite:///data/facebook_scraper.db
LOG_LEVEL=INFO
```

### 5. Inicialize o banco de dados
```bash
python -c "from app import create_app; from app.config.database import setup_database; app = create_app(); setup_database(app); app.app_context().push(); setup_database(app).create_tables()"
```

## 🚀 Execução

### Executar a aplicação
```bash
python run.py
```

A aplicação estará disponível em: http://127.0.0.1:5000

### Executar testes
```bash
# Instalar dependências de teste
pip install pytest pytest-cov

# Executar todos os testes
pytest tests/ -v

# Executar com cobertura
pytest tests/ --cov=app --cov-report=html
```

## 📁 Estrutura do Projeto

```
web-scraping-facebook/
├── app/
│   ├── __init__.py              # Factory da aplicação Flask
│   ├── config/
│   │   ├── database.py          # Configuração do banco SQLite
│   │   └── logging_config.py    # Sistema de logs
│   ├── models/                  # Modelos de dados (Entities)
│   │   ├── scraping_task.py     # Modelo de tarefas
│   │   ├── facebook_data.py     # Modelo de dados extraídos
│   │   └── export_job.py        # Modelo de jobs de exportação
│   ├── repositories/            # Camada de acesso a dados
│   │   ├── scraping_task_repository.py
│   │   ├── facebook_data_repository.py
│   │   └── export_job_repository.py
│   ├── use_cases/              # Casos de uso (Business Logic)
│   │   ├── create_scraping_task.py
│   │   ├── execute_scraping.py
│   │   └── export_to_excel.py
│   ├── services/               # Serviços externos
│   │   ├── scraping_service.py  # Selenium WebDriver
│   │   └── excel_service.py     # Geração de Excel
│   ├── controllers/            # Controllers Flask
│   │   ├── dashboard_controller.py
│   │   ├── scraping_controller.py
│   │   └── export_controller.py
│   └── templates/              # Templates HTML
│       ├── base.html
│       ├── dashboard/
│       ├── scraping/
│       └── export/
├── tests/                      # Testes automatizados
├── data/                       # Banco de dados SQLite
├── logs/                       # Arquivos de log
├── requirements.txt            # Dependências Python
├── .env.example               # Exemplo de variáveis de ambiente
├── run.py                     # Arquivo principal
└── README.md                  # Este arquivo
```

## 🎯 Como Usar

### 1. Criar Nova Tarefa
1. Acesse o dashboard principal
2. Clique em "Nova Tarefa"
3. Preencha:
   - Nome da tarefa
   - URL do Facebook (página ou perfil público)
   - Configurações de scraping
4. Clique em "Salvar e Executar"

### 2. Monitorar Execução
- Acompanhe o progresso em tempo real
- Visualize logs detalhados
- Pare a execução se necessário

### 3. Exportar Dados
1. Selecione tarefas concluídas
2. Escolha tipos de dados para exportar
3. Configure opções de formatação
4. Gere arquivo Excel com relatórios

## 📊 Tipos de Dados Extraídos

- **Posts**: Conteúdo, autor, data, curtidas, compartilhamentos
- **Comentários**: Texto, autor, data, curtidas
- **Perfil**: Informações básicas, seguidores, posts recentes
- **Mídia**: URLs de imagens e vídeos
- **Engajamento**: Métricas de interação

## 🔧 Configurações Avançadas

### Selenium WebDriver
- Suporte a modo headless
- Configuração de timeouts
- User agents personalizados
- Delays inteligentes

### Sistema de Logs
- Logs separados por módulo
- Rotação automática de arquivos
- Níveis configuráveis (DEBUG, INFO, WARNING, ERROR)
- Logs estruturados para análise

### Banco de Dados
- SQLite com otimizações de performance
- Backup automático
- Limpeza de dados antigos
- Índices para consultas rápidas

## 🧪 Testes

O projeto inclui testes abrangentes:

- **Testes de Modelos**: Validação de entidades e relacionamentos
- **Testes de Use Cases**: Lógica de negócio
- **Testes de Repositórios**: Acesso a dados
- **Testes de Controllers**: Endpoints da API
- **Testes de Integração**: Fluxos completos

## 📝 Comandos CLI

```bash
# Inicializar banco
flask init-db

# Resetar banco (CUIDADO!)
flask reset-db

# Criar backup
flask backup-db

# Otimizar banco
flask optimize-db

# Informações do banco
flask db-info
```

## ⚠️ Considerações Importantes

### Termos de Uso
- Respeite os termos de serviço do Facebook
- Use apenas em páginas e perfis públicos
- Implemente delays adequados entre requisições
- Monitore para evitar bloqueios

### Performance
- Configure delays apropriados (2-5 segundos)
- Limite o número de posts por execução
- Use modo headless em produção
- Monitore uso de memória

### Segurança
- Mantenha credenciais em variáveis de ambiente
- Use HTTPS em produção
- Implemente rate limiting
- Monitore logs de segurança

## 🐛 Solução de Problemas

### Erro de WebDriver
```bash
# Instalar ChromeDriver
# macOS
brew install chromedriver

# Ubuntu
sudo apt-get install chromium-chromedriver

# Windows
# Baixar de: https://chromedriver.chromium.org/
```

### Erro de Permissões SQLite
```bash
# Verificar permissões do diretório data/
chmod 755 data/
chmod 644 data/*.db
```

### Erro de Dependências
```bash
# Reinstalar dependências
pip install --upgrade -r requirements.txt
```

## 📈 Melhorias Futuras

- [ ] Suporte a múltiplas redes sociais
- [ ] API REST completa
- [ ] Dashboard em tempo real com WebSockets
- [ ] Análise de sentimentos
- [ ] Detecção de spam/bot
- [ ] Exportação para outros formatos (CSV, JSON, PDF)
- [ ] Agendamento de tarefas
- [ ] Notificações por email
- [ ] Interface mobile responsiva
- [ ] Containerização com Docker

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👥 Autores

- **Rogério Assunção** - *Desenvolvimento inicial* - [SeuGitHub](https://github.com/devjogerio)

## 🙏 Agradecimentos

- Flask e SQLAlchemy pela base sólida
- Selenium pela automação web
- Bootstrap pela interface responsiva
- Pytest pela estrutura de testes
- Comunidade Python pelo suporte

---

**⚠️ Aviso Legal**: Esta ferramenta é destinada apenas para fins educacionais e de pesquisa. O uso deve estar em conformidade com os termos de serviço das plataformas e leis aplicáveis.