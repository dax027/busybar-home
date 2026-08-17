# BUSY Bar Home

A local, visual control center for your [BUSY Bar](https://busy.app/). Choose polished front and
rear display scenes in seconds, check battery and firmware health, and capture device diagnostics
from one browser dashboard.

BUSY Bar Home is built with Python 3.12 and the official
[`busylib`](https://pypi.org/project/busylib/) SDK. Device access stays behind a mockable client and
an explicit hardware safety gate, so development and tests run safely without physical hardware.

## Requirements

- Python 3.12 or newer
- [`uv`](https://docs.astral.sh/uv/)

## Setup

```shell
uv sync
```

Optionally copy `.env.example` to `.env` for reference. This application reads environment
variables directly; it does not automatically load `.env` files.

## Run safely with the fake client

The default command performs no network I/O. It records the requested display message in
memory and prints a fake device snapshot:

```shell
uv run busybar-home "BUSY"
```

### Local visual dashboard

Start the dashboard on the local machine:

```shell
uv run busybar-home-web
```

Then open [http://127.0.0.1:8765](http://127.0.0.1:8765). The dashboard previews the
front and rear displays and offers one-click scene presets. The default fake client records
selections in memory and performs no network I/O.

The main page also shows device name, battery level, power state, firmware, API version, and
uptime. Status is read once when the page loads and only again when **Refresh status** is selected;
the app does not continuously poll the device.

Open [http://127.0.0.1:8765/logs](http://127.0.0.1:8765/logs) for device diagnostics. Nothing is
captured automatically. Selecting **Capture device log** snapshots the BUSY Bar's in-memory log
buffer to its fixed default `/ext/log.txt`, downloads it through the official storage API, and
shows it locally. Repeated captures overwrite that same dump path; the app does not delete other
device files. Display is capped at the newest 512 KiB. Device-log capture requires BUSY Bar API
25.0.0 or newer. Raw diagnostics may contain internal device or network details; keep captures
local and do not commit or share them casually.

### Included scenes

| Scene | Public front display | Private rear cue |
| --- | --- | --- |
| Deep focus | `BUSY` | `DEEP FOCUS` — One task. No inbox. |
| In a meeting | `ON A CALL` | `MEETING MODE` — Capture decisions. |
| Available | `FREE` | `RESET WINDOW` — Clear quick replies. |
| Stepped away | `AWAY` | `PAUSE` — Reset when I return. |
| Low social battery | Native animated low-battery display | `SOCIAL BATTERY` — Quiet mode. Recharge. |
| Coding | Native animated coding display | `BUILD MODE` — Write. Run. Refine. |
| Hacking | Cyan/magenta cyberpunk `HACKING` treatment | `CYBER OPS` — Map. Probe. Learn. |
| Daydreaming | Sky-blue `DAYDREAMING` scene with white clouds | `WANDER MODE` — Let ideas drift. |

The browser uses the official frame sets to preview Coding and Low social battery exactly, while
Hacking retains its animated glitch preview. On the physical device, Coding and Low social battery
use the corresponding stock BUSY Bar animations. Playback happens on the device; the app does not
simulate animation with a continuous network-command loop.

The Coding and Low social battery browser previews are generated from the corresponding official
[BUSY Bar firmware animation assets](https://github.com/busy-app/busybar-firmware/tree/dev/assets/shared/animations),
which are licensed by BUSY under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

### Everyday real-device launcher

After explicitly authorizing physical-device control and completing `uv sync`, run:

```powershell
.\start-busybar-home.ps1
```

This launcher selects the official client, explicitly enables the hardware safety gate, and
defaults to the USB address `10.0.4.20`. Keep
[http://127.0.0.1:8765](http://127.0.0.1:8765) bookmarked for quick access. It does not install a
Windows startup task or expose the dashboard to other computers.

If a scene reports that another BUSY app owns the display, close or release the BUSY app on the
other computer, phone, or tablet and try again. Those clients can hold a higher-priority display
session even though this dashboard and the device remain reachable.

### Start automatically with Windows

Install the per-user Windows startup shortcut once:

```powershell
.\install-startup.ps1
```

At future sign-ins, Windows starts the dashboard server in the background without opening a
browser. Open the bookmarked [http://127.0.0.1:8765](http://127.0.0.1:8765) when you are ready to
use it. The launcher checks the dashboard port first, so it does not start a duplicate server.
Keep the official BUSY app closed on other devices if it competes for display ownership.

To remove the startup shortcut:

```powershell
.\install-startup.ps1 -Remove
```

The foreground `start-busybar-home.ps1` launcher remains available for troubleshooting.

## Development commands

```shell
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run ruff format .
```

Run all non-mutating checks together:

```shell
uv run ruff check . && uv run ruff format --check . && uv run pytest
```

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `BUSYBAR_CLIENT` | `fake` | `fake` or `official` |
| `BUSYBAR_DEVICE_ADDRESS` | `10.0.4.20` | Device IP/address for the official client |
| `BUSYBAR_ACCESS_TOKEN` | empty | Optional device access key; never commit it |
| `BUSYBAR_ALLOW_HARDWARE` | `false` | Safety gate required for the official client |
| `BUSYBAR_DISPLAY_PRIORITY` | `100` | Display ownership priority from 1–100 |
| `BUSYBAR_WEB_HOST` | `127.0.0.1` | Local dashboard bind address |
| `BUSYBAR_WEB_PORT` | `8765` | Local dashboard port |

The fake client remains the default. Selecting `BUSYBAR_CLIENT=official` without also explicitly
setting `BUSYBAR_ALLOW_HARDWARE=true` fails before the SDK client is created. The everyday launcher
sets both values intentionally for real-device use.

Before changing physical-device behavior, verify the installed `busylib` API and device firmware
compatibility. Do not put real access tokens in `.env.example`, tests, logs, or source control.

## Structure

```text
src/busybar_home/
  client.py            # mockable DeviceClient protocol
  clients/fake.py      # in-memory test/development client
  clients/official.py  # isolated busylib adapter
  config.py            # environment-backed settings
  factory.py           # client selection and hardware safety gate
  models.py            # SDK-independent data models
  service.py           # application use cases
  cli.py               # console entry point
  dashboard.py         # display presets and dashboard state
  web.py               # local HTTP API and dashboard server
  static/              # visual dashboard assets
tests/                  # hardware-free unit tests
```

## SDK notes

The adapter targets `busylib` 1.x. Scene rendering uses `display_draw(...)` with native text,
rectangle, and stock animation elements. Device health uses `name()`, `status_power()`, `status_firmware()`, and
`status_system()`. Manual diagnostics use `log_dump()` followed by `storage_read()`. The adapter
clears the existing Canvas layer before applying a scene and uses configurable display priority so
the dashboard can take ownership cleanly. BUSY Bar firmware and SDK contracts can change. Keep
SDK-specific types and method calls inside `clients/official.py`; application code should depend
only on `DeviceClient`.
