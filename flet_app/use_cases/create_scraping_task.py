"""Use case para criar tarefas de scraping - Versão Flet.

Este módulo implementa a lógica de negócio para criação
de novas tarefas de scraping do Facebook na aplicação desktop.
"""

import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from flet_app.models.scraping_task import ScrapingTask
from flet_app.repositories.scraping_task_repository import ScrapingTaskRepository
from flet_app.config.logging_config import get_logger


class CreateScrapingTaskUseCase:
    """Use case para criar tarefas de scraping.
    
    Implementa a lógica de negócio para validação e criação
    de novas tarefas de scraping do Facebook.
    """
    
    def __init__(self, task_repository: ScrapingTaskRepository):
        """Inicializar use case.
        
        Args:
            task_repository: Repositório de tarefas de scraping
        """
        self.task_repository = task_repository
        self.logger = get_logger('CreateScrapingTaskUseCase')
    
    def execute(self, name: str, url: str, config: Optional[Dict[str, Any]] = None) -> ScrapingTask:
        """Executar criação de tarefa de scraping.
        
        Args:
            name: Nome da tarefa
            url: URL do Facebook para scraping
            config: Configurações específicas da tarefa
            
        Returns:
            Tarefa de scraping criada
            
        Raises:
            ValueError: Se os dados de entrada são inválidos
        """
        try:
            self.logger.info(f'Iniciando criação de tarefa: {name}')
            
            # Validar dados de entrada
            self._validate_input(name, url, config)
            
            # Normalizar URL
            normalized_url = self._normalize_url(url)
            
            # Aplicar configurações padrão
            final_config = self._apply_default_config(config)
            
            # Criar tarefa
            task = ScrapingTask(
                name=name.strip(),
                url=normalized_url,
                config=final_config
            )
            
            # Salvar no repositório
            created_task = self.task_repository.create(task)
            
            self.logger.info(f'Tarefa criada com sucesso: {created_task.id}')
            return created_task
            
        except Exception as e:
            self.logger.error(f'Erro ao criar tarefa: {str(e)}')
            raise
    
    def _validate_input(self, name: str, url: str, config: Optional[Dict[str, Any]]) -> None:
        """Validar dados de entrada.
        
        Args:
            name: Nome da tarefa
            url: URL do Facebook
            config: Configurações da tarefa
            
        Raises:
            ValueError: Se algum dado é inválido
        """
        # Validar nome
        if not name or not name.strip():
            raise ValueError("Nome da tarefa é obrigatório")
        
        if len(name.strip()) < 3:
            raise ValueError("Nome da tarefa deve ter pelo menos 3 caracteres")
        
        if len(name.strip()) > 255:
            raise ValueError("Nome da tarefa deve ter no máximo 255 caracteres")
        
        # Validar URL
        if not url or not url.strip():
            raise ValueError("URL é obrigatória")
        
        if not self._is_valid_facebook_url(url):
            raise ValueError("URL deve ser uma URL válida do Facebook")
        
        # Validar configurações
        if config:
            self._validate_config(config)
    
    def _is_valid_facebook_url(self, url: str) -> bool:
        """Validar se é uma URL válida do Facebook.
        
        Args:
            url: URL a ser validada
            
        Returns:
            True se é uma URL válida do Facebook
        """
        try:
            parsed = urlparse(url)
            
            # Verificar se tem esquema
            if not parsed.scheme:
                return False
            
            # Verificar se é HTTPS
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Verificar domínio do Facebook
            facebook_domains = [
                'facebook.com',
                'www.facebook.com',
                'm.facebook.com',
                'mobile.facebook.com'
            ]
            
            if parsed.netloc.lower() not in facebook_domains:
                return False
            
            # Verificar se tem path
            if not parsed.path or parsed.path == '/':
                return False
            
            return True
            
        except Exception:
            return False
    
    def _normalize_url(self, url: str) -> str:
        """Normalizar URL do Facebook.
        
        Args:
            url: URL original
            
        Returns:
            URL normalizada
        """
        url = url.strip()
        
        # Adicionar https se não tiver esquema
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Converter para HTTPS
        url = url.replace('http://', 'https://')
        
        # Normalizar domínio
        url = re.sub(r'(m\.|mobile\.)facebook\.com', 'www.facebook.com', url)
        
        # Remover parâmetros desnecessários
        parsed = urlparse(url)
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        # Remover barra final se existir
        if clean_url.endswith('/') and len(parsed.path) > 1:
            clean_url = clean_url[:-1]
        
        return clean_url
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validar configurações da tarefa.
        
        Args:
            config: Configurações a serem validadas
            
        Raises:
            ValueError: Se alguma configuração é inválida
        """
        # Validar tipos de dados
        if 'data_types' in config:
            valid_types = ['post', 'comment', 'profile', 'like', 'share']
            data_types = config['data_types']
            
            if not isinstance(data_types, list):
                raise ValueError("data_types deve ser uma lista")
            
            if not data_types:
                raise ValueError("Pelo menos um tipo de dado deve ser selecionado")
            
            for data_type in data_types:
                if data_type not in valid_types:
                    raise ValueError(f"Tipo de dado inválido: {data_type}")
        
        # Validar limite máximo de itens
        if 'max_items' in config:
            max_items = config['max_items']
            
            if not isinstance(max_items, int) or max_items <= 0:
                raise ValueError("max_items deve ser um número inteiro positivo")
            
            if max_items > 10000:
                raise ValueError("max_items não pode ser maior que 10.000")
        
        # Validar delay entre requisições
        if 'delay_min' in config:
            delay_min = config['delay_min']
            
            if not isinstance(delay_min, (int, float)) or delay_min < 0:
                raise ValueError("delay_min deve ser um número não negativo")
        
        if 'delay_max' in config:
            delay_max = config['delay_max']
            
            if not isinstance(delay_max, (int, float)) or delay_max < 0:
                raise ValueError("delay_max deve ser um número não negativo")
            
            if 'delay_min' in config and delay_max < config['delay_min']:
                raise ValueError("delay_max deve ser maior ou igual a delay_min")
        
        # Validar filtro de data
        if 'date_filter' in config and config['date_filter']:
            date_filter = config['date_filter']
            
            if not isinstance(date_filter, dict):
                raise ValueError("date_filter deve ser um objeto")
            
            # Validar campos de data
            for field in ['start_date', 'end_date']:
                if field in date_filter:
                    date_value = date_filter[field]
                    if not isinstance(date_value, str):
                        raise ValueError(f"{field} deve ser uma string")
                    
                    # Validar formato de data (YYYY-MM-DD)
                    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_value):
                        raise ValueError(f"{field} deve estar no formato YYYY-MM-DD")
    
    def _apply_default_config(self, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Aplicar configurações padrão.
        
        Args:
            config: Configurações fornecidas pelo usuário
            
        Returns:
            Configurações com valores padrão aplicados
        """
        default_config = {
            'data_types': ['post', 'comment'],
            'max_items': 100,
            'delay_min': 1,
            'delay_max': 3,
            'max_retries': 3,
            'timeout': 30,
            'headless': True,
            'date_filter': None,
            'include_reactions': True,
            'include_shares': True,
            'extract_links': False,
            'extract_images': False
        }
        
        if config:
            # Mesclar configurações fornecidas com padrões
            final_config = default_config.copy()
            final_config.update(config)
            return final_config
        
        return default_config
    
    def validate_task_name_uniqueness(self, name: str) -> bool:
        """Validar se o nome da tarefa é único.
        
        Args:
            name: Nome da tarefa a ser validado
            
        Returns:
            True se o nome é único
        """
        try:
            existing_tasks = self.task_repository.search_by_name(name.strip())
            is_unique = len(existing_tasks) == 0
            
            if not is_unique:
                self.logger.warning(f'Nome de tarefa já existe: {name}')
            
            return is_unique
        except Exception as e:
            self.logger.error(f'Erro ao validar unicidade do nome: {str(e)}')
            return True  # Em caso de erro, permitir criação
    
    def get_suggested_name(self, url: str) -> str:
        """Gerar nome sugerido baseado na URL.
        
        Args:
            url: URL do Facebook
            
        Returns:
            Nome sugerido para a tarefa
        """
        try:
            parsed = urlparse(url)
            path_parts = [part for part in parsed.path.split('/') if part]
            
            if path_parts:
                # Usar primeira parte do path como base
                base_name = path_parts[0]
                
                # Limpar caracteres especiais
                clean_name = re.sub(r'[^a-zA-Z0-9\s-]', '', base_name)
                clean_name = re.sub(r'\s+', ' ', clean_name).strip()
                
                if clean_name:
                    suggested_name = f"Scraping - {clean_name.title()}"
                    
                    # Verificar se o nome já existe e adicionar número se necessário
                    counter = 1
                    original_name = suggested_name
                    
                    while not self.validate_task_name_uniqueness(suggested_name):
                        counter += 1
                        suggested_name = f"{original_name} ({counter})"
                    
                    return suggested_name
            
            return "Nova Tarefa de Scraping"
            
        except Exception as e:
            self.logger.error(f'Erro ao gerar nome sugerido: {str(e)}')
            return "Nova Tarefa de Scraping"
    
    def get_config_template(self) -> Dict[str, Any]:
        """Obter template de configuração padrão.
        
        Returns:
            Dicionário com configuração template
        """
        return {
            'data_types': ['post', 'comment'],
            'max_items': 100,
            'delay_min': 1,
            'delay_max': 3,
            'headless': True,
            'include_reactions': True,
            'include_shares': True,
            'extract_links': False,
            'extract_images': False
        }
    
    def validate_url_accessibility(self, url: str) -> tuple[bool, str]:
        """Validar se a URL é acessível.
        
        Args:
            url: URL a ser validada
            
        Returns:
            Tupla (é_acessível, mensagem)
        """
        try:
            import requests
            
            # Fazer requisição HEAD para verificar acessibilidade
            response = requests.head(url, timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                return True, "URL acessível"
            elif response.status_code == 403:
                return False, "Acesso negado - página pode estar privada"
            elif response.status_code == 404:
                return False, "Página não encontrada"
            else:
                return False, f"Erro HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "Timeout - página demorou muito para responder"
        except requests.exceptions.ConnectionError:
            return False, "Erro de conexão - verifique sua internet"
        except Exception as e:
            return False, f"Erro ao verificar URL: {str(e)}"