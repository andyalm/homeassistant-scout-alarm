import json

import aiohttp

from custom_components.scout_alarm.const import LOGGER


class ScoutSession:
    base_url = "https://api.scoutalarm.com"

    def __init__(self, username, password) -> None:
        self._username = username
        self._password = password
        self._jwt = None

    async def async_get_token(self):
        if self._jwt is not None:
            return self._jwt

        self._jwt = await self.__get_fresh_jwt()
        return self._jwt

    async def async_get_channel_token(self, socket_id, channel_name):
        api_token = await self.async_get_token()
        headers = {
            "Authorization": api_token,
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        async with aiohttp.ClientSession() as http_session:
            async with http_session.post(
                f"{self.base_url}/auth/pusher",
                data=f"socket_id={socket_id}&channel_name={channel_name}",
                headers=headers,
            ) as response:
                LOGGER.debug(f"POST /auth/pusher returned {response.status}")
                return (await response.json())["auth"]

    async def __get_fresh_jwt(self):
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        body = {"email": self._username, "password": self._password}

        async with aiohttp.ClientSession() as http_session:
            async with http_session.post(
                f"{self.base_url}/auth", data=json.dumps(body), headers=headers
            ) as response:
                LOGGER.debug(f"POST /auth returned {response.status}")
                return (await response.json())["jwt"]
