import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
import voluptuous as vol
from .tuya_api import TuyaAPI

_LOGGER = logging.getLogger(__name__)

DOMAIN = "tuya_custom"

CONF_ACCESS_ID = "access_id"
CONF_ACCESS_SECRET = "access_secret"
CONF_IR_REMOTE_DEVICE_ID = "ir_remote_device_id"
CONF_REMOTE_ID = "remote_id"

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_ACCESS_ID): cv.string,
        vol.Required(CONF_ACCESS_SECRET): cv.string,
        vol.Required(CONF_IR_REMOTE_DEVICE_ID): cv.string,
        vol.Required(CONF_REMOTE_ID): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: ConfigType):
    conf = config[DOMAIN]
    access_id = conf[CONF_ACCESS_ID]
    access_secret = conf[CONF_ACCESS_SECRET]
    ir_remote_device_id = conf[CONF_IR_REMOTE_DEVICE_ID]
    remote_id = conf[CONF_REMOTE_ID]

    tuya_api = TuyaAPI(hass, access_id, access_secret, ir_remote_device_id, remote_id)

    async def handle_enable_learning_status(call):
        state = call.data.get("state", True)
        await tuya_api.enable_learning_status(state)

    async def handle_get_learned_ir_code(call):
        learning_time = call.data.get("learning_time")
        await tuya_api.get_learned_ir_code(learning_time)

    async def handle_save_learned_ir_code(call):
        category_id = call.data.get("category_id")
        remote_name = call.data.get("remote_name")
        key_name = call.data.get("key_name")
        learned_code = call.data.get("learned_code")
        await tuya_api.save_learned_ir_code(category_id, remote_name, key_name, learned_code)

    async def handle_get_remote_keys(call):
        await tuya_api.get_remote_keys()

    async def handle_send_standard_command(call):
        category_id = call.data.get("category_id")
        remote_index = call.data.get("remote_index")
        key = call.data.get("key")
        await tuya_api.send_standard_command(category_id, remote_index, key)

    async def handle_send_key_command(call):
        category_id = call.data.get("category_id")
        key_id = call.data.get("key_id")
        key = call.data.get("key")
        await tuya_api.send_key_command(category_id, key_id, key)

    hass.services.async_register(DOMAIN, "enable_learning_status", handle_enable_learning_status)
    hass.services.async_register(DOMAIN, "get_learned_ir_code", handle_get_learned_ir_code)
    hass.services.async_register(DOMAIN, "save_learned_ir_code", handle_save_learned_ir_code)
    hass.services.async_register(DOMAIN, "get_remote_keys", handle_get_remote_keys)
    hass.services.async_register(DOMAIN, "send_standard_command", handle_send_standard_command)
    hass.services.async_register(DOMAIN, "send_key_command", handle_send_key_command)

    return True
