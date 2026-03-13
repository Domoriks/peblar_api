# Peblar API

![Peblar icon](custom_components/peblar_api/brand/icon.png)

[![HACS][hacsbadge]][hacs]
[![GitHub Release][releases-shield]][releases]
[![License][license-shield]][license]
[![Installs][hainstallbadge]][hainstall]

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=domoriks&repository=peblar_api&category=integration)
[![Open your Home Assistant instance and start setting up Peblar API.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=peblar_api)

Home Assistant custom integration for **local** monitoring and control of [Peblar EV chargers](https://www.peblar.com/) via its built-in REST API. No cloud connection required — all communication happens directly between Home Assistant and the charger on your local network.

## Disclaimer

> This is an unofficial, project and is **not** affiliated with, endorsed by, or supported by Peblar.
> It is maintained by a single developer with a personal Peblar charger.
> Use at your own risk. The developer is not responsible for any damage, charging issues, data loss, or other consequences.

## What this integration does

Once installed and configured, this integration:

- **Connects locally** to your Peblar charger over your home network using the charger's REST API — no internet or cloud account needed.
- **Polls three API endpoints** (`system`, `meter`, `evinterface`) on a regular interval to keep all sensor values up to date in Home Assistant.
- **Exposes 27 sensor entities** so you can monitor everything from firmware version and signal strength to per-phase current, voltage, power, energy counters and EV connection state.
- **Exposes 1 number entity** (`Charge Current Limit`) that lets you set the maximum charge current directly from Home Assistant — useful for automations, demand control, or solar-excess charging.

## Features

- UI-based setup — enter your charger's IP address/hostname and API token; no YAML required.
- Local polling only — no cloud account or internet access needed after initial setup.
- Duplicate prevention using the charger's serial number as the unique device ID.
- 27 sensor entities covering diagnostics, real-time metering, and EV interface state.
- 1 number entity for charge current limit control (amperes).

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant.
2. Add this repository as a custom repository if it does not appear automatically:
   - URL: `https://github.com/domoriks/peblar_api`
   - Category: `Integration`
3. Search for and install **Peblar API**.
4. Restart Home Assistant.

### Manual installation

1. Copy the `custom_components/peblar_api` folder into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.

## Configuration

### Step 1 — Enable the local REST API on your charger

Before adding the integration, you must enable the local REST API on the charger and create an API token.

- Follow the Peblar developer documentation: https://developer.peblar.com/local-rest-api#section/General
- Enable the local REST API in the charger's web interface.
- Create an API token and set the permission level to **Read/Write**.

> **Important:** A read-only token is not sufficient. Write access is required for the `Charge Current Limit` control to work.

![Peblar local API enable screen](api_enable.png)

### Step 2 — Add the integration in Home Assistant

1. Go to **Settings → Devices & Services**.
2. Click **Add Integration**.
3. Search for **Peblar API**.
4. Enter the **IP address or hostname** of your charger.
5. Enter your **API token** (must be Read/Write).

## Entities

### Sensors (27 total)

| Entity | Source | Unit | Notes |
|---|---|---|---|
| Firmware Version | `system` | — | Diagnostic |
| Serial Number | `system` | — | Diagnostic |
| Product Part Number | `system` | — | Diagnostic |
| Phase Count | `system` | — | Diagnostic |
| Uptime | `system` | s | Diagnostic |
| Cellular Signal Strength | `system` | dBm | Diagnostic |
| WLAN Signal Strength | `system` | dBm | Diagnostic |
| Active Error Codes | `system` | — | Diagnostic; comma-separated list or `None` |
| Active Warning Codes | `system` | — | Diagnostic; comma-separated list or `None` |
| Current Phase 1 / 2 / 3 | `meter` | A | Real-time per-phase current |
| Voltage Phase 1 / 2 / 3 | `meter` | V | Real-time per-phase voltage |
| Power Phase 1 / 2 / 3 | `meter` | W | Real-time per-phase power |
| Power Total | `meter` | W | Sum of all phases |
| Energy Session | `meter` | Wh | Energy delivered in the current session |
| Energy Total | `meter` | Wh | Lifetime energy delivered |
| Charge Current Limit | `evinterface` | A | Configured maximum charge current |
| Charge Current Limit Actual | `evinterface` | A | Currently applied limit |
| Charge Current Limit Source | `evinterface` | — | Diagnostic; which source owns the limit |
| Charge State | `evinterface` | — | Human-readable CP state (e.g. `Charging`) |
| Force Single Phase | `evinterface` | — | Diagnostic |
| Lock State | `evinterface` | — | Plug lock status |

### Controls

| Entity | Type | Range | Notes |
|---|---|---|---|
| Charge Current Limit | `number` | 6–32 A | Writes `ChargeCurrentLimit` to the charger via REST API |

## Troubleshooting

| Error | Likely cause | Fix |
|---|---|---|
| `cannot_connect` | Wrong host/IP or charger not reachable on the network | Verify the IP address and that HA can reach the charger |
| `invalid_auth` | Wrong or expired API token | Re-enter the token; confirm it has Read/Write permission |
| `already_configured` | Charger already added to Home Assistant | The same serial number is already registered as a device |

Enable debug logging by adding the following to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.peblar_api: debug
```

## Repository structure

```text
custom_components/peblar_api/
  __init__.py        — Integration entry point and setup
  api.py             — HTTP client for the Peblar REST API
  config_flow.py     — UI-based setup and validation flow
  const.py           — Domain name and shared constants
  coordinator.py     — DataUpdateCoordinator; polls all three endpoints
  manifest.json      — Home Assistant / HACS integration manifest
  number.py          — Charge current limit control entity
  sensor.py          — All 27 sensor entity definitions
  strings.json       — UI strings for config flow and entities
  brand/             — Integration icon used in HA and HACS
  translations/      — Localisation files (currently English)
```

## HACS publishing notes

- `hacs.json` is included in the repository root.
- Integration files are under `custom_components/peblar_api`.
- `manifest.json` includes all required HACS keys and a `version` field.
- Brand assets exist in `custom_components/peblar_api/brand/`.

Before requesting inclusion in the default HACS repository:

- Add a clear description to the GitHub repository.
- Add relevant topics: `home-assistant`, `hacs`, `homeassistant-integration`, `peblar`, `ev-charger`.
- Publish GitHub releases so HACS can offer versioned installs.

## License

This project is open source and available under the [MIT License](LICENSE).

---

[releases-shield]: https://img.shields.io/github/release/domoriks/peblar_api.svg
[releases]: https://github.com/domoriks/peblar_api/releases
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs]: https://github.com/hacs/integration
[hainstallbadge]: https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=installs&suffix=%20users&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.peblar_api.total
[hainstall]: https://analytics.home-assistant.io/custom_integrations
[license-shield]: https://img.shields.io/github/license/domoriks/peblar_api.svg
[license]: https://github.com/domoriks/peblar_api/blob/main/LICENSE
