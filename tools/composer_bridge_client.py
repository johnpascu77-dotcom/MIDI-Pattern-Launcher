#!/usr/bin/env python3
"""
Composer Bridge reference client for MIDI Pattern Launcher.

Requires:
    pip install mido python-rtmidi

Examples:
    python tools/composer_bridge_client.py list

    python tools/composer_bridge_client.py dump --out "MIDI Pattern Launcher" --in "MIDI Pattern Launcher" --pattern 0

    python tools/composer_bridge_client.py set-step --out "MIDI Pattern Launcher" --pattern 0 --step 0 --enabled 1 --note 60 --velocity 100 --duration 1

    python tools/composer_bridge_client.py clear --out "MIDI Pattern Launcher" --pattern 0

    python tools/composer_bridge_client.py copy --out "MIDI Pattern Launcher" --source 0 --dest 1

    python tools/composer_bridge_client.py write-pattern --out "MIDI Pattern Launcher" --pattern 0 --root 60 --velocity 100 --duration 1
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Iterable, List, Optional

try:
    import mido
except ImportError:
    print("ERROR: missing dependency 'mido'. Install with:", file=sys.stderr)
    print("    pip install mido python-rtmidi", file=sys.stderr)
    sys.exit(2)


HEADER = [0x7D, 0x4D, 0x50, 0x4C, 0x01]

CMD_WRITE_STEP = 0x01
CMD_CLEAR_PATTERN = 0x02
CMD_COPY_PATTERN = 0x03
CMD_WRITE_FULL_PATTERN = 0x04
CMD_REQUEST_DUMP = 0x05
CMD_PATTERN_DUMP = 0x06
CMD_FEEDBACK = 0x7F

STATUS_NAMES = {
    0x00: "ACK",
    0x01: "NACK malformed",
    0x02: "NACK invalid pattern",
    0x03: "NACK invalid step",
    0x04: "NACK unsupported command",
}


def ensure_data_byte(value: int, name: str) -> int:
    if not 0 <= value <= 127:
        raise ValueError(f"{name} must be in range 0..127, got {value}")
    return value


def make_sysex(command: int, payload: Iterable[int]) -> "mido.Message":
    data = HEADER + [ensure_data_byte(command, "command")]

    for index, value in enumerate(payload):
        data.append(ensure_data_byte(int(value), f"payload[{index}]"))

    return mido.Message("sysex", data=data)


def is_composer_bridge_message(msg: "mido.Message") -> bool:
    return msg.type == "sysex" and list(msg.data[: len(HEADER)]) == HEADER


def message_command(msg: "mido.Message") -> Optional[int]:
    if not is_composer_bridge_message(msg):
        return None

    data = list(msg.data)

    if len(data) <= len(HEADER):
        return None

    return data[len(HEADER)]


def payload_after_command(msg: "mido.Message") -> List[int]:
    return list(msg.data)[len(HEADER) + 1 :]


def format_hex_data(data: Iterable[int]) -> str:
    return " ".join(f"{byte:02X}" for byte in data)


def print_message(msg: "mido.Message", prefix: str = "RX") -> None:
    if msg.type == "sysex":
        print(f"{prefix}: F0 {format_hex_data(msg.data)} F7")
    else:
        print(f"{prefix}: {msg}")


def list_ports(_args: argparse.Namespace) -> int:
    print("Input ports:")

    for name in mido.get_input_names():
        print(f"  {name}")

    print()
    print("Output ports:")

    for name in mido.get_output_names():
        print(f"  {name}")

    return 0


def open_output(name: str):
    try:
        return mido.open_output(name)
    except OSError as exc:
        print(f"ERROR: could not open output port: {name}", file=sys.stderr)
        print(exc, file=sys.stderr)
        return None


def open_input(name: Optional[str]):
    if not name:
        return None

    try:
        return mido.open_input(name)
    except OSError as exc:
        print(f"ERROR: could not open input port: {name}", file=sys.stderr)
        print(exc, file=sys.stderr)
        return None


def receive_for_seconds(input_port, seconds: float) -> List["mido.Message"]:
    if input_port is None or seconds <= 0:
        return []

    deadline = time.time() + seconds
    received = []

    while time.time() < deadline:
        for msg in input_port.iter_pending():
            received.append(msg)

        time.sleep(0.01)

    return received


def print_feedback(msg: "mido.Message") -> None:
    payload = payload_after_command(msg)

    if len(payload) < 3:
        print_message(msg)
        print("  malformed feedback payload")
        return

    status, original_command, detail = payload[:3]
    status_name = STATUS_NAMES.get(status, f"unknown status {status}")

    print_message(msg)
    print(f"  feedback: {status_name}, originalCommand=0x{original_command:02X}, detail={detail}")


def print_pattern_dump(msg: "mido.Message") -> None:
    payload = payload_after_command(msg)

    if len(payload) < 2:
        print_message(msg)
        print("  malformed pattern dump payload")
        return

    pattern = payload[0]
    step_count = payload[1]
    step_bytes = payload[2:]

    print_message(msg)
    print()
    print(f"Pattern dump: pattern={pattern}, stepCount={step_count}")

    expected_length = step_count * 4

    if len(step_bytes) != expected_length:
        print(f"WARNING: expected {expected_length} step bytes, got {len(step_bytes)}")

    print()
    print("Step | Enabled | Note | Velocity | Duration")
    print("-----+---------+------+----------+---------")

    for step in range(min(step_count, len(step_bytes) // 4)):
        offset = step * 4
        enabled, note, velocity, duration = step_bytes[offset : offset + 4]
        print(f"{step:>4} | {enabled:>7} | {note:>4} | {velocity:>8} | {duration:>8}")


def print_received_messages(messages: List["mido.Message"]) -> None:
    if not messages:
        print("No messages received.")
        return

    for msg in messages:
        command = message_command(msg)

        if command == CMD_FEEDBACK:
            print_feedback(msg)
        elif command == CMD_PATTERN_DUMP:
            print_pattern_dump(msg)
        else:
            print_message(msg)


def send_and_optionally_receive(args: argparse.Namespace, msg: "mido.Message") -> int:
    out_port = open_output(args.out)

    if out_port is None:
        return 1

    in_port = open_input(getattr(args, "in_port", None))

    if getattr(args, "in_port", None) and in_port is None:
        out_port.close()
        return 1

    print_message(msg, prefix="TX")
    out_port.send(msg)

    wait = getattr(args, "wait", 0.5)

    if in_port is not None and wait > 0:
        messages = receive_for_seconds(in_port, wait)
        print_received_messages(messages)

    if in_port is not None:
        in_port.close()

    out_port.close()

    return 0


def command_dump(args: argparse.Namespace) -> int:
    msg = make_sysex(CMD_REQUEST_DUMP, [args.pattern])
    return send_and_optionally_receive(args, msg)


def command_set_step(args: argparse.Namespace) -> int:
    msg = make_sysex(
        CMD_WRITE_STEP,
        [args.pattern, args.step, args.enabled, args.note, args.velocity, args.duration],
    )

    return send_and_optionally_receive(args, msg)


def command_clear(args: argparse.Namespace) -> int:
    msg = make_sysex(CMD_CLEAR_PATTERN, [args.pattern])
    return send_and_optionally_receive(args, msg)


def command_copy(args: argparse.Namespace) -> int:
    msg = make_sysex(CMD_COPY_PATTERN, [args.source, args.dest])
    return send_and_optionally_receive(args, msg)


def command_write_pattern(args: argparse.Namespace) -> int:
    steps = []

    for step in range(16):
        enabled = 1
        note = ensure_data_byte(args.root + step, f"note for step {step}")
        velocity = args.velocity
        duration = args.duration
        steps.extend([enabled, note, velocity, duration])

    msg = make_sysex(CMD_WRITE_FULL_PATTERN, [args.pattern, 16] + steps)
    return send_and_optionally_receive(args, msg)


def add_common_midi_args(parser: argparse.ArgumentParser, receive_default: bool = True) -> None:
    parser.add_argument("--out", required=True, help="MIDI output port name")
    parser.add_argument("--in", dest="in_port", help="MIDI input port name for responses")
    parser.add_argument(
        "--wait",
        type=float,
        default=0.5 if receive_default else 0.0,
        help="Seconds to wait for responses when --in is provided",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Composer Bridge reference client for MIDI Pattern Launcher"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List available MIDI ports")
    list_parser.set_defaults(func=list_ports)

    dump_parser = subparsers.add_parser("dump", help="Request and print a pattern dump")
    add_common_midi_args(dump_parser)
    dump_parser.add_argument("--pattern", type=int, required=True)
    dump_parser.set_defaults(func=command_dump)

    set_step_parser = subparsers.add_parser("set-step", help="Write one pattern step")
    add_common_midi_args(set_step_parser)
    set_step_parser.add_argument("--pattern", type=int, required=True)
    set_step_parser.add_argument("--step", type=int, required=True)
    set_step_parser.add_argument("--enabled", type=int, required=True)
    set_step_parser.add_argument("--note", type=int, required=True)
    set_step_parser.add_argument("--velocity", type=int, required=True)
    set_step_parser.add_argument("--duration", type=int, required=True)
    set_step_parser.set_defaults(func=command_set_step)

    clear_parser = subparsers.add_parser("clear", help="Clear one pattern")
    add_common_midi_args(clear_parser)
    clear_parser.add_argument("--pattern", type=int, required=True)
    clear_parser.set_defaults(func=command_clear)

    copy_parser = subparsers.add_parser("copy", help="Copy one pattern to another slot")
    add_common_midi_args(copy_parser)
    copy_parser.add_argument("--source", type=int, required=True)
    copy_parser.add_argument("--dest", type=int, required=True)
    copy_parser.set_defaults(func=command_copy)

    write_pattern_parser = subparsers.add_parser(
        "write-pattern", help="Write a simple ascending 16-step pattern"
    )
    add_common_midi_args(write_pattern_parser)
    write_pattern_parser.add_argument("--pattern", type=int, required=True)
    write_pattern_parser.add_argument("--root", type=int, default=60)
    write_pattern_parser.add_argument("--velocity", type=int, default=100)
    write_pattern_parser.add_argument("--duration", type=int, default=1)
    write_pattern_parser.set_defaults(func=command_write_pattern)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
