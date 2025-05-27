from fastapi import FastAPI, WebSocket, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import logging
from typing import Dict
import uuid

from contest_server.database import init_db, SessionLocal
from contest_server.models import Team, Task, Solution, SolutionStatus
from contest_server.auth import create_token, verify_token, get_password_hash, verify_password, create_access_token, get_current_user
from contest_server.websocket import ws_manager
from contest_server.scheduler import start_scheduler
from contest_server.task_loader import initialize_task_pool
from contest_server.schemas import (
    TaskSubmissionRequest, 
    TaskSubmissionResponse, 
    ExpectedTaskResponse, 
    TeamCreate, 
    Token, 
    SolutionCreate, 
    SolutionResponse, 
    TaskResponse
)

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

@app.post("/createTeam", response_model=Token)
async def create_team(team_data: TeamCreate, db: Session = Depends(get_db)):
    # Проверяем, не существует ли уже команда с таким именем
    if db.query(Team).filter(Team.name == team_data.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team with this name already exists"
        )
    
    # Создаем новую команду
    userId = str(uuid.uuid4())
    hashed_password = get_password_hash(team_data.password)
    
    team = Team(
        name=team_data.name,
        userId=userId,
        passs=hashed_password,
        dateCreate=datetime.utcnow()
    )
    
    db.add(team)
    db.commit()
    db.refresh(team)
    
    # Создаем токен доступа
    access_token = create_access_token(data={"sub": team.userId})
    return Token(access_token=access_token)

@app.post("/login", response_model=Token)
async def login(team_data: TeamCreate, db: Session = Depends(get_db)):
    # Находим команду по имени
    team = db.query(Team).filter(Team.name == team_data.name).first()
    if not team or not verify_password(team_data.password, team.passs):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect team name or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создаем токен доступа
    access_token = create_access_token(data={"sub": team.userId})
    return Token(access_token=access_token)

@app.post("/submit", response_model=SolutionResponse)
async def submit_solution(
    solution: SolutionCreate,
    current_user: Team = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Проверяем существование задачи
    task = db.query(Task).filter(Task.taskId == solution.taskId).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Создаем новое решение
    db_solution = Solution(
        userId=current_user.userId,
        taskId=solution.taskId,
        text=solution.text,
        status=SolutionStatus.PENDING
    )
    
    db.add(db_solution)
    db.commit()
    db.refresh(db_solution)
    
    return db_solution

@app.get("/task/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user: Team = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.taskId == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 