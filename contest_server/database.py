from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

engine = create_engine("sqlite:///contest.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    ## проверка что у тебя нет таблиц
    ## иначе скип
    // нужно написать  sql скрипт( патч) для заполнения стартовыми данными моей таблицы таск так что бы данные
    были похожи на настоящие
    Base.metadata.create_all(bind=engine) # type: ignore
