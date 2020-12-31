from .scout_session import ScoutSession
from custom_components.scout_alarm.const import LOGGER
import pysher
import asyncio
import json


class ScoutListener:
    api_key = "baf06f5a867d462e09d4"

    def __init__(self, session: ScoutSession):
        self.session = session
        self.pusher = pysher.Pusher(self.api_key)
        self.socket_id = None
        self._mode_handlers = []

    async def async_connect(self):
        await self.__async_pusher_connect()

    async def async_add_location(self, location_id):
        channel_name = f'private-{location_id}'
        channel_token = await self.session.async_get_channel_token(self.socket_id, channel_name)
        channel = self.pusher.subscribe(channel_name, auth=channel_token)

        def mode_change(payload):
            LOGGER.info(f"mode changed: {payload}")
            data = json.loads(payload)
            for handler in self._mode_handlers:
                handler(data)

        channel.bind('mode', mode_change)

        return channel

    def on_mode_change(self, callback):
        self._mode_handlers.append(callback)

    def __async_pusher_connect(self):
        connected_future = asyncio.Future()

        def connect_handler(payload):
            data = json.loads(payload)
            self.socket_id = data['socket_id']
            LOGGER.info(f"Connected to scout_alarm pusher with socket_id '{self.socket_id}'")
            if not connected_future.done():
                connected_future.set_result(data['socket_id'])

        self.pusher.connection.bind('pusher:connection_established', connect_handler)
        self.pusher.connect()

        return connected_future
