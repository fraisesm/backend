from fastapi import FastAPI, WebSocket, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json
import logging
from typing import Dict

from database import init_db, SessionLocal, Team, Task, Submission
from auth import create_token, verify_token
from websocket import ws_manager
from scheduler import start_scheduler
from task_loader import initialize_task_pool
from schemas import TaskSubmissionRequest, TaskSubmissionResponse, ExpectedTaskResponse

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Contest Server",
    description="Сервер для проведения AI соревнований с выдачей задач в реальном времени",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация
DATASET_PATH = "dataset"  # Путь к директории с JSON файлами датасета

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске сервера"""
    try:
        # Инициализация базы данных
        init_db(add_test_data=False)  # Отключаем тестовые данные
        logger.info("База данных инициализирована")
        
        # Инициализация пула задач из датасета
        db = SessionLocal()
        try:
            initialize_task_pool(DATASET_PATH, db)
            logger.info("Пул задач инициализирован")
        finally:
            db.close()
        
        # Запуск планировщика
        start_scheduler()
        logger.info("Планировщик запущен")
    except Exception as e:
        logger.error(f"Ошибка при инициализации: {str(e)}")
        raise

@app.get("/task_format")
async def get_task_format():
    """
    Получение информации о формате ответа на задачи
    """
    return {
        "description": "Формат ответа на задачи",
        "schema": ExpectedTaskResponse.schema()
    }

@app.post("/submit", response_model=TaskSubmissionResponse)
async def submit_solution(
    solution: TaskSubmissionRequest,
    team_name: str = Depends(verify_token)
):
    """
    Прием решения от команды
    """
    db = SessionLocal()
    try:
        team = db.query(Team).filter(Team.name == team_name).first()
        if not team:
            raise HTTPException(status_code=404, detail="Команда не найдена")
        
        task = db.query(Task).filter(Task.id == solution.task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Задание не найдено")
        
        # Проверяем формат решения
        try:
            ExpectedTaskResponse(**solution.solution)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Неверный формат решения: {str(e)}"
            )
        
        # Создаем новое решение
        submission = Submission(
            team_id=team.id,
            task_id=solution.task_id,
            content=json.dumps(solution.solution),
            status="received",
            received_at=datetime.utcnow(),
            metadata=json.dumps(solution.metadata) if solution.metadata else None
        )
        db.add(submission)
        db.commit()
        
        logger.info(f"Получено решение от команды {team_name} для задания {solution.task_id}")
        
        return TaskSubmissionResponse(
            submission_id=submission.id,
            status=submission.status,
            received_at=submission.received_at,
            message="Решение успешно принято"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при сохранении решения: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при сохранении решения")
    finally:
        db.close()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    """
    WebSocket эндпоинт для реального времени
    """
    if not token:
        await websocket.close(code=4001, reason="Требуется токен")
        return
    
    try:
        team_name = verify_token(token)
        db = SessionLocal()
        
        try:
            team = db.query(Team).filter(Team.name == team_name).first()
            if not team:
                await websocket.close(code=4004, reason="Команда не найдена")
                return
                
            team.last_seen = datetime.utcnow()
            db.commit()
            
            await ws_manager.connect(team_name, websocket)
            
            try:
                while True:
                    data = await websocket.receive_text()
                    # Обработка входящих сообщений, если необходимо
                    
            except Exception as e:
                logger.error(f"Ошибка WebSocket соединения: {str(e)}")
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Ошибка при обработке WebSocket подключения: {str(e)}")
        await websocket.close(code=4000, reason="Внутренняя ошибка сервера")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 