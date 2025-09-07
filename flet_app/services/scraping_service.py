"""Serviço de scraping do Facebook - Versão Flet.

Este módulo implementa a lógica de extração de dados do Facebook
utilizando Selenium e BeautifulSoup de forma responsável para aplicação desktop.
"""

import time
import random
import threading
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from urllib.parse import urljoin, urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import requests

from flet_app.config.logging_config import get_logger
from flet_app.models.facebook_data import FacebookData


class ScrapingService:
    """Serviço para extração de dados do Facebook.
    
    Implementa métodos para extrair diferentes tipos de dados
    do Facebook de forma ética e respeitando rate limits.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Inicializar serviço de scraping.
        
        Args:
            config: Configurações do scraping
        """
        self.config = config
        self.logger = get_logger('ScrapingService')
        self.driver = None
        self.active_tasks = set()
        self.stop_flags = {}
        
        # Configurações padrão
        self.delay_min = config.get('delay_min', 1)
        self.delay_max = config.get('delay_max', 3)
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        self.headless = config.get('headless', True)
        self.user_agent = config.get('user_agent', 
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Configurar driver do Selenium.
        
        Returns:
            Driver configurado
        """
        options = Options()
        
        if self.headless:
            options.add_argument('--headless')
        
        # Configurações de segurança e performance
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')
        options.add_argument(f'--user-agent={self.user_agent}')
        options.add_argument('--window-size=1920,1080')
        
        # Configurações de privacidade
        options.add_argument('--incognito')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=VizDisplayCompositor')
        
        try:
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(self.timeout)
            return driver
        except Exception as e:
            self.logger.error(f'Erro ao configurar driver: {str(e)}')
            raise
    
    def _random_delay(self) -> None:
        """Aplicar delay aleatório entre requisições."""
        delay = random.uniform(self.delay_min, self.delay_max)
        time.sleep(delay)
    
    def _safe_get_text(self, element, default: str = '') -> str:
        """Extrair texto de elemento de forma segura.
        
        Args:
            element: Elemento BeautifulSoup ou Selenium
            default: Valor padrão se não encontrar texto
            
        Returns:
            Texto extraído ou valor padrão
        """
        try:
            if hasattr(element, 'get_text'):
                return element.get_text(strip=True)
            elif hasattr(element, 'text'):
                return element.text.strip()
            else:
                return str(element).strip()
        except Exception:
            return default
    
    def _extract_metadata_from_post(self, post_element) -> Dict[str, Any]:
        """Extrair metadados de um post.
        
        Args:
            post_element: Elemento do post
            
        Returns:
            Dicionário com metadados
        """
        metadata = {
            'author': '',
            'timestamp': '',
            'likes_count': 0,
            'comments_count': 0,
            'shares_count': 0,
            'reactions': {},
            'links': [],
            'images': []
        }
        
        try:
            # Extrair autor
            author_elem = post_element.find('strong') or post_element.find('[data-testid="post_author"]')
            if author_elem:
                metadata['author'] = self._safe_get_text(author_elem)
            
            # Extrair timestamp
            time_elem = post_element.find('time') or post_element.find('[data-testid="story-subtitle"]')
            if time_elem:
                metadata['timestamp'] = self._safe_get_text(time_elem)
            
            # Extrair contadores (implementação simplificada)
            like_elem = post_element.find('[aria-label*="curtida"]') or post_element.find('[aria-label*="like"]')
            if like_elem:
                like_text = self._safe_get_text(like_elem)
                metadata['likes_count'] = self._extract_number_from_text(like_text)
            
            # Extrair links
            links = post_element.find_all('a', href=True)
            metadata['links'] = [link['href'] for link in links if link['href'].startswith('http')]
            
            # Extrair imagens
            images = post_element.find_all('img', src=True)
            metadata['images'] = [img['src'] for img in images if img['src'].startswith('http')]
            
        except Exception as e:
            self.logger.warning(f'Erro ao extrair metadados: {str(e)}')
        
        return metadata
    
    def _extract_number_from_text(self, text: str) -> int:
        """Extrair número de um texto.
        
        Args:
            text: Texto contendo número
            
        Returns:
            Número extraído ou 0
        """
        import re
        
        # Procurar por números no texto
        numbers = re.findall(r'\d+', text.replace('.', '').replace(',', ''))
        if numbers:
            return int(numbers[0])
        return 0
    
    def extract_data_async(self, task_id: str, url: str, config: Dict[str, Any], 
                          progress_callback: Optional[Callable[[int, str], None]] = None,
                          data_callback: Optional[Callable[[FacebookData], None]] = None) -> List[FacebookData]:
        """Extrair dados de forma assíncrona.
        
        Args:
            task_id: ID da tarefa
            url: URL para scraping
            config: Configurações específicas
            progress_callback: Callback para atualizar progresso
            data_callback: Callback para processar dados extraídos
            
        Returns:
            Lista de dados extraídos
        """
        self.active_tasks.add(task_id)
        self.stop_flags[task_id] = False
        
        all_data = []
        
        try:
            data_types = config.get('data_types', ['post', 'comment'])
            max_items = config.get('max_items', 100)
            
            total_progress = 0
            progress_per_type = 100 // len(data_types)
            
            for i, data_type in enumerate(data_types):
                if self.stop_flags.get(task_id, False):
                    break
                
                if progress_callback:
                    progress_callback(total_progress, f'Extraindo {data_type}s...')
                
                # Extrair dados por tipo
                if data_type == 'post':
                    data = self._extract_posts(task_id, url, max_items // len(data_types), config)
                elif data_type == 'comment':
                    data = self._extract_comments(task_id, url, max_items // len(data_types), config)
                elif data_type == 'profile':
                    data = self._extract_profile_info(task_id, url, config)
                else:
                    data = []
                
                # Processar dados extraídos
                for item in data:
                    if self.stop_flags.get(task_id, False):
                        break
                    
                    fb_data = FacebookData(
                        task_id=task_id,
                        data_type=data_type,
                        content=item.get('content', ''),
                        metadata=item,
                        source_url=url
                    )
                    
                    all_data.append(fb_data)
                    
                    if data_callback:
                        data_callback(fb_data)
                
                total_progress += progress_per_type
                if progress_callback:
                    progress_callback(total_progress, f'{data_type.title()}s extraídos: {len(data)}')
            
            if progress_callback and not self.stop_flags.get(task_id, False):
                progress_callback(100, f'Concluído! {len(all_data)} itens extraídos.')
            
        except Exception as e:
            self.logger.error(f'Erro durante extração da tarefa {task_id}: {str(e)}')
            if progress_callback:
                progress_callback(0, f'Erro: {str(e)}')
        
        finally:
            self.active_tasks.discard(task_id)
            self.stop_flags.pop(task_id, None)
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass
                self.driver = None
        
        return all_data
    
    def _extract_posts(self, task_id: str, url: str, limit: int, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrair posts de uma página do Facebook.
        
        Args:
            task_id: ID da tarefa
            url: URL da página
            limit: Limite de posts
            config: Configurações específicas
            
        Returns:
            Lista de posts extraídos
        """
        posts = []
        
        try:
            if not self.driver:
                self.driver = self._setup_driver()
            
            self.logger.info(f'Extraindo posts de: {url}')
            
            # Navegar para a página
            self.driver.get(url)
            self._random_delay()
            
            # Aguardar carregamento
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Simular scroll para carregar mais posts
            self._scroll_to_load_content(limit, task_id)
            
            # Obter HTML da página
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Encontrar posts (seletores podem variar)
            post_selectors = [
                '[data-testid="post"]',
                '[role="article"]',
                '.userContentWrapper',
                '._5pcr'
            ]
            
            post_elements = []
            for selector in post_selectors:
                elements = soup.select(selector)
                if elements:
                    post_elements = elements
                    break
            
            # Extrair dados dos posts
            for i, post_elem in enumerate(post_elements[:limit]):
                if self.stop_flags.get(task_id, False):
                    break
                
                try:
                    content = self._safe_get_text(post_elem)
                    
                    if content and len(content.strip()) > 10:  # Filtrar posts muito pequenos
                        metadata = self._extract_metadata_from_post(post_elem)
                        
                        posts.append({
                            'content': content,
                            'source_url': url,
                            'author': metadata['author'],
                            'timestamp': metadata['timestamp'],
                            'likes_count': metadata['likes_count'],
                            'comments_count': metadata['comments_count'],
                            'shares_count': metadata['shares_count'],
                            'reactions': metadata['reactions'],
                            'links': metadata['links'],
                            'images': metadata['images']
                        })
                        
                        self.logger.debug(f'Post {i+1} extraído: {content[:100]}...')
                    
                except Exception as e:
                    self.logger.warning(f'Erro ao processar post {i+1}: {str(e)}')
                    continue
            
        except Exception as e:
            self.logger.error(f'Erro ao extrair posts: {str(e)}')
        
        self.logger.info(f'Extraídos {len(posts)} posts')
        return posts
    
    def _extract_comments(self, task_id: str, url: str, limit: int, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrair comentários de uma página do Facebook.
        
        Args:
            task_id: ID da tarefa
            url: URL da página
            limit: Limite de comentários
            config: Configurações específicas
            
        Returns:
            Lista de comentários extraídos
        """
        comments = []
        
        try:
            if not self.driver:
                self.driver = self._setup_driver()
            
            self.logger.info(f'Extraindo comentários de: {url}')
            
            # Navegar para a página
            self.driver.get(url)
            self._random_delay()
            
            # Aguardar carregamento
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Tentar expandir comentários
            self._expand_comments(task_id)
            
            # Obter HTML da página
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Encontrar comentários
            comment_selectors = [
                '[data-testid="comment"]',
                '.UFICommentContent',
                '._3l3x'
            ]
            
            comment_elements = []
            for selector in comment_selectors:
                elements = soup.select(selector)
                if elements:
                    comment_elements = elements
                    break
            
            # Extrair dados dos comentários
            for i, comment_elem in enumerate(comment_elements[:limit]):
                if self.stop_flags.get(task_id, False):
                    break
                
                try:
                    content = self._safe_get_text(comment_elem)
                    
                    if content and len(content.strip()) > 3:
                        # Extrair autor do comentário
                        author_elem = comment_elem.find('strong') or comment_elem.find('[data-testid="comment_author"]')
                        author = self._safe_get_text(author_elem) if author_elem else ''
                        
                        comments.append({
                            'content': content,
                            'source_url': url,
                            'author': author,
                            'timestamp': '',  # Implementar extração de timestamp se necessário
                            'likes_count': 0,  # Implementar extração de curtidas se necessário
                            'comments_count': 0,
                            'shares_count': 0
                        })
                        
                        self.logger.debug(f'Comentário {i+1} extraído: {content[:50]}...')
                
                except Exception as e:
                    self.logger.warning(f'Erro ao processar comentário {i+1}: {str(e)}')
                    continue
        
        except Exception as e:
            self.logger.error(f'Erro ao extrair comentários: {str(e)}')
        
        self.logger.info(f'Extraídos {len(comments)} comentários')
        return comments
    
    def _extract_profile_info(self, task_id: str, url: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrair informações de perfil.
        
        Args:
            task_id: ID da tarefa
            url: URL do perfil
            config: Configurações específicas
            
        Returns:
            Lista com informações do perfil
        """
        profile_info = []
        
        try:
            if not self.driver:
                self.driver = self._setup_driver()
            
            self.logger.info(f'Extraindo informações de perfil: {url}')
            
            # Navegar para a página
            self.driver.get(url)
            self._random_delay()
            
            # Aguardar carregamento
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Obter HTML da página
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extrair informações básicas
            profile_data = {
                'content': '',
                'source_url': url,
                'name': '',
                'description': '',
                'followers_count': 0,
                'following_count': 0,
                'posts_count': 0
            }
            
            # Extrair nome da página/perfil
            name_selectors = ['h1', '[data-testid="page_title"]', '.profileName']
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem:
                    profile_data['name'] = self._safe_get_text(name_elem)
                    break
            
            # Extrair descrição
            desc_selectors = ['[data-testid="page_description"]', '.profileDescription', '.intro']
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    profile_data['description'] = self._safe_get_text(desc_elem)
                    break
            
            # Montar conteúdo principal
            profile_data['content'] = f"Nome: {profile_data['name']}\nDescrição: {profile_data['description']}"
            
            if profile_data['name'] or profile_data['description']:
                profile_info.append(profile_data)
        
        except Exception as e:
            self.logger.error(f'Erro ao extrair informações de perfil: {str(e)}')
        
        self.logger.info(f'Extraídas informações de perfil')
        return profile_info
    
    def _scroll_to_load_content(self, target_items: int, task_id: str) -> None:
        """Fazer scroll para carregar mais conteúdo.
        
        Args:
            target_items: Número alvo de itens a carregar
            task_id: ID da tarefa (para verificar stop flag)
        """
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scrolls = 0
            max_scrolls = min(target_items // 5, 10)  # Limitar número de scrolls
            
            while scrolls < max_scrolls and not self.stop_flags.get(task_id, False):
                # Scroll para baixo
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Aguardar carregamento
                self._random_delay()
                
                # Verificar se carregou mais conteúdo
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                
                last_height = new_height
                scrolls += 1
                
        except Exception as e:
            self.logger.warning(f'Erro durante scroll: {str(e)}')
    
    def _expand_comments(self, task_id: str) -> None:
        """Tentar expandir comentários na página.
        
        Args:
            task_id: ID da tarefa (para verificar stop flag)
        """
        try:
            # Procurar botões de "Ver mais comentários"
            expand_buttons = self.driver.find_elements(By.XPATH, 
                "//span[contains(text(), 'Ver mais') or contains(text(), 'View more') or contains(text(), 'comentários')]"
            )
            
            for button in expand_buttons[:3]:  # Limitar a 3 cliques
                if self.stop_flags.get(task_id, False):
                    break
                
                try:
                    if button.is_displayed() and button.is_enabled():
                        self.driver.execute_script("arguments[0].click();", button)
                        self._random_delay()
                except Exception:
                    continue
                    
        except Exception as e:
            self.logger.warning(f'Erro ao expandir comentários: {str(e)}')
    
    def stop_scraping(self, task_id: str) -> None:
        """Parar scraping de uma tarefa específica.
        
        Args:
            task_id: ID da tarefa a ser parada
        """
        if task_id in self.active_tasks:
            self.stop_flags[task_id] = True
            self.logger.info(f'Scraping da tarefa {task_id} foi sinalizado para parar')
        
        # Fechar driver se estiver ativo
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
    
    def is_task_active(self, task_id: str) -> bool:
        """Verificar se uma tarefa está ativa.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            True se a tarefa está ativa
        """
        return task_id in self.active_tasks
    
    def __del__(self):
        """Destrutor para garantir limpeza do driver."""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass