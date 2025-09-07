# Facebook Scraper - Aplicação Desktop com Flet

## Visão Geral

Esta é uma versão desktop da aplicação de scraping do Facebook, desenvolvida com a biblioteca **Flet**. A aplicação oferece uma interface gráfica intuitiva e moderna para gerenciar tarefas de scraping, monitorar progresso em tempo real e exportar dados para Excel.

## Características Principais

### 🖥️ Interface Desktop Moderna
- Interface responsiva desenvolvida com Flet
- Design limpo e profissional
- Componentes interativos e intuitivos
- Suporte a temas claro e escuro

### 📊 Dashboard Completo
- Visão geral das tarefas de scraping
- Estatísticas em tempo real
- Cards informativos com métricas
- Lista de tarefas com status atualizado

### ⚙️ Gerenciamento de Tarefas
- Criação de novas tarefas com validação
- Configurações avançadas de scraping
- Monitoramento em tempo real do progresso
- Controle de execução (iniciar/parar)

### 📈 Monitoramento em Tempo Real
- Progresso visual das tarefas
- Logs detalhados de execução
- Estatísticas de dados extraídos
- Notificações de status

### 📋 Exportação para Excel
- Exportação completa dos dados
- Formatação automática das planilhas
- Agrupamento por tipo de dados
- Planilhas de resumo e estatísticas

## Estrutura do Projeto

```
flet_app/
├── __init__.py              # Configuração do módulo
├── main.py                  # Aplicação principal
├── models/                  # Modelos de dados
│   ├── __init__.py
│   ├── base.py             # Configuração base SQLAlchemy
│   ├── scraping_task.py    # Modelo de tarefas
│   └── facebook_data.py    # Modelo de dados extraídos
├── repositories/            # Camada de acesso a dados
│   ├── __init__.py
│   ├── scraping_task_repository.py
│   └── facebook_data_repository.py
├── services/               # Serviços de negócio
│   ├── __init__.py
│   ├── scraping_service.py # Serviço de scraping
│   └── excel_service.py    # Serviço de exportação
├── use_cases/              # Casos de uso
│   ├── __init__.py
│   ├── create_scraping_task.py
│   ├── execute_scraping.py
│   └── export_to_excel.py
└── views/                  # Interface gráfica
    ├── __init__.py
    ├── dashboard_view.py   # Dashboard principal
    ├── new_task_view.py    # Formulário de nova tarefa
    └── task_detail_view.py # Detalhes da tarefa
```

## Instalação e Configuração

### Pré-requisitos
- Python 3.8+
- Chrome/Chromium instalado
- ChromeDriver compatível

### Dependências
```bash
pip install flet
pip install selenium
pip install sqlalchemy
pip install openpyxl
pip install python-dotenv
```

### Configuração
1. Copie o arquivo `.env.example` para `.env`
2. Configure as variáveis de ambiente necessárias
3. Certifique-se de que o ChromeDriver está no PATH

### Execução
```bash
python -m flet_app.main
```

## Funcionalidades Detalhadas

### Dashboard Principal
- **Estatísticas Gerais**: Total de tarefas, dados extraídos, exportações
- **Lista de Tarefas**: Visualização de todas as tarefas com status
- **Ações Rápidas**: Criar nova tarefa, exportar dados
- **Atualização Automática**: Dados atualizados em tempo real

### Criação de Tarefas
- **Validação de URL**: Verificação automática de URLs do Facebook
- **Configurações Avançadas**: 
  - Número máximo de posts
  - Delay entre requisições
  - Extração de comentários
  - Extração de perfis
- **Validação em Tempo Real**: Feedback imediato sobre configurações

### Monitoramento de Execução
- **Progresso Visual**: Barra de progresso e percentual
- **Logs Detalhados**: Registro completo das ações
- **Dados Extraídos**: Visualização dos dados em tempo real
- **Controles**: Pausar, parar ou reiniciar tarefas

### Exportação para Excel
- **Múltiplos Formatos**: Planilhas organizadas por tipo
- **Formatação Automática**: Headers, cores e estilos
- **Estatísticas**: Planilha de resumo com métricas
- **Histórico**: Controle de exportações realizadas

## Arquitetura

### Padrões Utilizados
- **Clean Architecture**: Separação clara de responsabilidades
- **Repository Pattern**: Abstração da camada de dados
- **Use Cases**: Lógica de negócio isolada
- **Dependency Injection**: Baixo acoplamento entre componentes

### Threading e Assincronismo
- **Threading**: Operações de scraping em threads separadas
- **Callbacks**: Atualização da interface via callbacks
- **Queue**: Comunicação thread-safe entre componentes
- **Locks**: Sincronização de recursos compartilhados

### Banco de Dados
- **SQLite**: Banco local para persistência
- **SQLAlchemy**: ORM para mapeamento objeto-relacional
- **Migrations**: Controle de versão do schema
- **Transações**: Garantia de consistência dos dados

## Segurança e Boas Práticas

### Configurações Seguras
- Variáveis sensíveis em arquivo `.env`
- Validação rigorosa de entradas
- Sanitização de dados
- Tratamento de exceções

### Performance
- Lazy loading de dados
- Cache de consultas frequentes
- Otimização de queries SQL
- Gerenciamento eficiente de memória

### Logging
- Sistema de logs estruturado
- Diferentes níveis de log
- Rotação automática de arquivos
- Logs de auditoria

## Troubleshooting

### Problemas Comuns

1. **ChromeDriver não encontrado**
   - Instale o ChromeDriver compatível
   - Adicione ao PATH do sistema

2. **Erro de permissão no banco**
   - Verifique permissões da pasta
   - Execute como administrador se necessário

3. **Interface não carrega**
   - Verifique se todas as dependências estão instaladas
   - Consulte os logs para erros específicos

4. **Scraping falha**
   - Verifique conectividade com a internet
   - Confirme se a URL é válida
   - Ajuste delays se necessário

### Logs e Debugging
- Logs são salvos em `logs/app.log`
- Configure nível de log em `.env`
- Use modo debug para informações detalhadas

## Contribuição

### Estrutura de Desenvolvimento
1. Fork do repositório
2. Criar branch para feature
3. Implementar mudanças
4. Testes unitários
5. Pull request

### Padrões de Código
- PEP 8 para Python
- Docstrings em português
- Type hints obrigatórios
- Testes para novas funcionalidades

## Licença

Este projeto está sob licença MIT. Consulte o arquivo LICENSE para mais detalhes.

## Suporte

Para suporte técnico ou dúvidas:
- Abra uma issue no GitHub
- Consulte a documentação técnica
- Verifique os logs de erro

---

**Desenvolvido com ❤️ usando Flet e Python**