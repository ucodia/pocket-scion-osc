# Pocket Scion OSC bridge

Lightweight bridge that reads MIDI sysex from an Instruo Pocket Scion and sends the decoded biofeedback stats as OSC bundles (no companion app required).

**OSC addresses:** `/min`, `/max`, `/delta`, `/mean`, `/variance`, `/deviation` (one float each, sent as a single bundle per sysex).

## Requirements

- [uv](https://docs.astral.sh/uv/) (recommended)

## Setup

```bash
uv sync
```

## Run

```bash
uv run bridge.py
```

Defaults: OSC → `127.0.0.1:11046`. Override with:

```bash
uv run bridge.py --host 192.168.1.10 --port 9000
uv run bridge.py -H 192.168.1.10 -p 9000
```

The script picks up the first connected MIDI input whose name contains `scion`.
