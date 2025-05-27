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
logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.active_teams: Set[str] = set()
        self.message_queue: Dict[str, list] = {}
        self.max_queue_size = 100
        self.heartbeat_interval = 30  # секунды

    async def connect(self, team: str, websocket: WebSocket):
        """
        Подключение нового WebSocket соединения
        :param team: Идентификатор команды
        :param websocket: WebSocket соединение
        """
        try:
            await websocket.accept()
            self.connections[team] = websocket
            self.active_teams.add(team)
            logger.info(f"Team {team} connected successfully")
            
            # Отправляем накопленные сообщения, если они есть
            if team in self.message_queue:
                for message in self.message_queue[team]:
                    try:
                        await websocket.send_text(message)
                    except Exception as e:
                        logger.error(f"Error sending queued message to team {team}: {e}")
                del self.message_queue[team]
            
            # Запускаем heartbeat для проверки соединения
            asyncio.create_task(self._heartbeat(team))
            
        except Exception as e:
            logger.error(f"Error during connection for team {team}: {e}")
            await self.disconnect(team)
            raise

    async def disconnect(self, team: str, reason: Optional[str] = None):
        """
        Отключение WebSocket соединения
        :param team: Идентификатор команды
        :param reason: Причина отключения
        """
        if team in self.connections:
            try:
                await self.connections[team].close()
            except Exception as e:
                logger.error(f"Error closing connection for team {team}: {e}")
            finally:
                del self.connections[team]
                self.active_teams.discard(team)
                logger.info(f"Team {team} disconnected: {reason or 'Normal closure'}")

    async def send_message(self, team: str, message: str, queue_if_offline: bool = True):
        """
        Отправка сообщения команде
        :param team: Идентификатор команды
        :param message: Сообщение для отправки
        :param queue_if_offline: Сохранять ли сообщение, если команда оффлайн
        """
        if team in self.connections:
            try:
                await self.connections[team].send_text(message)
                logger.debug(f"Message sent to team {team}")
            except WebSocketDisconnect:
                logger.warning(f"WebSocket disconnected while sending message to team {team}")
                await self.disconnect(team, "WebSocket disconnected during message send")
                if queue_if_offline:
                    self._queue_message(team, message)
            except Exception as e:
                logger.error(f"Error sending message to team {team}: {e}")
                await self.disconnect(team, f"Error: {str(e)}")
                if queue_if_offline:
                    self._queue_message(team, message)
        elif queue_if_offline:
            self._queue_message(team, message)

    async def broadcast(self, message: str, exclude: Optional[Set[str]] = None):
        """
        Отправка сообщения всем подключенным клиентам
        :param message: Сообщение для отправки
        :param exclude: Множество команд, которым не нужно отправлять сообщение
        """
        exclude = exclude or set()
        disconnected_teams = []
        
        for team in self.active_teams - exclude:
            if team in self.connections:
                try:
                    await self.connections[team].send_text(message)
                except WebSocketDisconnect:
                    logger.warning(f"WebSocket disconnected while broadcasting to team {team}")
                    disconnected_teams.append((team, "WebSocket disconnected during broadcast"))
                except Exception as e:
                    logger.error(f"Error broadcasting to team {team}: {e}")
                    disconnected_teams.append((team, f"Error: {str(e)}"))
        
        # Отключаем команды с ошибками
        for team, reason in disconnected_teams:
            await self.disconnect(team, reason)

    def _queue_message(self, team: str, message: str):
        """
        Сохранение сообщения в очередь для отправки позже
        :param team: Идентификатор команды
        :param message: Сообщение для сохранения
        """
        if team not in self.message_queue:
            self.message_queue[team] = []
        
        if len(self.message_queue[team]) < self.max_queue_size:
            self.message_queue[team].append(message)
            logger.debug(f"Message queued for offline team {team}")
        else:
            logger.warning(f"Message queue full for team {team}, dropping message")

    async def _heartbeat(self, team: str):
        """
        Периодическая проверка соединения
        :param team: Идентификатор команды
        """
        while team in self.connections:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                if team in self.connections:
                    await self.connections[team].send_text(
                        json.dumps({
                            "type": "ping",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    )
            except WebSocketDisconnect:
                logger.warning(f"Heartbeat failed for team {team}")
                await self.disconnect(team, "Heartbeat check failed")
                break
            except Exception as e:
                logger.error(f"Heartbeat error for team {team}: {e}")
                await self.disconnect(team, f"Heartbeat error: {str(e)}")
                break

ws_manager = WebSocketManager()
