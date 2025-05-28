import asyncio
import json
<<<<<<< HEAD
import random
import aiohttp
import websockets
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ParticipantEmulator:
    def __init__(self, server_url="http://127.0.0.1:8000", ws_url="ws://127.0.0.1:8000"):
        self.server_url = server_url
        self.ws_url = ws_url
        self.token = None
        self.team_name = f"team_{random.randint(1000, 9999)}"
        self.ws = None
        self.is_running = False
        self.reconnect_delay = 1  # Starting delay for exponential backoff
        self.max_retries = 5  # Максимальное количество попыток для операций
        self.current_task = None  # Текущее задание
        self.pending_solution = None  # Ожидающее отправки решение

    async def register(self):
        """Регистрация команды и получение токена"""
        try:
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field('name', self.team_name)
                logger.info(f"Attempting to register team {self.team_name}")
                async with session.post(f"{self.server_url}/register", data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.token = result["token"]
                        logger.info(f"Успешная регистрация команды {self.team_name}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка регистрации: статус {response.status}, ответ: {error_text}")
                        return False
        except Exception as e:
            logger.error(f"Ошибка при регистрации: {str(e)}")
            return False

    async def get_task(self):
        """Получение задания от сервера"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.token}"}
                async with session.get(f"{self.server_url}/task", headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Ошибка получения задания: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Ошибка при получении задания: {e}")
            return None

    async def submit_solution(self, solution):
        """Отправка решения на сервер"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.token}"}
                data = aiohttp.FormData()
                data.add_field('file', 
                             json.dumps(solution),
                             filename='solution.json',
                             content_type='application/json')
                
                async with session.post(f"{self.server_url}/submit", headers=headers, data=data) as response:
                    if response.status == 200:
                        logger.info("Решение успешно отправлено")
                        return True
                    else:
                        logger.error(f"Ошибка отправки решения: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Ошибка при отправке решения: {e}")
            return False

    def generate_solution(self, task_content):
        """Генерация решения с случайными координатами"""
        try:
            task_data = json.loads(task_content)
            text_length = len(task_data.get("text", ""))
            if text_length < 2:  # Проверка на минимальную длину текста
                return None
            
            start = random.randint(0, max(0, text_length - 10))
            end = random.randint(start + 1, min(text_length, start + 10))  # Уменьшил максимальный диапазон
            
            return {
                "selections": [
                    {
                        "type": "ЛОГИЧЕСКАЯ ОШИБКА",
                        "startSelection": start,
                        "endSelection": end
                    }
                ]
            }
        except Exception as e:
            logger.error(f"Ошибка при генерации решения: {e}")
            return None

    async def submit_with_retry(self, solution, max_retries=None):
        """Отправка решения с автоматическими повторными попытками"""
        if max_retries is None:
            max_retries = self.max_retries
            
        retries = 0
        while retries < max_retries:
            try:
                if await self.submit_solution(solution):
                    self.pending_solution = None
                    return True
                    
                retries += 1
                await asyncio.sleep(min(2 ** retries, 30))  # Экспоненциальная задержка
                
            except Exception as e:
                logger.error(f"Попытка {retries + 1} не удалась: {e}")
                retries += 1
                if retries == max_retries:
                    self.pending_solution = solution  # Сохраняем для последующей отправки
                    return False
                await asyncio.sleep(min(2 ** retries, 30))
        
        return False

    async def handle_websocket(self):
        """Обработка WebSocket соединения с улучшенным механизмом переподключения"""
        while self.is_running:
            try:
                async with websockets.connect(f"{self.ws_url}/ws/{self.team_name}") as websocket:
                    self.ws = websocket
                    self.reconnect_delay = 1  # Сброс задержки при успешном подключении
                    logger.info("WebSocket подключение установлено")
                    
                    # Проверяем наличие ожидающего решения
                    if self.pending_solution:
                        logger.info("Отправка ожидающего решения после переподключения...")
                        await self.submit_with_retry(self.pending_solution)
                    
                    while self.is_running:
                        try:
                            message = await websocket.recv()
                            logger.info(f"Получено сообщение: {message}")
                            
                            # Обработка нового задания
                            try:
                                task_data = json.loads(message)
                                self.current_task = task_data
                                # Генерация и отправка решения с задержкой
                                await self.process_task(task_data)
                            except json.JSONDecodeError:
                                logger.error("Получено некорректное JSON сообщение")
                            
                        except websockets.ConnectionClosed:
                            logger.warning("WebSocket соединение закрыто")
                            break
                        
            except Exception as e:
                logger.error(f"Ошибка WebSocket соединения: {e}")
                if self.is_running:
                    await asyncio.sleep(self.reconnect_delay)
                    self.reconnect_delay = min(self.reconnect_delay * 2, 60)
                    continue

    async def process_task(self, task_data):
        """Обработка полученного задания"""
        # Случайная задержка 1-5 секунд
        delay = random.uniform(1, 5)
        await asyncio.sleep(delay)
        
        # Генерация решения
        solution = self.generate_solution(json.dumps(task_data))
        if solution:
            # Отправка с автоматическими повторными попытками
            await self.submit_with_retry(solution)

    async def main_loop(self):
        """Основной цикл работы эмулятора"""
        self.is_running = True
        
        if not await self.register():
            logger.error("Не удалось зарегистрироваться")
            return

        # Запуск WebSocket обработчика
        websocket_task = asyncio.create_task(self.handle_websocket())
        
        while self.is_running:
            try:
                # Получение задания
                task = await self.get_task()
                if task and "content" in task:
                    # Случайная задержка 1-5 секунд
                    delay = random.uniform(1, 5)
                    await asyncio.sleep(delay)
                    
                    # Генерация и отправка решения
                    solution = self.generate_solution(task["content"])
                    if solution:
                        success = await self.submit_solution(solution)
                        if not success:
                            logger.info("Повторная попытка отправки решения...")
                            await asyncio.sleep(1)
                            await self.submit_solution(solution)
                
                await asyncio.sleep(1)  # Пауза между итерациями
                
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                await asyncio.sleep(1)

        # Отмена WebSocket задачи при остановке
        websocket_task.cancel()

    def stop(self):
        """Остановка эмулятора"""
        self.is_running = False
        logger.info("Эмулятор остановлен")

async def main():
    # Создаем несколько эмуляторов
    num_teams = 10  # Количество команд
    emulators = []
    
    for i in range(num_teams):
        emulator = ParticipantEmulator()
        emulators.append(emulator)
    
    try:
        # Запускаем все эмуляторы одновременно
        tasks = [emulator.main_loop() for emulator in emulators]
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        for emulator in emulators:
            emulator.stop()

if __name__ == "__main__":
    asyncio.run(main())
=======
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# === Настройки ===
API_URL = "http://localhost:8000"  # Адрес сервера
TEAM_NAME = "Команда_1"            # Имя команды
HEADERS = {}
MAX_RETRIES = 3                    # Максимальное количество попыток
RETRY_BACKOFF = 2                  # Множитель для увеличения времени между попытками

# === Настройка сессии с автоматическими повторами ===
def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_BACKOFF,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# === Регистрация команды и получение токена ===
def register_team():
    global HEADERS
    while True:
        try:
            session = create_session()
            response = session.post(f"{API_URL}/register", data={"name": TEAM_NAME})
            response.raise_for_status()
            token = response.json()["token"]
            HEADERS = {"Authorization": f"Bearer {token}"}
            print(f"[OK] Получен токен для команды '{TEAM_NAME}'")
            return
        except Exception as e:
            print(f"[Ошибка регистрации] {e}")
            print("[~] Повторная попытка через 5 секунд...")
            time.sleep(5)

# === Получение задания ===
def get_task():
    try:
        session = create_session()
        response = session.get(f"{API_URL}/task", headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        if "content" not in data:
            print("[!] Нет доступных заданий")
            return None, None
        return data["filename"], json.loads(data["content"])
    except requests.exceptions.ConnectionError:
        print("[!] Ошибка подключения к серверу")
        return None, None
    except Exception as e:
        print(f"[Ошибка получения задания] {e}")
        return None, None

# === Создание фейкового решения ===
def create_solution(task_json):
    task_json["selections"] = [{
        "type": "ЛОГИЧЕСКАЯ ОШИБКА",
        "startSelection": 5,
        "endSelection": 223
    }]
    filename = "solution.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(task_json, f, ensure_ascii=False, indent=2)
    return filename

# === Отправка решения ===
def send_solution(filepath):
    for attempt in range(MAX_RETRIES):
        try:
            session = create_session()
            with open(filepath, "rb") as f:
                response = session.post(f"{API_URL}/submit", headers=HEADERS, files={"file": f})
                response.raise_for_status()
                print(f"[OK] Решение отправлено: {response.json()}")
                return True
        except requests.exceptions.ConnectionError:
            print(f"[!] Попытка {attempt + 1}/{MAX_RETRIES}: Ошибка подключения")
        except Exception as e:
            print(f"[!] Попытка {attempt + 1}/{MAX_RETRIES}: {e}")
        
        if attempt < MAX_RETRIES - 1:
            wait_time = RETRY_BACKOFF ** attempt
            print(f"[~] Повторная попытка через {wait_time} сек...")
            time.sleep(wait_time)
    
    print("[X] Не удалось отправить решение после всех попыток")
    return False

# === Основной цикл работы эмулятора ===
def main_loop():
    consecutive_errors = 0
    while True:
        try:
            filename, task_json = get_task()
            if not task_json:
                wait_time = min(30 * (2 ** consecutive_errors), 300)  # Максимум 5 минут
                print(f"[=] Ждём {wait_time} секунд до следующей попытки\n")
                time.sleep(wait_time)
                consecutive_errors += 1
                continue

            consecutive_errors = 0
            print(f"[->] Получено задание: {filename}")

            delay = random.randint(1, 5)
            print(f"[~] Имитируем работу... ждём {delay} сек")
            time.sleep(delay)

            solution_path = create_solution(task_json)
            if send_solution(solution_path):
                print("[=] Ждём 30 секунд до следующего задания\n")
                time.sleep(30)
            else:
                print("[=] Ждём 10 секунд перед повторной попыткой\n")
                time.sleep(10)

        except Exception as e:
            print(f"[!] Неожиданная ошибка в главном цикле: {e}")
            time.sleep(5)

# === Точка входа ===
if __name__ == "__main__":
    while True:
        try:
            register_team()
            main_loop()
        except KeyboardInterrupt:
            print("\n[X] Работа эмулятора прервана пользователем")
            break
        except Exception as e:
            print(f"[!] Критическая ошибка: {e}")
            print("[~] Перезапуск эмулятора через 10 секунд...")
            time.sleep(10)
>>>>>>> d4064c07154b37cc68ec40159791ab6874354da3
