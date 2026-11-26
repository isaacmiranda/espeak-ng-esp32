# SPDX-License-Identifier: GPL-3.0-or-later
"""bench.yaml: role -> how to recognise the board. Never a /dev/ttyACM* path."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_PATH = Path(__file__).resolve().parents[3] / "bench.yaml"


@dataclass(frozen=True)
class Role:
    name: str
    vid: int
    pid: int
    serial: str | None
    chip: str
    flash_mb: int
    psram: bool
    required: bool


@dataclass(frozen=True)
class Bench:
    project: str
    link_prefix: str
    volume_ceiling: int | None
    roles: dict[str, Role]

    def role(self, name: str) -> Role:
        if name not in self.roles:
            raise KeyError(f"unknown role {name!r}; bench.yaml has {sorted(self.roles)}")
        return self.roles[name]

    def link(self, name: str) -> str:
        return f"{self.link_prefix}{name}"


def _vid_pid(text: str) -> tuple[int, int]:
    vid, pid = str(text).split(":")
    return int(vid, 16), int(pid, 16)


def parse(data: dict) -> Bench:
    roles = {}
    for name, r in (data.get("roles") or {}).items():
        vid, pid = _vid_pid(r["vid_pid"])
        roles[name] = Role(
            name=name,
            vid=vid,
            pid=pid,
            serial=r.get("serial") or None,
            chip=r["chip"],
            flash_mb=int(r["flash_mb"]),
            psram=bool(r["psram"]),
            required=bool(r.get("required", True)),
        )
    audio = data.get("audio") or {}
    return Bench(
        project=data["project"],
        link_prefix=data["link_prefix"],
        volume_ceiling=audio.get("bench_volume_ceiling"),
        roles=roles,
    )


def load(path: Path | str | None = None) -> Bench:
    with open(path or DEFAULT_PATH, encoding="utf-8") as fh:
        return parse(yaml.safe_load(fh))
