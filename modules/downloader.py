import os
import json
from telethon import TelegramClient
from telethon.errors import MessageIdInvalidError
from telethon.tl.custom.message import Message
from typing import Optional

class TelegramMediaDownloader:
    def __init__(self, config_path: str = 'config.json', session_file: str = 'tg.session', media_folder: str = 'media'):
        self.config_path = config_path
        self.session_file = session_file
        self.media_folder = media_folder
        self.client: Optional[TelegramClient] = None
        self._config = None

    async def startup(self):
        with open(self.config_path, 'r') as f:
            self._config = json.load(f)
        self.client = TelegramClient(self.session_file, self._config['api_id'], self._config['api_hash'])
        await self.client.start()

    async def download_media(self, channel: str, message_id: int) -> Optional[str]:
        channel_path = os.path.join(self.media_folder, channel)
        os.makedirs(channel_path, exist_ok=True)
        try:
            message: Message = await self.client.get_messages(channel, ids=message_id)
            if not message or not message.media:
                return None
            path = await self.client.download_media(message, file=channel_path)
            # path_split = path.split(os.sep)
            # path = os.sep.join(path_split[0,-2]) + os.sep + path_split[-1].lower()
            # print(f"::: downloaded to message.media: {message}, downloaded to path: {path}")
            return path if path else None
        except MessageIdInvalidError:
            return None
        except Exception as e:
            print(f"[ERR] download media: {e}")
            return None

    def delete_media(self, filename: str) -> bool:
        # file_path = os.path.join(self.media_folder, filename)
        try:
            if os.path.exists(filename):
                os.remove(filename)
                return True
            return False
        except Exception as e:
            print(f"[ERR] delete media: {e}")
            return False
