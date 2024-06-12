import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .tuya_api import TuyaAPI

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    if "tuya_ir" in config:
        tuya_config = config["tuya_ir"]
        access_id = tuya_config.get("access_id")
        access_secret = tuya_config.get("access_secret")
        ir_remote_device_id = tuya_config.get("ir_remote_device_id")

        tuya_api = TuyaAPI(hass, access_id, access_secret, ir_remote_device_id)

        async def handle_enable_learning_state(call):
            _LOGGER.debug("Handling enable_learning_state service call")
            state = call.data.get("state")
            _LOGGER.debug(f"State parameter: {state}")

            await tuya_api.enable_learning_status(state)
        
        async def handle_get_learned_code(service_call):
            learning_time = service_call.data.get('learning_time')
            _LOGGER.debug(f"Fetching learned IR code at learning time: {learning_time}")
            learned_code = await tuya_api.get_learned_ir_code(learning_time)
            _LOGGER.info(f"Learned code: {learned_code}")

        async def handle_save_learned_code(service_call):
            category_id = service_call.data.get('category_id')
            remote_name = service_call.data.get('remote_name')
            code = service_call.data.get('code')
            key = service_call.data.get('key')
            _LOGGER.debug(f"Saving learned code: category_id={category_id}, remote_name={remote_name}, code={code}, key={key}")
            await tuya_api.save_learned_ir_code(category_id, remote_name, code, key)

        async def handle_send_learned_code(service_call):
            remote_id = service_call.data.get('remote_id')
            code = service_call.data.get('code')
            key = service_call.data.get('key')
            learned_code = service_call.data.get('learned_code')  # Adding 'learned_code' parameter
            _LOGGER.debug(f"Sending learned code to remote_id={remote_id}: {code}")
            await tuya_api.save_learned_ir_code(remote_id, code, key, learned_code)

        hass.services.async_register("tuya_ir", "enable_learning_state", handle_enable_learning_state)
        hass.services.async_register("tuya_ir", "get_learned_code", handle_get_learned_code)
        hass.services.async_register("tuya_ir", "save_learned_code", handle_save_learned_code)
        hass.services.async_register("tuya_ir", "send_learned_code", handle_send_learned_code)

        return True

    return False
