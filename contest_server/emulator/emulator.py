import requests
import time
import random
import json
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
