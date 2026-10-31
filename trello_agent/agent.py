import sys
from pathlib import Path

# Importa o root_agent e as ferramentas do agent.py principal da raiz do projeto
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from agent import root_agent, criar_tarefa, listar_tarefas, mover_tarefa, remover_tarefa, listar_quadros

__all__ = ["root_agent", "criar_tarefa", "listar_tarefas", "mover_tarefa", "remover_tarefa", "listar_quadros"]
