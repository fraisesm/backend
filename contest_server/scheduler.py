import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
<<<<<<< HEAD
import shutil
import os
from websocket import ws_manager
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TASK_POOL_DIR = "tasks_pool"  # задания тут
TASK_OUT_DIR = "tasks"        # выдача сюда

issued_task_index = 1
total_tasks = 50

async def issue_task():
    global issued_task_index
    if issued_task_index > total_tasks:
        logger.info("[SCHEDULER] Все задания выданы.")
        return

    src_file = os.path.join(TASK_POOL_DIR, f"task_{issued_task_index:03}.json")
    dst_file = os.path.join(TASK_OUT_DIR, f"task_{issued_task_index:03}.json")
=======
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_
import json
from typing import Optional
from contest_server.database import SessionLocal, Task
from contest_server.websocket import ws_manager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Константы
MAX_TASKS = 50  # Максимальное количество задач
TASK_INTERVAL = 30  # Интервал выдачи задач в секундах
>>>>>>> d4064c07154b37cc68ec40159791ab6874354da3

async def issue_task() -> Optional[Task]:
    """
    Выдает следующее доступное задание
    :return: Выданное задание или None, если нет доступных заданий
    """
    db = SessionLocal()
    try:
<<<<<<< HEAD
        # Копируем файл задания
        shutil.copy(src_file, dst_file)
        
        # Читаем содержимое задания для отправки через WebSocket
        with open(src_file, 'r', encoding='utf-8') as f:
            task_content = json.load(f)
        
        # Добавляем метаданные
        task_data = {
            "task_id": issued_task_index,
            "timestamp": datetime.now().isoformat(),
            "content": task_content
        }
        
        # Отправляем всем подключенным клиентам
        await ws_manager.broadcast(json.dumps(task_data))
        
        logger.info(f"[SCHEDULER] [{datetime.now()}] Выдано задание {issued_task_index}/{total_tasks}: task_{issued_task_index:03}.json")
        issued_task_index += 1
        
    except FileNotFoundError:
        logger.error(f"[SCHEDULER] Файл {src_file} не найден.")
    except Exception as e:
        logger.error(f"[SCHEDULER] Ошибка при выдаче задания: {e}")

def start_scheduler():
    """Запуск планировщика задач"""
    try:
        os.makedirs(TASK_OUT_DIR, exist_ok=True)
        scheduler = AsyncIOScheduler()
        scheduler.add_job(issue_task, "interval", seconds=30)
        scheduler.start()
        logger.info("[SCHEDULER] Планировщик успешно запущен")
    except Exception as e:
        logger.error(f"[SCHEDULER] Ошибка при запуске планировщика: {e}")
=======
        # Получаем следующее доступное задание
        task = db.query(Task).filter(
            and_(
                Task.is_sent == False,  # type: ignore
                Task.created_at <= datetime.utcnow()
            )
        ).first()
        
        if task:
            task.is_sent = True
            task.issued_at = datetime.utcnow()
            db.commit()
            
            # Отправляем задание всем подключенным клиентам
            await ws_manager.broadcast(
                json.dumps({
                    "type": "new_task",
                    "task": {
                        "id": task.id,
                        "content": task.content
                    }
                })
            )
            
            logger.info(f"Выдано задание {task.id}")
            return task
            
        return None
        
    except Exception as e:
        logger.error(f"Ошибка при выдаче задания: {str(e)}")
        db.rollback()
        return None
    finally:
        db.close()

async def broadcast_available_tasks(db: Session):
    """
    Отправляет список всех доступных заданий подключенным командам
    :param db: Сессия базы данных
    """
    try:
        # Получаем все выданные задания
        available_tasks = db.query(Task).filter(Task.is_sent == True).all()
        total_issued = len(available_tasks)
        
        tasks_list = [{
            "task_id": task.id,
            "name": task.name,
            "content": json.loads(task.content),
            "difficulty": task.difficulty,
            "max_attempts": task.max_attempts,
            "issued_at": task.issued_at.isoformat() if task.issued_at else None
        } for task in available_tasks]

        message = {
            "type": "available_tasks",
            "data": {
                "tasks": tasks_list,
                "total_issued": total_issued,
                "max_tasks": MAX_TASKS,
                "remaining_tasks": MAX_TASKS - total_issued,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        await ws_manager.broadcast(json.dumps(message))
        
    except Exception as e:
        logger.error(f"Ошибка при отправке списка доступных заданий: {str(e)}")

def start_scheduler():
    """
    Запускает планировщик выдачи заданий
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(issue_task, 'interval', seconds=TASK_INTERVAL)
    scheduler.start()
    logger.info("Планировщик запущен")
>>>>>>> d4064c07154b37cc68ec40159791ab6874354da3
