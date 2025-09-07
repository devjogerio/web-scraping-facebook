"""Módulo de modelos de dados.

Este módulo centraliza a importação de todos os modelos de dados
da aplicação seguindo os padrões da Clean Architecture.
"""

from .scraping_task import ScrapingTask
from .facebook_data import FacebookData
from .export_job import ExportJob

# Exportar todos os modelos
__all__ = [
    'ScrapingTask',
    'FacebookData',
    'ExportJob'
]