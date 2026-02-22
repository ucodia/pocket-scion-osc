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

## Building as a standalone executable

By using PyInstaller the program can be bundled as a standlone executable which does not require Python to run on the target system.

To build run the following command:

```bash
uv run pyinstaller launcher.spec
```

The executable is written to `dist/`.

When launched without any arguments (e.g. double-clicking the `.exe` on Windows), interactive mode is enabled automatically. Passing any CLI argument disables auto-interactive, making the executable suitable for scripting:

```bash
./pocket-scion-osc.exe --host 192.168.1.100 --port 9000
```

### Building for Linux with Docker

To build for Linux variants `arm64` and `amd64` set the `PLATFORM` value accordingly in the command below:

```bash
PLATFORM=arm64
docker build --platform linux/$PLATFORM -t pocket-scion-osc-trixie -f - . <<'DOCKERFILE'
FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim
RUN apt-get update && apt-get install -y --no-install-recommends binutils libasound2-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
RUN uv sync --group dev
CMD ["uv", "run", "pyinstaller", "launcher.spec"]
DOCKERFILE
docker run --rm -v "$(pwd)/dist:/app/dist" --platform linux/$PLATFORM pocket-scion-osc-trixie
```
