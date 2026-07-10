from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta

from .api import IrisApiClient
from .const import CONF_API_TOKEN, DOMAIN, SERVICE_SEND_COMMAND

PLATFORMS = [Platform.MEDIA_PLAYER, Platform.FAN, Platform.BUTTON]
SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
        vol.Required("command"): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    client = IrisApiClient(
        session,
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data.get(CONF_API_TOKEN) or None,
    )
    health = await client.async_get_health()
    devices = await client.async_get_devices()
    bridge_id = str(health.get("bridge_id") or entry.data.get("device_id") or entry.entry_id)
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, bridge_id)},
        name=entry.title,
        entry_type=dr.DeviceEntryType.SERVICE,
    )
    runtime = {
        "client": client,
        "devices": devices,
        "bridge_id": bridge_id,
        "entry": entry,
    }
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = runtime

    async def async_refresh_inventory(_now) -> None:
        try:
            refreshed = await client.async_get_devices()
        except Exception:  # The normal entity availability path handles bridge outages.
            return
        if refreshed != runtime["devices"]:
            runtime["devices"] = refreshed
            await hass.config_entries.async_reload(entry.entry_id)

    runtime["unsub_inventory"] = async_track_time_interval(
        hass, async_refresh_inventory, timedelta(seconds=30)
    )

    if not hass.services.has_service(DOMAIN, SERVICE_SEND_COMMAND):

        async def async_send_command(call: ServiceCall) -> None:
            device_id = call.data["device_id"]
            command = call.data["command"]
            entries: dict[str, dict[str, Any]] = hass.data.get(DOMAIN, {})
            for runtime in entries.values():
                if any(device.id == device_id for device in runtime["devices"]):
                    await runtime["client"].async_send_command(device_id, command)
                    return
            raise ValueError(f"IRIS device `{device_id}` is not configured")

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
        runtime = hass.data[DOMAIN].pop(entry.entry_id)
        runtime["unsub_inventory"]()
    return unload_ok
