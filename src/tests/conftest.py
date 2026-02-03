# src/tests/conftest.py
import sys
import os

# Получаем абсолютный путь к корню проекта (finance_bot)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Добавляем корень проекта в Python path
sys.path.insert(0, project_root)

# Также добавляем src в путь
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)