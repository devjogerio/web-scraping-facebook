"""Módulo de views da aplicação Flet."""

from .dashboard_view import DashboardView
from .new_task_view import NewTaskView
from .task_detail_view import TaskDetailView

__all__ = [
    'DashboardView',
    'NewTaskView',
    'TaskDetailView'
]