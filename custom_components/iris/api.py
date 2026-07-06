from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class IrisApiError(Exception):
    """Base IRIS API error."""


class IrisAuthError(IrisApiError):
    """Raised when IRIS rejects the configured token."""


@dataclass(frozen=True)
class IrisProfile:
    id: str
    brand: str
    model: str
    device_type: str
    commands: tuple[str, ...]

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> "IrisProfile":
        return cls(
            id=str(payload["id"]),
            brand=str(payload["brand"]),
            model=str(payload["model"]),
            device_type=str(payload.get("device_type", "tv")),
            commands=tuple(str(command) for command in payload.get("commands", [])),
        )


class IrisApiClient:
    def __init__(
        self,
        session: Any,
        host: str,
        port: int,
        token: str | None,
    ) -> None:
        self._session = session
        self._base_url = f"http://{host}:{port}"
        self._token = token

    async def async_get_health(self) -> dict[str, Any]:
        return await self._request("GET", "/health", auth=False)

    async def async_get_profile(self) -> IrisProfile:
        payload = await self._request("GET", "/profile")
        return IrisProfile.from_json(payload)

    async def async_send_command(self, command: str) -> None:
        await self._request("POST", f"/send/{command}")

    async def _request(
        self,
        method: str,
        path: str,
        *,
        auth: bool = True,
    ) -> dict[str, Any]:
        headers = {}
        if auth and self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        async with self._session.request(
            method,
            f"{self._base_url}{path}",
            headers=headers,
        ) as response:
            if response.status == 401:
                raise IrisAuthError("invalid IRIS API token")
            if response.status >= 400:
                text = await response.text()
                raise IrisApiError(f"IRIS API returned {response.status}: {text}")
            return await response.json()
