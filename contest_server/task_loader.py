import json
import os
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TaskLoader:
    def __init__(self, dataset_path: str):
        """
        Инициализация загрузчика задач
        :param dataset_path: Путь к директории с JSON файлами неразмеченного датасета
        """
        self.dataset_path = Path(dataset_path)
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset path {dataset_path} does not exist")

    def load_tasks(self) -> List[Dict[str, Any]]:
        """
        Загрузка JSON файлов из неразмеченного датасета
        :return: Список задач
        """
        tasks = []
        try:
            json_files = list(self.dataset_path.glob("*.json"))
            if not json_files:
                raise FileNotFoundError("No JSON files found in dataset directory")
            
            # Ограничиваем количество задач до 50
            json_files = json_files[:50]
            
            for i, json_file in enumerate(json_files, 1):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        # Загружаем данные из неразмеченного датасета как есть
                        unlabeled_data = json.load(f)
                        
                        # Создаем задачу на основе неразмеченных данных
                        task = {
                            'task_id': i,
                            'name': json_file.stem,
                            'content': json.dumps(unlabeled_data),  # Сохраняем оригинальные данные
                            'created_at': datetime.utcnow(),
                            'difficulty': self._estimate_difficulty(unlabeled_data),
                            'max_attempts': 3,
                            'task_type': self._determine_task_type(unlabeled_data),
                            'metadata': {
                                'original_file': json_file.name,
                                'file_size': os.path.getsize(json_file)
                            }
                        }
                        tasks.append(task)
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON file {json_file}: {e}")
                except Exception as e:
                    logger.error(f"Error processing file {json_file}: {e}")
            
            if not tasks:
                raise ValueError("No valid tasks could be loaded from the dataset")
            
            logger.info(f"Successfully loaded {len(tasks)} tasks from dataset")
            return tasks
        except Exception as e:
            logger.error(f"Error loading tasks from dataset: {e}")
            raise

    def _estimate_difficulty(self, data: Dict[str, Any]) -> int:
        """
        Оценка сложности задачи на основе данных
        :param data: Данные задачи
        :return: Уровень сложности (1-5)
        """
        try:
            # Оцениваем сложность на основе размера и структуры данных
            complexity_factors = [
                len(str(data)),  # размер данных
                len(self._get_all_keys(data)),  # количество уникальных ключей
                self._get_max_depth(data)  # максимальная глубина вложенности
            ]
            
            # Нормализация и взвешенная сумма факторов
            normalized_score = sum(complexity_factors) / (1000 * len(complexity_factors))
            difficulty = max(1, min(5, round(normalized_score * 5)))
            
            return difficulty
        except Exception:
            return 1  # По умолчанию возвращаем минимальную сложность

    def _determine_task_type(self, data: Dict[str, Any]) -> str:
        """
        Определение типа задачи на основе структуры данных
        :param data: Данные задачи
        :return: Тип задачи
        """
        # Анализируем структуру данных для определения типа задачи
        keys = set(self._get_all_keys(data))
        
        if any(key in keys for key in ['image', 'img', 'image_url', 'url']):
            if any(key in keys for key in ['bbox', 'bounding_box', 'boxes']):
                return 'object_detection'
            elif any(key in keys for key in ['mask', 'segment', 'segmentation']):
                return 'segmentation'
            elif any(key in keys for key in ['keypoint', 'point', 'landmark']):
                return 'keypoint_detection'
            else:
                return 'classification'
        return 'unknown'

    def _get_all_keys(self, data: Dict[str, Any], prefix: str = '') -> List[str]:
        """
        Рекурсивное получение всех ключей из словаря
        :param data: Словарь для анализа
        :param prefix: Префикс для вложенных ключей
        :return: Список всех ключей
        """
        keys = []
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            keys.append(full_key)
            if isinstance(value, dict):
                keys.extend(self._get_all_keys(value, full_key))
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                keys.extend(self._get_all_keys(value[0], full_key))
        return keys

    def _get_max_depth(self, data: Dict[str, Any], current_depth: int = 1) -> int:
        """
        Получение максимальной глубины вложенности словаря
        :param data: Словарь для анализа
        :param current_depth: Текущая глубина
        :return: Максимальная глубина
        """
        if not isinstance(data, (dict, list)):
            return current_depth
        
        max_depth = current_depth
        if isinstance(data, dict):
            for value in data.values():
                depth = self._get_max_depth(value, current_depth + 1)
                max_depth = max(max_depth, depth)
        elif isinstance(data, list) and data:
            for item in data:
                depth = self._get_max_depth(item, current_depth + 1)
                max_depth = max(max_depth, depth)
        
        return max_depth

def initialize_task_pool(dataset_path: str, db_session) -> None:
    """
    Инициализация пула задач из датасета
    :param dataset_path: Путь к директории с JSON файлами
    :param db_session: Сессия базы данных
    """
    from database import Task  # Импорт здесь во избежание циклических зависимостей
    
    try:
        loader = TaskLoader(dataset_path)
        tasks = loader.load_tasks()
        
        # Распределяем время создания задач
        total_tasks = len(tasks)
        time_step = timedelta(seconds=30)  # интервал между задачами
        
        for i, task_data in enumerate(tasks):
            # Устанавливаем время создания с учетом интервала
            task_data['created_at'] = datetime.utcnow() + (i * time_step)
            
            # Создаем задачу в базе данных
            task = Task(**task_data)
            db_session.add(task)
        
        db_session.commit()
        logger.info(f"Successfully initialized task pool with {total_tasks} tasks")
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error initializing task pool: {e}")
        raise 