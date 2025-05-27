import json
import random
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

def generate_classification_task() -> Dict[str, Any]:
    """Генерация задачи классификации изображений"""
    classes = ["cat", "dog", "bird", "car", "person", "bicycle", "tree", "building"]
    image_size = random.choice([(224, 224), (299, 299), (384, 384)])
    
    return {
        "task_type": "classification",
        "description": "Classify the objects in the image",
        "input_data": {
            "image_url": f"https://example.com/images/task_{random.randint(1000, 9999)}.jpg",
            "image_size": image_size,
            "format": "RGB",
        },
        "constraints": {
            "max_processing_time": random.uniform(0.5, 2.0),
            "min_confidence": 0.7,
            "available_classes": random.sample(classes, k=random.randint(2, 5))
        }
    }

def generate_object_detection_task() -> Dict[str, Any]:
    """Генерация задачи обнаружения объектов"""
    objects = ["person", "car", "bicycle", "motorcycle", "traffic_light", "stop_sign"]
    image_size = random.choice([(640, 480), (800, 600), (1024, 768)])
    
    return {
        "task_type": "object_detection",
        "description": "Detect and locate objects in the image",
        "input_data": {
            "image_url": f"https://example.com/images/scene_{random.randint(1000, 9999)}.jpg",
            "image_size": image_size,
            "format": "RGB",
        },
        "constraints": {
            "max_processing_time": random.uniform(1.0, 3.0),
            "min_confidence": 0.8,
            "min_iou": 0.5,
            "target_objects": random.sample(objects, k=random.randint(2, 4))
        }
    }

def generate_segmentation_task() -> Dict[str, Any]:
    """Генерация задачи сегментации"""
    classes = ["background", "road", "sidewalk", "building", "vegetation", "sky", "person", "car"]
    image_size = random.choice([(512, 512), (768, 768), (1024, 1024)])
    
    return {
        "task_type": "segmentation",
        "description": "Perform semantic segmentation on the image",
        "input_data": {
            "image_url": f"https://example.com/images/scene_{random.randint(1000, 9999)}.jpg",
            "image_size": image_size,
            "format": "RGB",
        },
        "constraints": {
            "max_processing_time": random.uniform(2.0, 5.0),
            "min_accuracy": 0.75,
            "classes": random.sample(classes, k=random.randint(3, 6))
        }
    }

def generate_keypoint_detection_task() -> Dict[str, Any]:
    """Генерация задачи определения ключевых точек"""
    keypoints = ["nose", "left_eye", "right_eye", "left_ear", "right_ear", "left_shoulder", "right_shoulder"]
    image_size = random.choice([(512, 512), (640, 640), (768, 768)])
    
    return {
        "task_type": "keypoint_detection",
        "description": "Detect keypoints on human bodies",
        "input_data": {
            "image_url": f"https://example.com/images/person_{random.randint(1000, 9999)}.jpg",
            "image_size": image_size,
            "format": "RGB",
        },
        "constraints": {
            "max_processing_time": random.uniform(1.0, 3.0),
            "min_confidence": 0.7,
            "keypoints": random.sample(keypoints, k=random.randint(3, 7)),
            "max_distance_error": random.randint(5, 15)
        }
    }

def generate_tasks(num_tasks: int = 50) -> List[Dict[str, Any]]:
    """Генерация заданного количества разнообразных задач"""
    task_generators = [
        generate_classification_task,
        generate_object_detection_task,
        generate_segmentation_task,
        generate_keypoint_detection_task
    ]
    
    tasks = []
    for i in range(num_tasks):
        # Выбираем случайный генератор задач
        generator = random.choice(task_generators)
        task = generator()
        
        # Добавляем общие поля
        task.update({
            "task_id": i + 1,
            "difficulty": random.randint(1, 5),
            "max_attempts": 3,
            "time_limit": random.randint(30, 120),  # секунды
            "memory_limit": random.randint(512, 2048)  # MB
        })
        
        tasks.append(task)
    
    return tasks

def save_tasks(tasks: List[Dict[str, Any]], output_dir: str) -> None:
    """Сохранение задач в JSON файлы"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for task in tasks:
        file_path = output_path / f"task_{task['task_id']:03d}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(task, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    # Генерируем и сохраняем задачи
    tasks = generate_tasks(50)
    save_tasks(tasks, "dataset")
    print(f"Generated and saved {len(tasks)} tasks in the dataset directory") 