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


class IrisApiClientTests(unittest.TestCase):
    def test_get_profile_uses_bearer_token_and_parses_commands(self):
        async def run():
            session = FakeSession(
                FakeResponse(
                    200,
                    {
                        "id": "telstar/generic",
                        "brand": "telstar",
                        "model": "generic",
                        "device_type": "tv",
                        "commands": ["power", "volume_up"],
                    },
                )
            )
            client = IrisApiClient(session, "192.168.1.10", 8787, "secret")

            profile = await client.async_get_profile()

            self.assertEqual(profile.id, "telstar/generic")
            self.assertEqual(profile.commands, ("power", "volume_up"))
            self.assertEqual(
                session.calls,
                [
                    (
                        "GET",
                        "http://192.168.1.10:8787/profile",
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
                await client.async_get_profile()

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
