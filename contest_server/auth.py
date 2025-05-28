import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import time
<<<<<<< HEAD
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get secrets from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "")  # Will be empty if not set
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
security = HTTPBearer()

if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set. Please set it in .env file")

def create_token(name: str):
=======
from typing import Optional
import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from contest_server.database import get_db
from contest_server.models import Team
from contest_server.schemas import TokenData

# Безопасное хранение секретных ключей
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")  # Добавляем значение по умолчанию для тестирования
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 часа

LIVE_TIME = 3600  # 1 час в секундах (уменьшено с 24 часов для большей безопасности)
ALGORITHM = "HS256"
MIN_NAME_LENGTH = 3
MAX_NAME_LENGTH = 50

# Инициализация безопасности
security = HTTPBearer(
    scheme_name="JWT",
    description="Введите ваш JWT токен в формате: Bearer <token>",
    auto_error=True  # Изменено на True для автоматической обработки ошибок
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_token(name: str) -> str:
    """
    Создает JWT токен для пользователя
    :param name: Имя пользователя (subject)
    :return: Закодированный JWT токен
    :raises: ValueError если имя не соответствует требованиям
    """
    if not name or not isinstance(name, str):
        raise ValueError("Имя пользователя должно быть непустой строкой")
    
    if len(name) < MIN_NAME_LENGTH or len(name) > MAX_NAME_LENGTH:
        raise ValueError(f"Длина имени должна быть от {MIN_NAME_LENGTH} до {MAX_NAME_LENGTH} символов")
    
    if not name.replace("_", "").isalnum():
        raise ValueError("Имя может содержать только буквы, цифры и знак подчеркивания")
    
>>>>>>> d4064c07154b37cc68ec40159791ab6874354da3
    payload = {
        "sub": name,
        "exp": int(time.time() + LIVE_TIME),
        "iat": int(time.time()),
        "iss": "ai_competition_service",
        "jti": os.urandom(16).hex()  # Добавляем уникальный идентификатор токена
    }
    
    try:
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as e:
        raise RuntimeError(f"Ошибка создания токена: {str(e)}")

def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """
    Верифицирует JWT токен и возвращает имя пользователя
    :param credentials: Учетные данные из заголовка Authorization
    :return: Имя пользователя (subject)
    :raises: HTTPException 401 если токен невалидный
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={
                "require_exp": True,  # Требуем наличие expiration
                "require_sub": True,  # Требуем наличие subject
            }
        )
        
        # Дополнительная проверка subject
        if not payload.get("sub"):
            raise JWTError("Отсутствует subject в токене")
            
        return payload["sub"]
        
    except jwt.ExpiredSignatureError: # type: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен истек",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Неверный токен: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка проверки токена: {str(e)}"
        )

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Team:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        userId: str = payload.get("sub")
        if userId is None:
            raise credentials_exception
        token_data = TokenData(userId=userId)
    except JWTError:
        raise credentials_exception
        
    user = db.query(Team).filter(Team.userId == token_data.userId).first()
    if user is None:
        raise credentials_exception
    return user