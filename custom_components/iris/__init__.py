from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IrisApiClient
from .const import CONF_API_TOKEN, DOMAIN, SERVICE_SEND_COMMAND

PLATFORMS = [Platform.MEDIA_PLAYER, Platform.BUTTON]
SERVICE_SCHEMA = vol.Schema({vol.Required("command"): cv.string})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    client = IrisApiClient(
        session,
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data.get(CONF_API_TOKEN) or None,
    )
    profile = await client.async_get_profile()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "profile": profile,
    }

    if not hass.services.has_service(DOMAIN, SERVICE_SEND_COMMAND):

        async def async_send_command(call: ServiceCall) -> None:
            command = call.data["command"]
            entries: dict[str, dict[str, Any]] = hass.data.get(DOMAIN, {})
            for runtime in entries.values():
                await runtime["client"].async_send_command(command)

        hass.services.async_register(
            DOMAIN,
            SERVICE_SEND_COMMAND,
            async_send_command,
            schema=SERVICE_SCHEMA,
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
