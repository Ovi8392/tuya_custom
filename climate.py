import logging
from typing import Any, Dict

import voluptuous as vol
from pprint import pformat

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.components.climate.const import HVACMode
from homeassistant.const import UnitOfTemperature, STATE_UNKNOWN
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature

from .const import VALID_MODES
from .api import TuyaAPI

_LOGGER = logging.getLogger("tuya_hack")

# Define constants for configuration keys
ACCESS_ID = "access_id"
ACCESS_SECRET = "access_secret"
REMOTE_ID = "remote_id"
AC_ID = "ac_id"
NAME = "name"
SENSOR = "sensor"

# Schema for platform configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(ACCESS_ID): cv.string,
        vol.Required(ACCESS_SECRET): cv.string,
        vol.Required(REMOTE_ID): cv.string,
        vol.Required(AC_ID): cv.string,
        vol.Required(NAME): cv.string,
        vol.Required(SENSOR): cv.string,
    }
)

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Tuya thermostat platform."""
    _LOGGER.info("Setting up Tuya thermostat platform")
    climate_config = {
        "access_id": config[ACCESS_ID],
        "access_secret": config[ACCESS_SECRET],
        "remote_id": config[REMOTE_ID],
        "ac_id": config[AC_ID],
        "name": config[NAME],
        "sensor": config[SENSOR]
    }

    _LOGGER.debug(f"Platform configuration: {pformat(climate_config)}")
    add_entities([TuyaThermostat(climate_config, hass)])


class TuyaThermostat(ClimateEntity):
    """Representation of a Tuya Thermostat."""

    def __init__(self, climate: Dict[str, Any], hass: HomeAssistant) -> None:
        """Initialize the Tuya thermostat entity."""
        _LOGGER.info("Initializing Tuya thermostat")
        _LOGGER.debug(pformat(climate))
        self._api = TuyaAPI(
            hass,
            climate[ACCESS_ID],
            climate[ACCESS_SECRET],
            climate[AC_ID],
            climate[REMOTE_ID],
        )
        self._sensor_name = climate[SENSOR]
        self._name = climate[NAME]
        self.hass = hass

    @property
    def name(self) -> str:
        """Return the name of the thermostat."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the thermostat."""
        return f"tuya_thermostat_{self._api.thermostat_device_id}"

    @property
    def temperature_unit(self) -> str:
        """Return the unit of temperature measurement."""
        return UnitOfTemperature.CELSIUS

    @property
    def supported_features(self) -> int:
        """Return the supported features of the thermostat."""
        return (
            ClimateEntityFeature.TARGET_TEMPERATURE |
            ClimateEntityFeature.FAN_MODE
        )

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature that can be set."""
        return 15.0

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature that can be set."""
        return 30.0

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        sensor_state = self.hass.states.get(self._sensor_name)
        _LOGGER.debug(f"Current sensor state: {sensor_state}")
        if sensor_state and sensor_state.state != STATE_UNKNOWN:
            try:
                return float(sensor_state.state)
            except ValueError:
                _LOGGER.error(f"Invalid sensor state: {sensor_state.state}")
        return float(self._api._temperature) if self._api._temperature else None

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        return float(self._api._temperature) if self._api._temperature else None

    @property
    def hvac_mode(self) -> str | None:
        """Return current operation (heat, cool, idle)."""
        if self._api._power == "0":
            return HVACMode.OFF
        return VALID_MODES.get(str(self._api._mode), None)

    @property
    def hvac_modes(self) -> list[str]:
        """Return the list of available operation modes."""
        return list(VALID_MODES.values())

    @property
    def fan_mode(self) -> str | None:
        """Return the fan setting."""
        return (
            "Low" if self._api._wind == "1" else
            "Medium" if self._api._wind == "2" else
            "High" if self._api._wind == "3" else
            "Automatic" if self._api._wind == "0" else None
        )

    @property
    def fan_modes(self) -> list[str]:
        """Return the list of available fan modes."""
        return ["Low", "Medium", "High", "Automatic"]

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        _LOGGER.info(f"Setting fan mode to: {fan_mode}")
        command_map = {
            "Low": "1",
            "Medium": "2",
            "High": "3",
            "Automatic": "0",
        }
        if fan_mode in command_map:
            await self._api.send_command("wind", command_map[fan_mode])
        else:
            _LOGGER.warning(f"Invalid fan mode: {fan_mode}")

    async def async_update(self) -> None:
        """Update the state of the thermostat."""
        _LOGGER.info("Updating Tuya thermostat state")
        await self._api.async_update()
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get("temperature")
        if temperature is not None:
            _LOGGER.info(f"Setting target temperature to: {temperature}")
            await self._api.async_set_temperature(float(temperature))

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        """Set new target operation mode."""
        _LOGGER.info(f"Setting HVAC mode to: {hvac_mode}")
        for mode, mode_name in VALID_MODES.items():
            if hvac_mode == mode_name:
                if mode == "5":
                    await self._api.async_power_off()
                else:
                    if self._api._power == "0":
                        await self._api.async_power_on()
                    await self._api.async_set_hvac_mode(mode)
                break
        else:
            _LOGGER.warning(f"Invalid HVAC mode: {hvac_mode}")
