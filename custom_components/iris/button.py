from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import IrisApiClient, IrisDevice
from .command_buttons import FAN_BUTTONS, REMOTE_BUTTONS, RemoteButtonDescription
from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    runtime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            IrisCommandButton(runtime["client"], device, runtime["bridge_id"], description)
            for device in runtime["devices"]
            for description in _button_descriptions(device)
            if description.command in device.commands
        ]
    )


def _button_descriptions(device: IrisDevice) -> tuple[RemoteButtonDescription, ...]:
    if device.device_type == "tv":
        return REMOTE_BUTTONS
    if device.device_type == "fan":
        return FAN_BUTTONS
    return ()


class IrisCommandButton(ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, client: IrisApiClient, device: IrisDevice, bridge_id: str, description: RemoteButtonDescription) -> None:
        self._client = client
        self._device = device
        self._description = description
        device_key = f"{bridge_id}:{device.id}"
        self._attr_name = description.name
        self._attr_unique_id = f"{device_key}:{description.command}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_key)},
            "manufacturer": device.brand.title(),
            "model": device.model,
            "name": device.name,
            "via_device": (DOMAIN, bridge_id),
        }

    async def async_press(self) -> None:
        await self._client.async_send_command(self._device.id, self._description.command)
