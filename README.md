# IRIS Home Assistant

Custom Home Assistant integration for IRIS TV bridges.

IRIS runs on a Raspberry Pi and exposes a local HTTP API plus Zeroconf discovery. This integration discovers IRIS on the LAN and creates a `media_player` TV entity.

## Requirements

- Home Assistant with HACS installed.
- IRIS running on the Raspberry Pi with Home Assistant setup enabled.
- IRIS Rust app version compatible with API version `1`.

Prepare IRIS on the Raspberry Pi:

```bash
iris start telstar
iris home-assistant setup
iris daemon start telstar
```

Save the `api_token` printed by `iris home-assistant setup`.

## Install With HACS

1. In Home Assistant, open HACS.
2. Open the three-dot menu.
3. Select **Custom repositories**.
4. Add this repository URL:

   ```text
   https://github.com/pieza/iris-home-assistant
   ```

5. Select category **Integration**.
6. Click **Add**.
7. Search for **IRIS** in HACS and download it.
8. Restart Home Assistant.

After restart, Home Assistant should show IRIS as a discovered device. Accept it and enter the API token from the Raspberry Pi.

If discovery does not appear, go to **Settings > Devices & services > Add integration**, search for **IRIS**, then enter the Raspberry Pi IP address, port `8787`, and API token manually.

## Manual Install

Copy `custom_components/iris` into your Home Assistant `custom_components` directory and restart Home Assistant.

## Features

- Zeroconf discovery for `_iris-tv._tcp.local.`
- `media_player` TV entity.
- Power on/off via `power_on` / `power_off`, or optimistic `power` toggle when only that command exists.
- Volume up/down, mute, and input source commands when the active IRIS profile supports them.
- Button entities for supported remote commands, including channels, menu, navigation, colored keys, Netflix, Prime Video, and YouTube.
- `iris.send_command` service for extra profile commands such as `up`, `down`, `left`, `right`, `ok`, `back`, `home`, and `menu`.

## Development

Run local checks:

```bash
python -m compileall custom_components/iris
python -m unittest tests/test_ha_api.py
```
