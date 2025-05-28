<<<<<<< HEAD
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
=======
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text
>>>>>>> d4064c07154b37cc68ec40159791ab6874354da3
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class SolutionStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    PROCESSING = "processing"

class Team(Base):
<<<<<<< HEAD
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    token = Column(String, unique=True)
    status = Column(String, default="disconnected")  # connected/disconnected
    created_at = Column(DateTime, default=datetime.utcnow)

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True)
    task_file = Column(String)
    content = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    issued_at = Column(DateTime)
=======
    __tablename__ = "team"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    userId = Column(String(50), unique=True, index=True, nullable=False)
    passs = Column(String(256), nullable=False)  # Хранение хеша пароля
    dateCreate = Column(DateTime, default=func.now(), nullable=False)

class Solution(Base):
    __tablename__ = "solution"

    solutionId = Column(Integer, primary_key=True, index=True)
    status = Column(Enum(SolutionStatus), nullable=False, default=SolutionStatus.PENDING)
    userId = Column(String(50), ForeignKey("team.userId"), nullable=False)
    text = Column(Text, nullable=False)
    taskId = Column(Integer, ForeignKey("task.taskId"), nullable=False)

class Task(Base):
    __tablename__ = "task"

    taskId = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    content = Column(Text, nullable=False)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    connection_id = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
>>>>>>> d4064c07154b37cc68ec40159791ab6874354da3

class Submission(Base):
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True)
<<<<<<< HEAD
    team_name = Column(String, ForeignKey("teams.name"))
    task_file = Column(String)
    submission_file = Column(String)
    content = Column(JSON)
    received_at = Column(DateTime)
    submitted_at = Column(DateTime)
    processing_time = Column(Integer)  # в миллисекундах
    status = Column(String)  # SUCCESS, INVALID_JSON, INVALID_FORMAT, ERROR
=======
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, nullable=False)
    solution = Column(String, nullable=False)  # JSON строка с решением
    submitted_at = Column(DateTime, default=datetime.utcnow)
    score = Column(Integer, nullable=True)  # Оценка решения (если применимо)
>>>>>>> d4064c07154b37cc68ec40159791ab6874354da3
