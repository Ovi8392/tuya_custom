from tuya_connector import TuyaOpenAPI
from .const import VALID_MODES
from homeassistant.core import HomeAssistant
import logging
from pprint import pformat

_LOGGER = logging.getLogger("tuya_hack")

class TuyaAPI:
    """
    Interface to interact with Tuya devices.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        access_id,
        access_secret,
        thermostat_device_id,
        ir_remote_device_id,
    ):
        """
        Initialize Tuya API.
        """
        self.access_id = access_id
        self.access_secret = access_secret
        self.thermostat_device_id = thermostat_device_id
        self.ir_remote_device_id = ir_remote_device_id
        self.hass = hass

        """
        Change address according used server.
        China Data Center    https://openapi.tuyacn.com
        *** Western America Data Center    https://openapi.tuyaus.com
        Eastern America Data Center    https://openapi-ueaz.tuyaus.com
        Central Europe Data Center    https://openapi.tuyaeu.com
        Western Europe Data Center    https://openapi-weaz.tuyaeu.com
        India Data Center    https://openapi.tuyain.com
        """
        openapi = TuyaOpenAPI("https://openapi.tuyaus.com", access_id, access_secret)
        openapi.connect()
        self.openapi = openapi

        self._temperature = "0"
        self._mode = "0"
        self._power = "0"
        self._wind = "0"

    async def async_init(self):
        """
        Asynchronously initialize Tuya API.
        """
        await self.async_update()

    async def async_update(self):
        """
        Asynchronously update status from the device.
        """
        status = await self.get_status()
        if status:
            self._temperature = status.get("temp")
            self._mode = status.get("mode")
            self._power = status.get("power")
            self._wind = status.get("wind")
        _LOGGER.info(f"ASYNC_UPDATE: {status}")

    async def async_set_fan_speed(self, fan_speed):
        """
        Asynchronously set fan speed.
        """
        _LOGGER.info(f"Setting fan speed to {fan_speed}")
        await self.send_command("wind", str(fan_speed))

    async def async_set_temperature(self, temperature):
        """
        Asynchronously set temperature.
        """
        _LOGGER.info(f"Setting temperature to {temperature}")
        await self.send_command("temp", str(temperature))

    async def async_power_on(self):
        """
        Asynchronously turn on the device.
        """
        _LOGGER.info("Turning on")
        await self.send_command("power", "1")

    async def async_power_off(self):
        """
        Asynchronously turn off the device.
        """
        _LOGGER.info("Turning off")
        await self.send_command("power", "0")

    async def async_set_hvac_mode(self, hvac_mode):
        """
        Asynchronously set HVAC mode.
        """
        _LOGGER.info(f"Setting HVAC mode to {hvac_mode}")
        await self.send_command("mode", str(hvac_mode))

    async def get_status(self):
        """
        Asynchronously fetch device status.
        """
        url = f"/v2.0/infrareds/{self.ir_remote_device_id}/remotes/{self.thermostat_device_id}/ac/status"
        _LOGGER.info(f"Fetching status from URL: {url}")
        try:
            data = await self.hass.async_add_executor_job(self.openapi.get, url)
            _LOGGER.debug(f"Full response data: {pformat(data)}")
            if data.get("success"):
                _LOGGER.info(f"GET_STATUS: {data.get('result')}")
                return data.get("result")
            else:
                _LOGGER.warning(f"Failed to fetch status: {data}")
        except Exception as e:
            _LOGGER.error(f"Error fetching status: {e}")
        return None

    async def send_command(self, code, value):
        """
        Asynchronously send command to the device.
        """
        url = f"/v2.0/infrareds/{self.ir_remote_device_id}/air-conditioners/{self.thermostat_device_id}/command"
        _LOGGER.info(f"Sending command to URL: {url}")
        _LOGGER.info(f"SEND_COMMAND_CODE_THEN_VAL: {code} {value}")
        try:
            data = await self.hass.async_add_executor_job(
                self.openapi.post,
                url,
                {
                    "code": code,
                    "value": value,
                },
            )
            _LOGGER.debug(f"Full response data: {pformat(data)}")
            if data.get("success"):
                _LOGGER.info(f"Command {code} with value {value} sent successfully")
            else:
                _LOGGER.warning(f"Failed to send command {code} with value {value}: {data}")
            return data
        except Exception as e:
            _LOGGER.error(f"Error sending command: {e}")
            return False

    async def enable_learning_state(self, enable: bool):
        """
        Enable or disable the learning state of the device.
        """
        url = f"/v2.0/infrareds/{self.ir_remote_device_id}/learning-state?state={str(enable).lower()}"
        _LOGGER.info(f"Setting learning state to {enable} for device ID: {self.ir_remote_device_id}")
        try:
            data = await self.hass.async_add_executor_job(self.openapi.put, url, {})
            _LOGGER.debug(f"Full response data: {pformat(data)}")
            if data.get("success"):
                _LOGGER.info(f"Learning state set to {enable} successfully")
                return data.get("result")
            else:
                _LOGGER.warning(f"Failed to set learning state: {data}")
        except Exception as e:
            _LOGGER.error(f"Error setting learning state: {e}")
        return None

    async def get_learned_code(self, learning_time: int):
        """
        Get the learned IR code from the device.
        """
        url = f"/v2.0/infrareds/{self.ir_remote_device_id}/learning-codes?learning_time={learning_time}"
        _LOGGER.info(f"Fetching learned code for device ID: {self.ir_remote_device_id} at time: {learning_time}")
        try:
            data = await self.hass.async_add_executor_job(self.openapi.get, url)
            _LOGGER.debug(f"Full response data: {pformat(data)}")
            if data.get("success"):
                _LOGGER.info(f"Learned code fetched successfully: {data.get('result')}")
                return data.get("result")
            else:
                _LOGGER.warning(f"Failed to fetch learned code: {data}")
        except Exception as e:
            _LOGGER.error(f"Error fetching learned code: {e}")
        return None

    async def save_learned_code(self, category_id, remote_name, code, key):
        """
        Save the learned IR code and generate a DIY remote control.
        """
        url = f"/v2.0/infrareds/{self.ir_remote_device_id}/learning-codes"
        payload = {
            "category_id": category_id,
            "remote_name": remote_name,
            "codes": [
                {
                    "code": code,
                    "key": key
                }
            ]
        }
        _LOGGER.info(f"Saving learned code for device ID: {self.ir_remote_device_id} with payload: {payload}")
        try:
            data = await self.hass.async_add_executor_job(self.openapi.post, url, payload)
            _LOGGER.debug(f"Full response data: {pformat(data)}")
            if data.get("success"):
                _LOGGER.info(f"Learned code saved successfully: {data.get('result')}")
                return data.get("result")
            else:
                _LOGGER.warning(f"Failed to save learned code: {data}")
        except Exception as e:
            _LOGGER.error(f"Error saving learned code: {e}")
        return None

    async def get_saved_learning_codes(self, remote_id: str):
        """
        Get the learning codes saved by a specified remote control.
        """
        url = f"/v2.0/infrareds/{self.ir_remote_device_id}/remotes/{remote_id}/learning-codes"
        _LOGGER.info(f"Fetching saved learning codes for remote ID: {remote_id}")
        try:
            data = await self.hass.async_add_executor_job(self.openapi.get, url)
            _LOGGER.debug(f"Full response data: {pformat(data)}")
            if data.get("success"):
                _LOGGER.info(f"Saved learning codes fetched successfully: {data.get('result')}")
                return data.get("result")
            else:
                _LOGGER.warning(f"Failed to fetch saved learning codes: {data}")
        except Exception as e:
            _LOGGER.error(f"Error fetching saved learning codes: {e}")
        return None

    async def send_learned_code(self, remote_id: str, code: str):
        """
        Send the learned IR code to a specified remote control.
        """
        url = f"/v2.0/infrareds/{self.ir_remote_device_id}/remotes/{remote_id}/learning-codes"
        payload = {"code": code}
        _LOGGER.info(f"Sending learned code for remote ID: {remote_id} with code: {code}")
        try:
            data = await self.hass.async_add_executor_job(self.openapi.post, url, payload)
            _LOGGER.debug(f"Full response data: {pformat(data)}")
            if data.get("success"):
                _LOGGER.info(f"Learned code sent successfully")
                return data.get("result")
            else:
                _LOGGER.warning(f"Failed to send learned code: {data}")
        except Exception as e:
            _LOGGER.error(f"Error sending learned code: {e}")
        return None