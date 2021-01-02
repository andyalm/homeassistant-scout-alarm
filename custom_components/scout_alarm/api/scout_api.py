import aiohttp
import json

from custom_components.scout_alarm.const import LOGGER
from .scout_session import ScoutSession


class ScoutApi:
    def __init__(self, session: ScoutSession):
        self.session = session

    async def get_current_member(self):
        return await self.__http('GET', '/auth')

    async def get_member_locations(self, member_id):
        return await self.__http('GET', f'/members/{member_id}/locations')

    async def get_location_hub(self, location_id):
        return await self.__http('GET', f'/locations/{location_id}/hub')

    async def get_location_modes(self, location_id):
        return await self.__http('GET', f'/locations/{location_id}/modes')

    async def get_location_devices(self, location_id):
        return await self.__http('GET', f'/locations/{location_id}/devices')

    async def get_device(self, device_id):
        return await self.__http('GET', f'/devices/{device_id}')

    async def update_mode_state(self, mode_id, state):
        body = {
            'state': state
        }
        await self.__http('POST', f'/modes/{mode_id}', body=body)

    async def __http(self, method, path, body=None):
        jwt = await self.session.async_get_token()

        headers = {
            'Authorization': jwt,
            'Accept': 'application/json'
        }

        serialized_body = None
        if body is not None:
            serialized_body = json.dumps(body)
            headers['Content-Type'] = 'application/json'

        async with aiohttp.ClientSession() as http_session:
            async with http_session.request(method, f'{self.session.base_url}/{path}', headers=headers, data=serialized_body) as response:
                LOGGER.info(f'{method} {path} returned {response.status}')
                return await response.json()


class ScoutLocationApi:
    def __init__(self, api: ScoutApi):
        self.__api = api
        self.__current_member = None
        self.__current_location = None

    async def get_modes(self):
        location = await self.get_current_location()
        return await self.__api.get_location_modes(location['id'])

    async def get_devices(self):
        location = await self.get_current_location()
        return await self.__api.get_location_devices(location['id'])

    async def get_device(self, device_id):
        return await self.__api.get_device(device_id)

    async def get_current_location(self):
        if self.__current_location is not None:
            return self.__current_location

        current_member = await self.__async_current_member()
        locations = await self.__api.get_member_locations(current_member['id'])
        # TODO support multiple locations
        self.__current_location = locations[0]
        return self.__current_location

    async def update_mode_state(self, mode_id, state):
        await self.__api.update_mode_state(mode_id, state)

    async def __async_current_member(self):
        if self.__current_member is not None:
            return self.__current_member

        self.__current_member = await self.__api.get_current_member()
        return self.__current_member
