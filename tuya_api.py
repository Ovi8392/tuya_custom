from tuya_connector import TuyaOpenAPI
from homeassistant.core import HomeAssistant
import logging
from pprint import pformat

_LOGGER = logging.getLogger(__name__)

class TuyaAPI:
    """
    Interface to interact with Tuya devices.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        access_id,
        access_secret,
        ir_remote_device_id,
    ):
        """
        Initialize Tuya API.
        """
        self.access_id = access_id
        self.access_secret = access_secret
        self.ir_remote_device_id = ir_remote_device_id
        self.hass = hass
        self.openapi = None

    async def enable_learning_status(self, state=True):
        """
        Enable the learning status.
        """
        url = f"/v2.0/infrareds/{self.ir_remote_device_id}/learning-state?state={state}"
        _LOGGER.info(f"Enabling learning status: {state}")
        return await self._api_request(url, method="PUT")

    async def get_learned_ir_code(self, learning_time):
        """
        Get the learned IR code.
        """
        url = f"/v2.0/infrareds/{self.ir_remote_device_id}/learning-codes?learning_time={learning_time}"
        _LOGGER.info(f"Fetching learned IR code at time: {learning_time}")
        return await self._api_request(url)

    async def save_learned_ir_code(self, category_id, remote_name, key_name, learned_code):
        """
        Save the learned IR code.
        """
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

    async def _api_request(self, url, method="GET", data=None):
        """
        Make API request.
        """
        if self.openapi is None:
            self.openapi = TuyaOpenAPI("https://openapi.tuyaus.com", self.access_id, self.access_secret)
            await self.hass.async_add_executor_job(self.openapi.connect)
        try:
            if method == "GET":
                response = await self.hass.async_add_executor_job(self.openapi.get, url)
            elif method == "POST":
                response = await self.hass.async_add_executor_job(self.openapi.post, url, data)
            elif method == "PUT":
                response = await self.hass.async_add_executor_job(self.openapi.put, url)
            else:
                raise ValueError("Unsupported HTTP method")
            _LOGGER.debug(f"API response: {pformat(response)}")
            return response
        except Exception as e:
            _LOGGER.error(f"Error making API request: {e}")
            return None
