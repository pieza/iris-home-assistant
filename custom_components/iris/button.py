from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import IrisApiClient, IrisProfile
from .command_buttons import REMOTE_BUTTONS, RemoteButtonDescription
from .const import CONF_DEVICE_ID, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime = hass.data[DOMAIN][entry.entry_id]
    profile = runtime["profile"]
    commands = set(profile.commands)
    async_add_entities(
        [
            IrisCommandButton(entry, runtime["client"], profile, description)
            for description in REMOTE_BUTTONS
            if description.command in commands
        ]
    )


class IrisCommandButton(ButtonEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        client: IrisApiClient,
        profile: IrisProfile,
        description: RemoteButtonDescription,
    ) -> None:
        self._client = client
        self._description = description
        device_id = str(entry.data.get(CONF_DEVICE_ID) or profile.id)
        self._attr_name = description.name
        self._attr_unique_id = f"{device_id}_{description.command}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "manufacturer": profile.brand.title(),
            "model": profile.model,
            "name": entry.data.get(CONF_NAME) or f"IRIS {profile.brand.title()} TV",
        }

    async def async_press(self) -> None:
        await self._client.async_send_command(self._description.command)
