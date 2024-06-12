import logging
from tuya_connector import TuyaOpenAPI
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

class TuyaAPI:
    def __init__(self, hass: HomeAssistant, access_id, access_secret, ir_remote_device_id):
        self.access_id = access_id
        self.access_secret = access_secret
        self.ir_remote_device_id = ir_remote_device_id
        self.hass = hass

        openapi = TuyaOpenAPI("https://openapi.tuyaus.com", access_id, access_secret)
        openapi.connect()
        self.openapi = openapi

    async def enable_learning_state(self, state):
        url = f"/v2.0/infrareds/{self.ir_remote_device_id}/learning-state"
        try:
            data = await self.hass.async_add_executor_job(self.openapi.put, url, {"state": state})
            if data.get("success"):
                _LOGGER.info(f"Learning state changed: {state}")
                return data.get("result")
            else:
                _LOGGER.warning(f"Failed to change learning state: {data}")
        except Exception as e:
            _LOGGER.error(f"Error changing learning state: {e}")
        return None

    async def get_learned_code(self, learning_time):
        url = f"/v2.0/infrareds/{self.ir_remote_device_id}/learning-codes?learning_time={learning_time}"
        try:
            data = await self.hass.async_add_executor_job(self.openapi.get, url)
            if data.get("success"):
                _LOGGER.info(f"Learned code retrieved")
                return data.get("result")
            else:
                _LOGGER.warning(f"Failed to retrieve learned code: {data}")
        except Exception as e:
            _LOGGER.error(f"Error retrieving learned code: {e}")
        return None

    async def save_learned_code(self, category_id, remote_name, code, key):
        url = f"/v2.0/infrareds/{self.ir_remote_device_id}/learning-codes"
        payload = {
            "category_id": category_id,
            "remote_name": remote_name,
            "codes": [{"code": code, "key": key}]
        }
        try:
            data = await self.hass.async_add_executor_job(self.openapi.post, url, payload)
            if data.get("success"):
                _LOGGER.info(f"Learned code saved successfully")
                return data.get("result")
            else:
                _LOGGER.warning(f"Failed to save learned code: {data}")
        except Exception as e:
            _LOGGER.error(f"Error saving learned code: {e}")
        return None

    async def send_learned_code(self, remote_id, code):
        url = f"/v2.0/infrareds/{self.ir_remote_device_id}/remotes/{remote_id}/learning-codes"
        payload = {"code": code}
        try:
            data = await self.hass.async_add_executor_job(self.openapi.post, url, payload)
            if data.get("success"):
                _LOGGER.info(f"Learned code sent successfully")
                return data.get("result")
            else:
                _LOGGER.warning(f"Failed to send learned code: {data}")
        except Exception as e:
            _LOGGER.error(f"Error sending learned code: {e}")
        return None
