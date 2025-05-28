<<<<<<< HEAD
from fastapi import WebSocket
from typing import Dict
import logging

=======
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Optional, Set
import asyncio
import json
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
>>>>>>> d4064c07154b37cc68ec40159791ab6874354da3
logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.active_teams: Set[str] = set()
        self.message_queue: Dict[str, list] = {}
        self.max_queue_size = 100
        self.heartbeat_interval = 30  # секунды

    async def connect(self, team_name: str, websocket: WebSocket):
        """
        Подключение нового WebSocket соединения
        """
        await websocket.accept()
<<<<<<< HEAD
        self.connections[team] = websocket
        logger.info(f"Team {team} connected. Total connections: {len(self.connections)}")

    def disconnect(self, team: str):
        if team in self.connections:
            del self.connections[team]
            logger.info(f"Team {team} disconnected. Total connections: {len(self.connections)}")

    async def send_message(self, team: str, message: str):
        if team in self.connections:
            try:
                await self.connections[team].send_text(message)
                logger.debug(f"Message sent to team {team}: {message}")
            except Exception as e:
                logger.error(f"Error sending message to team {team}: {str(e)}")
                self.disconnect(team)

    async def broadcast(self, message: str):
        logger.info(f"Broadcasting message to {len(self.connections)} connections: {message}")
        disconnected_teams = []
        for team, ws in self.connections.items():
            try:
                await ws.send_text(message)
                logger.debug(f"Broadcast message sent to team {team}")
            except Exception as e:
                logger.error(f"Error broadcasting to team {team}: {str(e)}")
                disconnected_teams.append(team)
        
        # Удаляем отключенные соединения
        for team in disconnected_teams:
            self.disconnect(team)
=======
        self.active_connections[team_name] = websocket
        self.active_teams.add(team_name)
        logger.info(f"Team {team_name} connected. Total active teams: {len(self.active_teams)}")
        
        # Отправляем накопленные сообщения, если они есть
        if team_name in self.message_queue:
            for message in self.message_queue[team_name]:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending queued message to team {team_name}: {e}")
            del self.message_queue[team_name]
        
        # Запускаем heartbeat для проверки соединения
        asyncio.create_task(self._heartbeat(team_name))

    async def disconnect(self, team_name: str):
        """
        Отключение WebSocket соединения
        """
        if team_name in self.active_connections:
            websocket = self.active_connections[team_name]
            try:
                await websocket.close()
            except Exception as e:
                logger.error(f"Error closing connection for team {team_name}: {e}")
            finally:
                del self.active_connections[team_name]
                self.active_teams.remove(team_name)
                logger.info(f"Team {team_name} disconnected. Total active teams: {len(self.active_teams)}")

    async def broadcast(self, message: str):
        """
        Отправка сообщения всем подключенным клиентам
        """
        disconnected_teams = set()
        for team_name, connection in self.active_connections.items():
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to {team_name}: {str(e)}")
                disconnected_teams.add(team_name)
                
        # Удаляем отключившиеся команды
        for team_name in disconnected_teams:
            await self.disconnect(team_name)
>>>>>>> d4064c07154b37cc68ec40159791ab6874354da3

    def _queue_message(self, team_name: str, message: str):
        """
        Сохранение сообщения в очередь для отправки позже
        :param team_name: Идентификатор команды
        :param message: Сообщение для сохранения
        """
        if team_name not in self.message_queue:
            self.message_queue[team_name] = []
        
        if len(self.message_queue[team_name]) < self.max_queue_size:
            self.message_queue[team_name].append(message)
            logger.debug(f"Message queued for offline team {team_name}")
        else:
            logger.warning(f"Message queue full for team {team_name}, dropping message")

    async def _heartbeat(self, team_name: str):
        """
        Периодическая проверка соединения
        :param team_name: Идентификатор команды
        """
        while team_name in self.active_connections:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                if team_name in self.active_connections:
                    await self.active_connections[team_name].send_text(
                        json.dumps({
                            "type": "ping",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    )
            except WebSocketDisconnect:
                logger.warning(f"Heartbeat failed for team {team_name}")
                await self.disconnect(team_name)
                break
            except Exception as e:
                logger.error(f"Heartbeat error for team {team_name}: {e}")
                await self.disconnect(team_name)
                break

# Создаем глобальный менеджер WebSocket соединений
ws_manager = WebSocketManager()
