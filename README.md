# Pocket Scion OSC bridge

Lightweight bridge that reads MIDI sysex from an Instruo Pocket Scion and sends the decoded biofeedback stats as OSC bundles (no companion app required).

OSC addresses:
- `/min`
- `/max`
- `/delta`
- `/mean`
- `/variance`
- `/deviation`

## Requirements

- [uv](https://docs.astral.sh/uv/) (recommended)

### Linux only

- Debian/Ubuntu: `apt install libasound2`
- Fedora/RHEL: `dnf install alsa-lib`

## Setup

```bash
uv sync
```

## Usage

Run with `uv run bridge.py`

```
usage: bridge.py [-h] [--host HOST] [--port PORT] [--index INDEX] [--debug] [--list | --interactive]

Pocket Scion OSC bridge

options:
  -h, --help         show this help message and exit
  --host, -H HOST    OSC destination host (default: 127.0.0.1)
  --port, -p PORT    OSC destination port (default: 11046)
  --index, -i INDEX  Index of the Scion device to bridge (default: 0)
  --debug, -d        Print OSC bundle data to stdout
  --list, -l         List connected Scion devices and exit
  --interactive, -I  Interactively select which Scion device to bridge
```
