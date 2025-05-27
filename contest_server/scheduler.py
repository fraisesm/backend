TASK_POOL_DIR = "tasks_pool"  # задания тут
TASK_OUT_DIR = "tasks"        # выдача сюда

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_
import json
from typing import Optional
from database import SessionLocal, Task
from websocket import ws_manager

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
        # Проверяем количество уже выданных задач
        issued_count = db.query(Task).filter(Task.is_sent == True).count()
        if issued_count >= MAX_TASKS:
            logger.info(f"Достигнут лимит выданных задач ({MAX_TASKS})")
            return None

        # Получаем первое невыданное задание, отсортированное по ID
        task = db.query(Task).filter(
            and_(
                Task.is_sent == False,  # Задание еще не выдано
                Task.created_at <= datetime.utcnow()  # Время выдачи наступило
            )
        ).order_by(Task.id).first()

        if not task:
            logger.info("Все доступные задания уже выданы")
            return None

        # Помечаем задание как выданное
        task.is_sent = True
        task.issued_at = datetime.utcnow()
        db.commit()

        # Формируем сообщение о новом задании
        task_message = {
            "type": "new_task",
            "data": {
                "task_id": task.id,
                "name": task.name,
                "content": json.loads(task.content),
                "difficulty": task.difficulty,
                "max_attempts": task.max_attempts,
                "issued_at": task.issued_at.isoformat(),
                "remaining_tasks": MAX_TASKS - (issued_count + 1)
            }
        }

        # Отправляем уведомление всем подключенным командам
        await ws_manager.broadcast(json.dumps(task_message))
        
        # Отправляем обновленный список всех доступных заданий
        await broadcast_available_tasks(db)
        
        logger.info(f"Выдано задание: {task.name} (ID: {task.id}). Осталось задач: {MAX_TASKS - (issued_count + 1)}")
        
        # Если это последнее задание, отправляем уведомление
        if issued_count + 1 >= MAX_TASKS:
            await ws_manager.broadcast(json.dumps({
                "type": "contest_status",
                "data": {
                    "status": "completed",
                    "message": "Все задания выданы",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }))
        
        return task

    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при выдаче задания: {str(e)}")
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

def start_scheduler(interval_seconds: int = TASK_INTERVAL):
    """
    Запускает планировщик выдачи заданий
    :param interval_seconds: Интервал между выдачей заданий в секундах
    """
    try:
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            issue_task, 
            "interval", 
            seconds=interval_seconds,
            max_instances=1,  # Предотвращаем параллельное выполнение
            coalesce=True    # Пропускаем пропущенные запуски
        )
        scheduler.start()
        logger.info(f"Планировщик запущен с интервалом {interval_seconds} секунд. "
                   f"Максимальное количество задач: {MAX_TASKS}")
    except Exception as e:
        logger.error(f"Ошибка при запуске планировщика: {str(e)}")
        raise
