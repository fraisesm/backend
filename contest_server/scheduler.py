TASK_POOL_DIR = "tasks_pool"  # задания тут
TASK_OUT_DIR = "tasks"        # выдача сюда

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
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

async def issue_task() -> Optional[Task]:
    """
    Выдает следующее доступное задание
    :return: Выданное задание или None, если нет доступных заданий
    """
    db = SessionLocal()
    try:
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
