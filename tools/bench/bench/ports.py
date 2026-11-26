# SPDX-License-Identifier: GPL-3.0-or-later
"""Finding a role's port and opening it without stopping a native-USB ESP32.

On the ESP32-S3 USB-Serial/JTAG, DTR asserted selects download mode and RTS
asserted holds the chip in reset. pyserial asserts both on open, so the lines
are set low *before* opening.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from .config import Bench, Role


class BenchError(Exception):
    """A precondition of the bench is not met (exit code 4)."""


@dataclass(frozen=True)
class Found:
    device: str
    vid: int
    pid: int
    serial: str | None


def list_devices() -> list[Found]:
    from serial.tools import list_ports

    return [
        Found(p.device, p.vid, p.pid, p.serial_number)
        for p in list_ports.comports()
        if p.vid is not None
    ]


def match(role: Role, devices: list[Found]) -> list[Found]:
    """Devices that are this role. Without a recorded serial, VID:PID decides."""
    hits = [d for d in devices if (d.vid, d.pid) == (role.vid, role.pid)]
    if role.serial:
        hits = [d for d in hits if d.serial == role.serial]
    return hits


def resolve(bench: Bench, role_name: str, devices: list[Found] | None = None,
            exists=os.path.exists) -> str:
    """The stable udev link if present, else the one device that matches the role."""
    link = bench.link(role_name)
    if exists(link):
        return link
    role = bench.role(role_name)
    hits = match(role, list_devices() if devices is None else devices)
    if not hits:
        raise BenchError(f"role {role_name!r} not found (no {link}, no {role.vid:04x}:{role.pid:04x}"
                         f"{' serial ' + role.serial if role.serial else ''})")
    if len(hits) > 1:
        raise BenchError(f"role {role_name!r} is ambiguous: {[h.device for h in hits]}; "
                         "record its serial in bench.yaml")
    return hits[0].device


def open_port(device: str, baudrate: int = 115200, timeout: float = 0.1, factory=None):
    """Open with DTR and RTS low first: opening first would stop the chip."""
    if factory is None:
        import serial

        factory = serial.serial_for_url
    ser = factory(device, do_not_open=True)
    ser.baudrate = baudrate
    ser.timeout = timeout
    ser.dtr = False
    ser.rts = False
    ser.open()
    return ser
