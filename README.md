# AI Contest Server

Сервис для проведения конкурса по искусственному интеллекту.  
Реализован на **FastAPI + SQLite**  включает автоматическую выдачу заданий, приём решений и WebSocket-подключения.

##  Возможности

- Автоматическая выдача заданий каждые 30 секунд
- JWT-аутентификация пользователей
- WebSocket подключения для real-time обновлений
- Сохранение решений участников
- Интерактивная Swagger документация
- Безопасное хранение данных в SQLite
- Асинхронная обработка запросов

##  Структура проекта

```
version2/
├── contest_server/           ← Бэкенд на FastAPI
│   ├── tasks/               ← директория для активных заданий
│   ├── tasks_pool/          ← пул из 50 заранее сгенерированных JSON-заданий
│   ├── submissions/         ← хранилище решений участников
│   ├── emulator/           ← клиент-эмулятор для тестирования
│   │   └── emulator.py
│   ├── main.py             ← точка входа FastAPI приложения
│   ├── scheduler.py        ← планировщик заданий (APScheduler)
│   ├── auth.py            ← система JWT-аутентификации
│   ├── models.py          ← ORM модели SQLAlchemy
│   ├── database.py        ← конфигурация базы данных
│   ├── websocket.py       ← WebSocket менеджер
│   └── requirements.txt    ← зависимости Python
│
├── ai-competition-new/     ← Фронтенд на Next.js
│   ├── src/               ← исходный код
│   ├── app/               ← роутинг и компоненты Next.js
│   ├── public/            ← статические файлы
│   ├── package.json       ← зависимости и скрипты
│   └── tailwind.config.js ← конфигурация Tailwind CSS
│
└── README.md
```

##  Установка и настройка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/your-username/ai-contest-server.git
   cd ai-contest-server
   ```

2. Установите зависимости бэкенда:
   ```bash
   cd contest_server
   pip install -r requirements.txt
   cd ..
   ```

3. Установите зависимости фронтенда:
   ```bash
   cd ai-competition-new
   npm install
   cd ..
   ```

## 🚀 Запуск

1. Запустите бэкенд:
   ```bash
   cd contest_server
   uvicorn main:app --reload 
   ```

2. В отдельном терминале запустите фронтенд:
   ```bash
   cd ai-competition-new
   npm run dev
   ```

3. Проверьте работу сервера:
   - Фронтенд: http://localhost:3000
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 💻 Фронтенд


### Запуск в production:
```bash
cd ai-competition-new
npm run build
npm start
```

## 🔧 Конфигурация

Основные настройки можно изменить через переменные окружения:
- `SECRET_KEY`: ключ для JWT-токенов
- `TASK_INTERVAL`: интервал выдачи заданий (по умолчанию 30 сек)
- `DATABASE_URL`: путь к базе данных
- `DEBUG`: режим отладки (True/False)

## 📝 API Endpoints

- `POST /auth/register`: регистрация нового пользователя
- `POST /auth/login`: получение JWT-токена
- `GET /tasks/current`: получение текущего задания
- `POST /submissions`: отправка решения
- `GET /submissions/history`: история решений
- `WS /ws`: WebSocket подключение

## 👥 Команда разработки

**Команда "Невдупленыши"**

- Автор кейса: **Сергей Михайлович Щербаков**
- Разработчики: 
  - **Другова Мила** - Backend (FastAPI), WebSocket
  - **Ульянова Риана** - Frontend 


