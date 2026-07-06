from __future__ import annotations

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import IrisApiClient, IrisProfile
from .const import CONF_DEVICE_ID, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            IrisMediaPlayer(
                entry,
                runtime["client"],
                runtime["profile"],
            )
        ]
    )


class IrisMediaPlayer(MediaPlayerEntity):
    _attr_device_class = MediaPlayerDeviceClass.TV
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        entry: ConfigEntry,
        client: IrisApiClient,
        profile: IrisProfile,
    ) -> None:
        self._entry = entry
        self._client = client
        self._profile = profile
        self._commands = set(profile.commands)
        self._attr_unique_id = str(entry.data.get(CONF_DEVICE_ID) or profile.id)
        self._attr_state = MediaPlayerState.OFF
        self._attr_supported_features = self._supported_features()
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._attr_unique_id)},
            "manufacturer": profile.brand.title(),
            "model": profile.model,
            "name": entry.data.get(CONF_NAME) or f"IRIS {profile.brand.title()} TV",
        }

    def _supported_features(self) -> MediaPlayerEntityFeature:
        features = MediaPlayerEntityFeature.TURN_ON | MediaPlayerEntityFeature.TURN_OFF
        if "volume_up" in self._commands:
            features |= MediaPlayerEntityFeature.VOLUME_STEP
        if "mute" in self._commands:
            features |= MediaPlayerEntityFeature.VOLUME_MUTE
        if "input" in self._commands:
            features |= MediaPlayerEntityFeature.SELECT_SOURCE
            self._attr_source_list = ["input"]
        return features

    async def async_turn_on(self) -> None:
        await self._send_first_available(("power_on", "power"))
        self._attr_state = MediaPlayerState.ON

    async def async_turn_off(self) -> None:
        await self._send_first_available(("power_off", "power"))
        self._attr_state = MediaPlayerState.OFF

    async def async_volume_up(self) -> None:
        await self._send_if_available("volume_up")

    async def async_volume_down(self) -> None:
        await self._send_if_available("volume_down")

    async def async_mute_volume(self, mute: bool) -> None:
        await self._send_if_available("mute")

    async def async_select_source(self, source: str) -> None:
        await self._send_if_available("input")

    async def _send_first_available(self, commands: tuple[str, ...]) -> None:
        for command in commands:
            if command in self._commands:
                await self._client.async_send_command(command)
                self.async_write_ha_state()
                return

    async def _send_if_available(self, command: str) -> None:
        if command in self._commands:
            await self._client.async_send_command(command)
            self.async_write_ha_state()
