# Facebook Scraper - Aplicação Desktop com Flet

## 📋 Descrição

Aplicação desktop moderna desenvolvida com Flet para extração automatizada de dados públicos do Facebook e exportação para planilhas Excel. A ferramenta oferece uma interface intuitiva e responsiva para automatizar tarefas de coleta de dados, operando dentro dos termos de serviço do Facebook e leis de privacidade aplicáveis.

## 🎯 Funcionalidades Principais

- **Dashboard Interativo**: Painel principal com estatísticas em tempo real e lista de tarefas
- **Criação de Tarefas**: Formulário intuitivo com validação em tempo real
- **Monitoramento**: Acompanhamento do progresso de execução em tempo real
- **Exportação Excel**: Geração automática de planilhas formatadas
- **Logs Detalhados**: Visualização completa de logs de execução
- **Interface Responsiva**: Design moderno com Material Design 3

## 🔧 Requisitos do Sistema

### Software Necessário
- **Python 3.11+** (recomendado)
- **Google Chrome** (versão mais recente)
- **ChromeDriver** (compatível com a versão do Chrome)

### Sistemas Operacionais Suportados
- macOS 10.14+
- Windows 10+
- Linux (Ubuntu 18.04+, CentOS 7+)

## 🚀 Instalação

### 1. Clone o Repositório
```bash
git clone <url-do-repositorio>
cd web-scraping-facebook
```

### 2. Crie um Ambiente Virtual
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Instale as Dependências
```bash
pip install -r requirements-flet.txt
```

### 4. Instale o ChromeDriver

#### macOS (usando Homebrew)
```bash
brew install chromedriver
```

#### Windows
1. Baixe o ChromeDriver de https://chromedriver.chromium.org/
2. Extraia o arquivo `chromedriver.exe`
3. Adicione o diretório ao PATH do sistema

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install chromium-chromedriver
```

### 5. Configure as Variáveis de Ambiente
```bash
cp .env.example .env
# Edite o arquivo .env conforme necessário
```

## ▶️ Como Executar

### Executar a Aplicação Desktop
```bash
python -m flet_app.main
```

### Executar em Modo Debug
```bash
FLET_DEBUG=1 python -m flet_app.main
```

### Executar como Aplicação Web (opcional)
```bash
flet run flet_app/main.py --web
```

## 📱 Como Usar

### 1. Dashboard Principal
- Visualize estatísticas gerais do sistema
- Acesse a lista de todas as tarefas criadas
- Monitore tarefas em execução

### 2. Criar Nova Tarefa
1. Clique em "Nova Tarefa" no dashboard
2. Preencha o nome da tarefa
3. Insira a URL do Facebook (será validada automaticamente)
4. Selecione os tipos de dados desejados:
   - Posts
   - Comentários
   - Informações de Perfil
   - Curtidas (limitado)
   - Compartilhamentos (limitado)
5. Configure o limite máximo de itens
6. Clique em "Criar Tarefa"

### 3. Monitorar Execução
- Acesse os detalhes da tarefa para ver o progresso
- Acompanhe logs em tempo real
- Pare a execução se necessário

### 4. Exportar Dados
- Após a conclusão, clique em "Exportar para Excel"
- O arquivo será salvo na pasta `exports/`
- Baixe o arquivo gerado

## 📁 Estrutura do Projeto

```
flet_app/
├── __init__.py              # Inicialização do módulo
├── main.py                  # Aplicação principal
├── config/                  # Configurações
│   ├── database.py         # Configuração do banco
│   └── logging_config.py   # Configuração de logs
├── models/                  # Modelos de dados
│   ├── scraping_task.py    # Modelo de tarefas
│   ├── facebook_data.py    # Modelo de dados extraídos
│   └── export_job.py       # Modelo de jobs de exportação
├── repositories/            # Camada de acesso a dados
│   ├── base_repository.py  # Repositório base
│   └── ...
├── services/               # Serviços de negócio
│   ├── scraping_service.py # Serviço de scraping
│   └── excel_service.py    # Serviço de exportação
├── use_cases/              # Casos de uso
│   ├── create_scraping_task.py
│   ├── execute_scraping.py
│   └── export_to_excel.py
└── views/                  # Interfaces de usuário
    ├── dashboard_view.py   # Dashboard principal
    ├── new_task_view.py    # Formulário de nova tarefa
    └── task_detail_view.py # Detalhes da tarefa
```

## 🔧 Configuração Avançada

### Variáveis de Ambiente (.env)
```env
# Configurações do Banco de Dados
DATABASE_URL=sqlite:///facebook_scraper.db

# Configurações de Scraping
SCRAPING_DELAY_MIN=1
SCRAPING_DELAY_MAX=3
SCRAPING_TIMEOUT=30
SCRAPING_MAX_RETRIES=3
SCRAPING_HEADLESS=true

# Configurações de Logs
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Configurações de Exportação
EXPORT_DIR=exports
EXPORT_MAX_ROWS=10000

# Configurações da Interface
FLET_DEBUG=false
FLET_PORT=8080
```

## 🐛 Troubleshooting

### Problemas Comuns

#### 1. ChromeDriver não encontrado
**Erro**: `selenium.common.exceptions.WebDriverException: 'chromedriver' executable needs to be in PATH`

**Solução**:
- Verifique se o ChromeDriver está instalado
- Adicione o ChromeDriver ao PATH do sistema
- No macOS: `brew install chromedriver`

#### 2. Erro de permissão no ChromeDriver (macOS)
**Erro**: `"chromedriver" cannot be opened because the developer cannot be verified`

**Solução**:
```bash
xattr -d com.apple.quarantine /usr/local/bin/chromedriver
```

#### 3. Aplicação não abre
**Possíveis causas**:
- Porta já em uso
- Dependências não instaladas corretamente
- Problemas de permissão

**Soluções**:
```bash
# Verificar dependências
pip list | grep flet

# Executar em modo debug
FLET_DEBUG=1 python -m flet_app.main

# Verificar logs
tail -f logs/app.log
```

#### 4. Erro de banco de dados
**Erro**: `sqlite3.OperationalError: no such table`

**Solução**:
```bash
# Remover banco existente e recriar
rm facebook_scraper.db
python -m flet_app.main
```

#### 5. Scraping não funciona
**Possíveis causas**:
- URL inválida do Facebook
- Mudanças na estrutura do Facebook
- Rate limiting
- Problemas de conectividade

**Soluções**:
- Verificar se a URL é válida e pública
- Aumentar delays entre requisições
- Verificar logs para erros específicos

### Logs e Debug

#### Localização dos Logs
- **Arquivo**: `logs/app.log`
- **Console**: Durante execução em modo debug

#### Níveis de Log
- `DEBUG`: Informações detalhadas para desenvolvimento
- `INFO`: Informações gerais de funcionamento
- `WARNING`: Avisos que não impedem a execução
- `ERROR`: Erros que podem afetar a funcionalidade
- `CRITICAL`: Erros críticos que impedem a execução

## 🔒 Considerações de Segurança

- **Respeite os Termos de Serviço**: Use apenas em páginas públicas
- **Rate Limiting**: A aplicação implementa delays automáticos
- **Dados Sensíveis**: Nunca extraia informações privadas
- **Uso Ético**: Use apenas para fins legítimos e educacionais

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Para suporte técnico ou dúvidas:
- Abra uma issue no GitHub
- Consulte a documentação técnica
- Verifique os logs da aplicação

---

**Nota**: Esta aplicação é destinada apenas para uso educacional e extração de dados públicos. Sempre respeite os termos de serviço das plataformas e as leis de privacidade aplicáveis.