import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base, Submission, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Contest Server")

class ContestManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.current_task_index = 0
        self.task_interval = 30  # seconds
        
        # Database setup
        self.engine = create_engine("sqlite:///contest.db")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        # Load all tasks at startup
        self.tasks = self._load_tasks()
        logger.info(f"Loaded {len(self.tasks)} tasks")
        
        # Start task scheduler
        self.task_scheduler_task = None
    
    def _load_tasks(self) -> list:
        """Загрузка всех задач из JSON файлов"""
        tasks = []
        dataset_path = Path("dataset")
        for i in range(1, 51):
            file_path = dataset_path / f"raw_{i:03d}.json"
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    tasks.append(json.load(f))
        return tasks

    async def connect(self, websocket: WebSocket):
        """Подключение нового клиента"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"New client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Отключение клиента"""
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast_task(self):
        """Отправка текущей задачи всем подключенным клиентам"""
        if not self.tasks or not self.active_connections:
            return
            
        task = self.tasks[self.current_task_index]
        task_message = {
            "type": "task",
            "task_id": self.current_task_index + 1,
            "total_tasks": len(self.tasks),
            "data": task
        }
        
        # Отправляем задачу всем подключенным клиентам
        disconnected = set()
        for websocket in self.active_connections:
            try:
                await websocket.send_json(task_message)
            except Exception as e:
                logger.error(f"Error sending task: {e}")
                disconnected.add(websocket)
        
        # Удаляем отключившихся клиентов
        for websocket in disconnected:
            self.disconnect(websocket)
            
        self.current_task_index = (self.current_task_index + 1) % len(self.tasks)
        logger.info(f"Task {self.current_task_index} sent to {len(self.active_connections)} clients")

    async def start_task_scheduler(self):
        """Запуск планировщика задач"""
        while True:
            await self.broadcast_task()
            await asyncio.sleep(self.task_interval)

    async def handle_submission(self, websocket: WebSocket, data: Dict):
        """Обработка решения от участника"""
        try:
            session = self.Session()
            
            # Получаем или создаем пользователя
            user = session.query(User).filter_by(
                connection_id=str(id(websocket))
            ).first()
            
            if not user:
                user = User(connection_id=str(id(websocket)))
                session.add(user)
            
            # Создаем запись о решении
            submission = Submission(
                user_id=user.id,
                task_id=data["task_id"],
                solution=json.dumps(data["solution"]),
                submitted_at=datetime.utcnow()
            )
            session.add(submission)
            session.commit()
            
            # Отправляем подтверждение
            await websocket.send_json({
                "type": "submission_result",
                "status": "accepted",
                "task_id": data["task_id"]
            })
            
        except Exception as e:
            logger.error(f"Error handling submission: {e}")
            await websocket.send_json({
                "type": "submission_result",
                "status": "error",
                "message": str(e)
            })
            
        finally:
            session.close()

# Создаем глобальный менеджер
manager = ContestManager()

@app.on_event("startup")
async def startup_event():
    """Запуск планировщика при старте приложения"""
    asyncio.create_task(manager.start_task_scheduler())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint для подключения клиентов"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data["type"] == "submission":
                await manager.handle_submission(websocket, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/status")
async def get_status():
    """Получение статуса сервера"""
    return {
        "active_connections": len(manager.active_connections),
        "current_task": manager.current_task_index + 1,
        "total_tasks": len(manager.tasks)
    }

@app.get("/tasks")
async def get_tasks():
    """Получение списка всех задач"""
    return {
        "total": len(manager.tasks),
        "tasks": [
            {
                "id": i + 1,
                "type": task.get("image_id", "").split("_")[0]
            }
            for i, task in enumerate(manager.tasks)
        ]
    } 