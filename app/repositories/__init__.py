"""Módulo de repositórios.

Este módulo centraliza a importação de todos os repositórios
da aplicação seguindo os padrões da Clean Architecture.
"""

from .base_repository import BaseRepository
from .scraping_task_repository import ScrapingTaskRepository
from .facebook_data_repository import FacebookDataRepository
from .export_job_repository import ExportJobRepository

# Exportar todos os repositórios
__all__ = [
    'BaseRepository',
    'ScrapingTaskRepository',
    'FacebookDataRepository',
    'ExportJobRepository'
]