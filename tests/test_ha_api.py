import asyncio
import importlib.util
from pathlib import Path
import sys
import unittest

API_PATH = Path(__file__).resolve().parents[1] / "custom_components" / "iris" / "api.py"
SPEC = importlib.util.spec_from_file_location("iris_ha_api", API_PATH)
api = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = api
SPEC.loader.exec_module(api)

IrisApiClient = api.IrisApiClient
IrisAuthError = api.IrisAuthError
IrisConnectionError = api.IrisConnectionError


class FakeResponse:
    def __init__(self, status, payload):
        self.status = status
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def json(self):
        return self._payload

    async def text(self):
        return str(self._payload)


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def request(self, method, url, headers):
        self.calls.append((method, url, headers))
        return self.response


class FailingSession:
    def request(self, method, url, headers):
        raise OSError("network unreachable")


class IrisApiClientTests(unittest.TestCase):
    def test_get_devices_uses_bearer_token_and_parses_device_metadata(self):
        async def run():
            session = FakeSession(
                FakeResponse(
                    200,
                    {
                        "devices": [{
                            "id": "bedroom_fan",
                            "name": "Bedroom Fan",
                            "profile": "generic/fan",
                            "brand": "generic",
                            "model": "fan",
                            "device_type": "fan",
                            "commands": ["power", "speed_low"],
                            "home_assistant": {"fan": {"presets": {"low": "speed_low"}}},
                        }],
                    },
                )
            )
            client = IrisApiClient(session, "192.168.1.10", 8787, "secret")

            devices = await client.async_get_devices()
            device = devices[0]

            self.assertEqual(device.id, "bedroom_fan")
            self.assertEqual(device.commands, ("power", "speed_low"))
            self.assertEqual(device.fan.presets, {"low": "speed_low"})
            self.assertEqual(
                session.calls,
                [
                    (
                        "GET",
                        "http://192.168.1.10:8787/devices",
                        {"Authorization": "Bearer secret"},
                    )
                ],
            )

        asyncio.run(run())

    def test_unauthorized_response_raises_auth_error(self):
        async def run():
            session = FakeSession(FakeResponse(401, {"error": "unauthorized"}))
            client = IrisApiClient(session, "192.168.1.10", 8787, "bad")

            with self.assertRaises(IrisAuthError):
                await client.async_get_devices()

        asyncio.run(run())

    def test_network_failure_raises_connection_error(self):
        async def run():
            client = IrisApiClient(FailingSession(), "192.168.1.10", 8787, "secret")

            with self.assertRaises(IrisConnectionError):
                await client.async_get_health()

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
