from __future__ import annotations

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import IrisApiClient, IrisDevice
from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    runtime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            IrisFan(runtime["client"], device, runtime["bridge_id"])
            for device in runtime["devices"]
            if device.device_type == "fan"
        ]
    )


class IrisFan(FanEntity):
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, client: IrisApiClient, device: IrisDevice, bridge_id: str) -> None:
        self._client = client
        self._device = device
        self._fan = device.fan
        self._attr_unique_id = f"{bridge_id}:{device.id}"
        self._attr_is_on = False
        features = FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
        if self._fan and self._fan.presets:
            features |= FanEntityFeature.PRESET_MODE
            self._attr_preset_modes = list(self._fan.presets)
        if self._fan and self._fan.oscillate:
            features |= FanEntityFeature.OSCILLATE
            self._attr_oscillating = False
        self._attr_supported_features = features
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._attr_unique_id)},
            "manufacturer": device.brand.title(),
            "model": device.model,
            "name": device.name,
            "via_device": (DOMAIN, bridge_id),
        }

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        await self._send_first_available(self._fan.power_on if self._fan else None, "power_on", "power")
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        await self._send_first_available(self._fan.power_off if self._fan else None, "power_off", "power")
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if not self._fan or preset_mode not in self._fan.presets:
            return
        await self._client.async_send_command(self._device.id, self._fan.presets[preset_mode])
        self._attr_preset_mode = preset_mode
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_oscillate(self, oscillating: bool) -> None:
        if (
            not self._fan
            or not self._fan.oscillate
            or self._fan.oscillate not in self._device.commands
            or oscillating == self._attr_oscillating
        ):
            return
        await self._client.async_send_command(self._device.id, self._fan.oscillate)
        self._attr_oscillating = oscillating
        self.async_write_ha_state()

    async def _send_first_available(self, *commands: str | None) -> None:
        available = set(self._device.commands)
        for command in commands:
            if command and command in available:
                await self._client.async_send_command(self._device.id, command)
                return
