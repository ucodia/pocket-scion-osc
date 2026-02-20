#!/usr/bin/env python3
import argparse
import struct
import sys
from dataclasses import dataclass

import mido
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Pocket Scion OSC bridge")
    parser.add_argument("--host", "-H", default=OSC_HOST, help=f"OSC destination host (default: {OSC_HOST})")
    parser.add_argument("--port", "-p", type=int, default=OSC_PORT, help=f"OSC destination port (default: {OSC_PORT})")
    args = parser.parse_args()

    names = mido.get_input_names()
    scion_port = next((n for n in names if "scion" in n.lower()), None)
    if scion_port is None:
        print(f"No Scion MIDI device found. Available: {names or '(none)'}", file=sys.stderr)
        sys.exit(1)

    osc = SimpleUDPClient(args.host, args.port)
    print(f"MIDI: {scion_port} → OSC: {args.host}:{args.port}")

    with mido.open_input(scion_port) as inport:
        for msg in inport:
            if msg.type == "sysex":
                result = decode_sysex(msg.data)
                if result:
                    send_osc(osc, result)


if __name__ == "__main__":
    main()
