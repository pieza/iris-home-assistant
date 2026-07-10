from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IrisApiClient, IrisApiError
from .const import (
    CONF_API_TOKEN,
    CONF_DEVICE_ID,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DOMAIN,
)


class IrisConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    def __init__(self) -> None:
        self._discovery: dict[str, Any] = {}

    async def async_step_zeroconf(self, discovery_info: Any) -> FlowResult:
        properties = dict(discovery_info.properties or {})
        host = str(discovery_info.host)
        port = int(discovery_info.port or DEFAULT_PORT)
        name = str(properties.get("name") or discovery_info.name or DEFAULT_NAME)
        device_id = str(properties.get("id") or discovery_info.name or host)

        await self.async_set_unique_id(device_id)
        self._abort_if_unique_id_configured(updates={CONF_HOST: host, CONF_PORT: port})

        self._discovery = {
            CONF_HOST: host,
            CONF_PORT: port,
            CONF_NAME: name,
            CONF_DEVICE_ID: device_id,
        }
        self.context["title_placeholders"] = {CONF_NAME: name}
        return await self.async_step_user()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        defaults = {
            CONF_HOST: self._discovery.get(CONF_HOST, ""),
            CONF_PORT: self._discovery.get(CONF_PORT, DEFAULT_PORT),
            CONF_NAME: self._discovery.get(CONF_NAME, DEFAULT_NAME),
            CONF_API_TOKEN: "",
        }

        if user_input is not None:
            data = {**self._discovery, **user_input}
            try:
                bridge_id = await self._validate_input(data)
            except IrisApiError:
                errors["base"] = "cannot_connect"
            else:
                device_id = str(data.get(CONF_DEVICE_ID) or bridge_id)
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_configured()
                data[CONF_DEVICE_ID] = device_id
                return self.async_create_entry(
                    title=str(data.get(CONF_NAME) or "IRIS Hub"),
                    data=data,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=defaults[CONF_HOST]): str,
                    vol.Required(CONF_PORT, default=defaults[CONF_PORT]): int,
                    vol.Required(CONF_NAME, default=defaults[CONF_NAME]): str,
                    vol.Required(CONF_API_TOKEN, default=defaults[CONF_API_TOKEN]): str,
                }
            ),
            errors=errors,
        )

    async def _validate_input(self, data: dict[str, Any]):
        session = async_get_clientsession(self.hass)
        token = str(data.get(CONF_API_TOKEN) or "")
        client = IrisApiClient(
            session,
            str(data[CONF_HOST]),
            int(data[CONF_PORT]),
            token or None,
        )
        health = await client.async_get_health()
        await client.async_get_devices()
        return str(health.get("bridge_id") or health.get("device_id") or data[CONF_HOST])


async def async_migrate_entry(hass, config_entry) -> bool:
    """Keep existing single-device entries as the IRIS hub entry."""
    if config_entry.version < 2:
        hass.config_entries.async_update_entry(config_entry, version=2)
    return True
