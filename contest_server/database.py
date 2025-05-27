from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json
import os
from typing import Optional, List
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создаем базовый класс для моделей
Base = declarative_base()

# Определяем модели
class Team(Base):
    __tablename__ = 'teams'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    token = Column(String(256), nullable=False, unique=True)
    last_seen = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    submissions = relationship("Submission", back_populates="team")
    
    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}')>"

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    content = Column(Text, nullable=False)
    answer = Column(Text)
    is_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    issued_at = Column(DateTime)
    difficulty = Column(Integer, default=1)  # 1-5
    max_attempts = Column(Integer, default=3)
    
    submissions = relationship("Submission", back_populates="task")
    
    def __repr__(self):
        return f"<Task(id={self.id}, name='{self.name}')>"

class Submission(Base):
    __tablename__ = 'submissions'
    
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String(20), default='pending')
    received_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    score = Column(Integer)
    feedback = Column(Text)
    
    team = relationship("Team", back_populates="submissions")
    task = relationship("Task", back_populates="submissions")
    
    __table_args__ = (
        UniqueConstraint('team_id', 'task_id', name='unique_team_task_submission'),
    )
    
    def __repr__(self):
        return f"<Submission(id={self.id}, team_id={self.team_id}, task_id={self.task_id}, status='{self.status}')>"

# Настройка подключения к БД
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///contest.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {},
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_size=5,
    max_overflow=10
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Получение сессии базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db(add_test_data: bool = False):
    """
    Инициализация базы данных
    :param add_test_data: Флаг добавления тестовых данных
    """
    try:
        # Создаем все таблицы
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        if add_test_data:
            db = SessionLocal()
            try:
                if not db.query(Team).first():
                    # Создаем тестовые команды
                    teams = [
                        Team(
                            name='Team Alpha',
                            token='token_alpha',
                            last_seen=datetime.utcnow(),
                            is_active=True
                        ),
                        Team(
                            name='Team Beta',
                            token='token_beta',
                            last_seen=datetime.utcnow(),
                            is_active=True
                        )
                    ]
                    
                    # Создаем тестовые задачи с разной сложностью
                    tasks = []
                    for i in range(1, 6):
                        tasks.append(Task(
                            name=f'Task {i}',
                            content=json.dumps({
                                'description': f'Test task {i}',
                                'constraints': {
                                    'time_limit': 1000,  # ms
                                    'memory_limit': 256  # MB
                                }
                            }),
                            answer=json.dumps({'selections': []}),
                            created_at=datetime.utcnow(),
                            difficulty=i,
                            max_attempts=3
                        ))
                    
                    db.add_all(teams + tasks)
                    db.commit()
                    logger.info('Test data added successfully')
            except Exception as e:
                db.rollback()
                logger.error(f'Error adding test data: {e}')
                raise
            finally:
                db.close()
                
    except Exception as e:
        logger.error(f'Database initialization error: {e}')
        raise

def validate_submission(db: SessionLocal, team_id: int, task_id: int) -> Optional[str]:
    """
    Проверяет возможность отправки решения
    :return: Сообщение об ошибке или None, если проверка пройдена
    """
    try:
        # Проверяем существование команды
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return "Team not found"
        if not team.is_active:
            return "Team is not active"
            
        # Проверяем существование задачи
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return "Task not found"
        if not task.is_sent:
            return "Task is not available yet"
            
        # Проверяем количество попыток
        attempts = db.query(Submission).filter(
            Submission.team_id == team_id,
            Submission.task_id == task_id
        ).count()
        
        if attempts >= task.max_attempts:
            return f"Maximum number of attempts ({task.max_attempts}) exceeded"
            
        return None
    except Exception as e:
        logger.error(f"Error validating submission: {e}")
        return "Internal validation error"