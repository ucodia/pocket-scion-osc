#!/usr/bin/env python3
import argparse
import struct
import sys
import time
from dataclasses import dataclass

import rtmidi
from pythonosc.osc_bundle_builder import OscBundleBuilder, IMMEDIATELY
from pythonosc.osc_message_builder import OscMessageBuilder
from pythonosc.udp_client import SimpleUDPClient

OSC_HOST = "127.0.0.1"
OSC_PORT = 11046

SYSEX_HEADER = (0, 22, 25, 25)
SYSEX_LENGTH = 53


@dataclass
class ScionData:
    min: float
    max: float
    delta: float
    mean: float
    variance: float
    deviation: float


class _NibbleView:
    def __init__(self, data: tuple[int, ...]):
        self._d = data

    def uint(self, offset: int, count: int) -> int:
        return sum(self._d[offset + i] << (4 * i) for i in range(count))

    def float32(self, offset: int, pad: tuple[int, ...] = ()) -> float:
        nibs = tuple(self._d[offset:offset + 8 - len(pad)]) + pad
        raw = bytes(nibs[i] | (nibs[i + 1] << 4) for i in range(0, 8, 2))
        return struct.unpack('<f', raw)[0]


def decode_sysex(data: tuple[int, ...]) -> ScionData | None:
    if len(data) != SYSEX_LENGTH or tuple(data[:4]) != SYSEX_HEADER:
        return None

    n = _NibbleView(data)

    return ScionData(
        min=n.uint(5, 3) / 1000,
        max=n.uint(13, 4) / 1000,
        delta=n.uint(21, 4) / 1000,
        mean=n.float32(29) / 1000,
        variance=n.float32(37) / 1_000_000,
        deviation=n.float32(45, pad=(4,)) / 1000,
    )


def _osc_msg(address: str, value: float) -> OscMessageBuilder:
    msg = OscMessageBuilder(address=address)
    msg.add_arg(value)
    return msg.build()


def send_osc(client: SimpleUDPClient, data: ScionData) -> None:
    bundle = OscBundleBuilder(IMMEDIATELY)
    bundle.add_content(_osc_msg("/min", data.min))
    bundle.add_content(_osc_msg("/max", data.max))
    bundle.add_content(_osc_msg("/delta", data.delta))
    bundle.add_content(_osc_msg("/mean", data.mean))
    bundle.add_content(_osc_msg("/variance", data.variance))
    bundle.add_content(_osc_msg("/deviation", data.deviation))
    client.send(bundle.build())


def handle_midi(event, data):
    osc, debug = data
    message, _ = event
    if message[0] == 0xF0:
        result = decode_sysex(tuple(message[1:-1]))
        if result:
            if debug:
                print(result)
            send_osc(osc, result)


def find_scion_devices() -> list[tuple[int, str]]:
    midi_in = rtmidi.MidiIn()
    return [(i, name) for i, name in enumerate(midi_in.get_ports()) if "scion" in name.lower()]


def print_devices(devices: list[tuple[int, str]]) -> None:
    for i, (_, name) in enumerate(devices):
        print(f"[{i}] {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pocket Scion OSC bridge")
    parser.add_argument("--host", "-H", default=OSC_HOST, help=f"OSC destination host (default: {OSC_HOST})")
    parser.add_argument("--port", "-p", type=int, default=OSC_PORT, help=f"OSC destination port (default: {OSC_PORT})")
    parser.add_argument("--index", "-i", type=int, default=0, help="Index of the Scion device to bridge (default: 0)")
    parser.add_argument("--debug", "-d", action="store_true", help="Print OSC bundle data to stdout")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--list", "-l", action="store_true", help="List connected Scion devices and exit")
    group.add_argument("--interactive", "-I", action="store_true", help="Interactively select which Scion device to bridge")
    args = parser.parse_args()

    devices = find_scion_devices()
    if not devices:
        all_ports = rtmidi.MidiIn().get_ports()
        print(f"No Scion MIDI device found. Available: {all_ports or '(none)'}", file=sys.stderr)
        sys.exit(1)

    if args.list:
        print_devices(devices)
        sys.exit(0)

    if args.interactive:
        print_devices(devices)
        try:
            raw = input(f"Select device index [{args.index}]: ").strip()
            index = int(raw) if raw else args.index
        except (ValueError, EOFError):
            print("Invalid input.", file=sys.stderr)
            sys.exit(1)

        try:
            raw = input(f"OSC host [{args.host}]: ").strip()
            host = raw if raw else args.host
        except EOFError:
            print("Invalid input.", file=sys.stderr)
            sys.exit(1)

        try:
            raw = input(f"OSC port [{args.port}]: ").strip()
            port = int(raw) if raw else args.port
        except (ValueError, EOFError):
            print("Invalid input.", file=sys.stderr)
            sys.exit(1)

        default_debug = "Y" if args.debug else "N"
        try:
            raw = input(f"Debug [{'Y/n' if args.debug else 'y/N'}]: ").strip().lower()
            debug = args.debug if raw == "" else raw in ("y", "yes")
        except EOFError:
            print("Invalid input.", file=sys.stderr)
            sys.exit(1)
    else:
        index = args.index
        host = args.host
        port = args.port
        debug = args.debug

    if not 0 <= index < len(devices):
        print(f"Index {index} out of range (0-{len(devices) - 1}).", file=sys.stderr)
        sys.exit(1)

    port_index, port_name = devices[index]
    osc = SimpleUDPClient(host, port)
    print(f"MIDI: {port_name} → OSC: {host}:{port}")

    midi_in = rtmidi.MidiIn()
    midi_in.ignore_types(sysex=False)
    midi_in.open_port(port_index)
    midi_in.set_callback(handle_midi, (osc, debug))
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        midi_in.close_port()


if __name__ == "__main__":
    main()
