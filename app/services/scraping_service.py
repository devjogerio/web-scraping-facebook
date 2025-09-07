"""Serviço de scraping do Facebook.

Este módulo implementa a lógica de extração de dados do Facebook
utilizando Selenium e BeautifulSoup de forma responsável.
"""

import time
import random
import logging
from typing import List, Dict, Any, Optional
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
        self.logger = logging.getLogger(__name__)
        self.driver = None
        self.active_tasks = set()
        
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
            self.logger.error(f"Erro ao configurar driver: {str(e)}")
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
            self.logger.warning(f"Erro ao extrair metadados: {str(e)}")
        
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
    
    def extract_posts(self, url: str, limit: int, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrair posts de uma página do Facebook.
        
        Args:
            url: URL da página
            limit: Limite de posts
            config: Configurações específicas
            
        Returns:
            Lista de posts extraídos
        """
        posts = []
        
        try:
            self.driver = self._setup_driver()
            self.logger.info(f"Extraindo posts de: {url}")
            
            # Navegar para a página
            self.driver.get(url)
            self._random_delay()
            
            # Aguardar carregamento
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Simular scroll para carregar mais posts
            self._scroll_to_load_content(limit)
            
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
                        
                        self.logger.debug(f"Post {i+1} extraído: {content[:100]}...")
                    
                except Exception as e:
                    self.logger.warning(f"Erro ao processar post {i+1}: {str(e)}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair posts: {str(e)}")
        
        finally:
            if self.driver:
                self.driver.quit()
        
        self.logger.info(f"Extraídos {len(posts)} posts")
        return posts
    
    def extract_comments(self, url: str, limit: int, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrair comentários de uma página do Facebook.
        
        Args:
            url: URL da página
            limit: Limite de comentários
            config: Configurações específicas
            
        Returns:
            Lista de comentários extraídos
        """
        comments = []
        
        try:
            self.driver = self._setup_driver()
            self.logger.info(f"Extraindo comentários de: {url}")
            
            # Navegar para a página
            self.driver.get(url)
            self._random_delay()
            
            # Aguardar carregamento
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Tentar expandir comentários
            self._expand_comments()
            
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
                        
                        self.logger.debug(f"Comentário {i+1} extraído: {content[:50]}...")
                
                except Exception as e:
                    self.logger.warning(f"Erro ao processar comentário {i+1}: {str(e)}")
                    continue
        
        except Exception as e:
            self.logger.error(f"Erro ao extrair comentários: {str(e)}")
        
        finally:
            if self.driver:
                self.driver.quit()
        
        self.logger.info(f"Extraídos {len(comments)} comentários")
        return comments
    
    def extract_profile_info(self, url: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrair informações de perfil.
        
        Args:
            url: URL do perfil
            config: Configurações específicas
            
        Returns:
            Lista com informações do perfil
        """
        profile_info = []
        
        try:
            self.driver = self._setup_driver()
            self.logger.info(f"Extraindo informações de perfil: {url}")
            
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
            self.logger.error(f"Erro ao extrair informações de perfil: {str(e)}")
        
        finally:
            if self.driver:
                self.driver.quit()
        
        self.logger.info(f"Extraídas informações de perfil")
        return profile_info
    
    def extract_likes(self, url: str, limit: int, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrair curtidas (implementação simplificada).
        
        Args:
            url: URL da página
            limit: Limite de curtidas
            config: Configurações específicas
            
        Returns:
            Lista de curtidas extraídas
        """
        # Implementação simplificada - retorna lista vazia
        # Em uma implementação real, seria necessário navegar para páginas específicas de curtidas
        self.logger.info("Extração de curtidas não implementada nesta versão")
        return []
    
    def extract_shares(self, url: str, limit: int, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrair compartilhamentos (implementação simplificada).
        
        Args:
            url: URL da página
            limit: Limite de compartilhamentos
            config: Configurações específicas
            
        Returns:
            Lista de compartilhamentos extraídos
        """
        # Implementação simplificada - retorna lista vazia
        # Em uma implementação real, seria necessário navegar para páginas específicas de compartilhamentos
        self.logger.info("Extração de compartilhamentos não implementada nesta versão")
        return []
    
    def _scroll_to_load_content(self, target_items: int) -> None:
        """Fazer scroll para carregar mais conteúdo.
        
        Args:
            target_items: Número alvo de itens a carregar
        """
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scrolls = 0
            max_scrolls = min(target_items // 5, 10)  # Limitar número de scrolls
            
            while scrolls < max_scrolls:
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
            self.logger.warning(f"Erro durante scroll: {str(e)}")
    
    def _expand_comments(self) -> None:
        """Tentar expandir comentários na página."""
        try:
            # Procurar botões de "Ver mais comentários"
            expand_buttons = self.driver.find_elements(By.XPATH, 
                "//span[contains(text(), 'Ver mais') or contains(text(), 'View more') or contains(text(), 'comentários')]"
            )
            
            for button in expand_buttons[:3]:  # Limitar a 3 cliques
                try:
                    if button.is_displayed() and button.is_enabled():
                        self.driver.execute_script("arguments[0].click();", button)
                        self._random_delay()
                except Exception:
                    continue
                    
        except Exception as e:
            self.logger.warning(f"Erro ao expandir comentários: {str(e)}")
    
    def stop_scraping(self, task_id: str) -> None:
        """Parar scraping de uma tarefa específica.
        
        Args:
            task_id: ID da tarefa a ser parada
        """
        if task_id in self.active_tasks:
            self.active_tasks.remove(task_id)
            self.logger.info(f"Scraping da tarefa {task_id} foi sinalizado para parar")
        
        # Fechar driver se estiver ativo
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
    
    def __del__(self):
        """Destrutor para garantir limpeza do driver."""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass