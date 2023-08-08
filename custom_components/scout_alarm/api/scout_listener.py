import asyncio
import json
import logging

import pysher

from custom_components.scout_alarm.const import LOGGER

from .scout_session import ScoutSession


class ScoutListener:
    api_key = "baf06f5a867d462e09d4"

    def __init__(self, session: ScoutSession, loop):
        self.session = session
        self._loop = loop

        self.pusher = pysher.Pusher(self.api_key, log_level=logging.WARN)
        self.socket_id = None
        self._mode_handlers = []
        self._device_handlers = []
        self._locations = []

    async def async_connect(self):
        await self.__async_pusher_connect()

    async def async_add_location(self, location_id):
        self._locations.append(location_id)
        return await self.__async_subscribe_location(location_id)

    def on_mode_change(self, callback):
        self._mode_handlers.append(callback)

    def on_device_change(self, callback):
        self._device_handlers.append(callback)

    async def __async_subscribe_location(self, location_id):
        LOGGER.info(f"subscribing to location #{location_id}...")
        channel_name = f"private-{location_id}"
        channel_token = await self.session.async_get_channel_token(
            self.socket_id, channel_name
        )
        channel = self.pusher.subscribe(channel_name, auth=channel_token)

        def mode_change(payload):
            LOGGER.debug(f"mode changed: {payload}")
            data = json.loads(payload)
            for handler in self._mode_handlers:
                handler(data)

        def device_change(payload):
            LOGGER.debug(f"device change: {payload}")
            data = json.loads(payload)
            for handler in self._device_handlers:
                handler(data)

        channel.bind("mode", mode_change)
        channel.bind("device", device_change)

        LOGGER.info(f"subscribed to location #{location_id}")
        return channel

    def __async_pusher_connect(self):
        connected_future = asyncio.Future()

        def connect_handler(payload):
            data = json.loads(payload)
            self.socket_id = data["socket_id"]
            LOGGER.info(
                f"Connected to scout_alarm pusher with socket_id '{self.socket_id}'"
            )
            # re-subscribe to any locations we've already subscribed to (to handle reconnects)
            for location_id in self._locations:
                asyncio.run_coroutine_threadsafe(
                    self.__async_subscribe_location(location_id), self._loop
                )

            if not connected_future.done():
                connected_future.set_result(data["socket_id"])

        self.pusher.connection.bind("pusher:connection_established", connect_handler)
        self.pusher.connect()

        return connected_future
