from tuya_connector import TuyaOpenAPI
from homeassistant.core import HomeAssistant
import logging
from pprint import pformat

_LOGGER = logging.getLogger(__name__)

class TuyaAPI:
    def __init__(self, hass: HomeAssistant, access_id, access_secret, ir_remote_device_id, remote_id):
        self.access_id = access_id
        self.access_secret = access_secret
        self.ir_remote_device_id = ir_remote_device_id
        self.remote_id = remote_id
        self.hass = hass
        self.openapi = TuyaOpenAPI("https://openapi.tuyaus.com", self.access_id, self.access_secret)

    async def enable_learning_status(self, state=True):
        url = f"/v2.0/infrareds/{self.ir_remote_device_id}/learning-state?state={state}"
        _LOGGER.info(f"Enabling learning status: {state}")
        return await self._api_request(url, method="PUT")

    async def get_learned_ir_code(self, learning_time):
        url = f"/v2.0/infrareds/{self.ir_remote_device_id}/learning-codes?learning_time={learning_time}"
        _LOGGER.info(f"Fetching learned IR code at time: {learning_time}")
        return await self._api_request(url)

    async def save_learned_ir_code(self, category_id, remote_name, key_name, learned_code):
        url = f"/v2.0/infrareds/{self.ir_remote_device_id}/learning-codes"
        data = {
            "category_id": category_id,
            "remote_name": remote_name,
            "codes": [
                {
                    "code": learned_code,
                    "key_name": key_name
                }
            ]
        }
        _LOGGER.info("Saving learned IR code")
        return await self._api_request(url, method="POST", data=data)

    #async def get_remote_keys(self):
    #    url = f"/v2.0/infrareds/{self.ir_remote_device_id}/remotes/{self.remote_id}/keys"
    #    _LOGGER.info(f"Fetching keys for remote control: {self.remote_id}")
    #    return await self._api_request(url)
        
    async def get_remote_keys(self):
    #    url = f"/v2.0/infrareds/8/base-key?lang=en"
        url = f"/v2.0/infrareds/{self.ir_remote_device_id}/remotes/{self.remote_id}/keys"
        _LOGGER.info(f"Fetching keys for remote control: {self.remote_id}")
        return await self._api_request(url)

    async def send_standard_command(self, category_id, remote_index, key):
        url = f"/v2.0/infrareds/{self.ir_remote_device_id}/remotes/{self.remote_id}/command"
        data = {
            "categoryId": category_id,
            "remoteIndex": remote_index,
            "key": key
        }
        _LOGGER.info(f"Sending standard command '{key}' to remote: {self.remote_id}")
        return await self._api_request(url, method="POST", data=data)

    async def send_key_command(self, category_id, key_id=None, key=None):
        url = f"/v2.0/infrareds/{self.ir_remote_device_id}/remotes/{self.remote_id}/raw/command"
        data = {
            "category_id": category_id,
            "key_id": key_id,
            "key": key
        }
        _LOGGER.info(f"Sending key command '{key}' to remote: {self.remote_id}")
        return await self._api_request(url, method="POST", data=data)

    async def _api_request(self, url, method="GET", data=None):
        await self.hass.async_add_executor_job(self.openapi.connect)

        try:
            if method == "GET":
                response = await self.hass.async_add_executor_job(self.openapi.get, url)
            elif method == "POST":
                response = await self.hass.async_add_executor_job(self.openapi.post, url, data)
            elif method == "PUT":
                response = await self.hass.async_add_executor_job(self.openapi.put, url)
            else:
                _LOGGER.error(f"Unsupported HTTP method: {method}")
                return None
            _LOGGER.info(f"API response: {pformat(response)}")
            return response
        except Exception as e:
            _LOGGER.error(f"API request error: {str(e)}")
            return None
