from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import time
from typing import Optional
import os

# Безопасное хранение секретных ключей
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY environment variable is not set")

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