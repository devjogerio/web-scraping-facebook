"""Módulo de controllers.

Este módulo centraliza a importação de todos os controllers
da aplicação seguindo os padrões da Clean Architecture.
"""

from .dashboard_controller import DashboardController
from .scraping_controller import ScrapingController
from .export_controller import ExportController

# Exportar todos os controllers
__all__ = [
    'DashboardController',
    'ScrapingController',
    'ExportController'
]