from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class IrisApiError(Exception):
    """Base IRIS API error."""


class IrisAuthError(IrisApiError):
    """Raised when IRIS rejects the configured token."""


@dataclass(frozen=True)
class IrisFanControls:
    power_on: str | None
    power_off: str | None
    oscillate: str | None
    presets: dict[str, str]


@dataclass(frozen=True)
class IrisDevice:
    id: str
    name: str
    profile: str
    brand: str
    model: str
    device_type: str
    commands: tuple[str, ...]
    fan: IrisFanControls | None = None

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> "IrisDevice":
        metadata = payload.get("home_assistant") or {}
        fan_payload = metadata.get("fan")
        fan = None
        if fan_payload:
            fan = IrisFanControls(
                power_on=fan_payload.get("power_on"),
                power_off=fan_payload.get("power_off"),
                oscillate=fan_payload.get("oscillate"),
                presets={str(k): str(v) for k, v in (fan_payload.get("presets") or {}).items()},
            )
        return cls(
            id=str(payload["id"]),
            name=str(payload.get("name") or payload["id"]),
            profile=str(payload.get("profile") or ""),
            brand=str(payload["brand"]),
            model=str(payload["model"]),
            device_type=str(payload.get("device_type", "tv")),
            commands=tuple(str(command) for command in payload.get("commands", [])),
            fan=fan,
        )


class IrisApiClient:
    def __init__(self, session: Any, host: str, port: int, token: str | None) -> None:
        self._session = session
        self._base_url = f"http://{host}:{port}"
        self._token = token

    async def async_get_health(self) -> dict[str, Any]:
        return await self._request("GET", "/health", auth=False)

    async def async_get_devices(self) -> tuple[IrisDevice, ...]:
        payload = await self._request("GET", "/devices")
        return tuple(IrisDevice.from_json(device) for device in payload.get("devices", []))

    async def async_send_command(self, device_id: str, command: str) -> None:
        await self._request("POST", f"/devices/{device_id}/send/{command}")

    async def _request(self, method: str, path: str, *, auth: bool = True) -> dict[str, Any]:
        headers = {}
        if auth and self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        async with self._session.request(method, f"{self._base_url}{path}", headers=headers) as response:
            if response.status == 401:
                raise IrisAuthError("invalid IRIS API token")
            if response.status >= 400:
                text = await response.text()
                raise IrisApiError(f"IRIS API returned {response.status}: {text}")
            return await response.json()
