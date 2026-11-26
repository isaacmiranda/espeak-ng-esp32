# SPDX-License-Identifier: GPL-3.0-or-later
"""Language selection and capacity check of the espeak-ng component (FSD 13).

    capacity.py --data <espeak-ng-data> [--languages "en pt-br" | --all] [--default-voice en]
                [--partition-bytes N | --partitions <csv> --label espeak] [--budget-kb 2048] [--warn-pct 90]
                [--map <linker .map>] [--task-stack N --task-stack-psram y|n]
                [--out espeak.img] [--report r.json]

Exit 0: the selection is valid and fits (warnings go to stdout and do not fail). Exit 1: it does not, with a
message on stderr that says why and what would be valid. Every size comes from the files given, never from a
table kept by hand (FR-CAP-09). The same tool runs at configure time (checks, image) and after the link (map).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_image


def fail(msg: str) -> None:
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


def partition_size(csv: Path, label: str) -> int:
    units = {"K": 1024, "M": 1024 * 1024}
    for line in csv.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        cols = [c.strip() for c in line.split(",")]
        if cols[0] == label:
            size = cols[4]
            return int(size[:-1], 0) * units[size[-1].upper()] if size[-1].upper() in units else int(size, 0)
    fail(f"partition {label!r} is not in {csv}")


def static_ram_internal(map_file: Path) -> int:
    """Bytes of the component's own .data/.bss/.noinit in internal RAM, from the linker map: input sections
    of libespeak-ng.a objects inside an output section that is not .ext_ram.* (those went to PSRAM)."""
    text = map_file.read_text(errors="replace")
    heads = [
        (m.start(), m.group(1)) for m in re.finditer(r"^(\.\S+)", text, re.M)
    ]  # output sections: column 0
    item = re.compile(r"^ (\.\S+)\s*\n?\s+0x[0-9a-f]+\s+0x([0-9a-f]+)\s+\S*libespeak-ng\.a\(\S+\)", re.M)
    total = 0
    import bisect

    starts = [h[0] for h in heads]
    for m in item.finditer(text):
        out = heads[bisect.bisect_right(starts, m.start()) - 1][1]
        if out.startswith((".dram0.bss", ".dram0.data", ".noinit", ".dram0.noinit")):
            total += int(m.group(2), 16)
    return total


def analyse(a: argparse.Namespace) -> tuple[dict, bytes]:
    data = Path(a.data)
    known = sorted(gen_image.voice_files(data))
    if a.all:
        # the upstream lists voices whose dictionary its own data build does not compile
        # (xex, fo and kaa in 1.52.0)
        langs = [
            v
            for v in known
            if (data / f"{gen_image.dictionary_of(gen_image.voice_files(data)[v])}_dict").is_file()
        ]
        skipped = sorted(set(known) - set(langs))
        if skipped:
            print(
                "WARNING: voices without a compiled dictionary in the upstream data, left out: "
                + " ".join(skipped)
            )
    else:
        langs = a.languages.split()
        bad = [n for n in langs if n.lower() not in known]
        if bad:
            fail(f"unknown language {', '.join(bad)}; the valid names are: {' '.join(known)}")
    if not langs:
        fail("the language list is empty")
    if a.default_voice.lower() not in [n.lower() for n in langs]:
        fail(
            f"the initial voice {a.default_voice!r} is not in the language list ({' '.join(langs)}); "
            "add it to CONFIG_ESPK_LANGUAGES or change CONFIG_ESPK_DEFAULT_VOICE"
        )
    files = gen_image.select(data, langs)
    image = gen_image.build(data, langs)
    common = sum(files[n].stat().st_size for n in gen_image.COMMON)
    dicts = [f.stat().st_size for n, f in files.items() if n.endswith("_dict")]
    report = {
        "languages": langs,
        "default_voice": a.default_voice,
        "image_bytes": len(image),
        "psram_peak_bytes": common + max(dicts),  # the common files plus the biggest chosen dictionary
        "psram_budget_bytes": a.budget_kb * 1024,
    }
    part = (
        a.partition_bytes
        if a.partition_bytes
        else (partition_size(Path(a.partitions), a.label) if a.partitions else None)
    )
    report["partition_bytes"] = part
    if a.map:
        report["static_ram_internal_bytes"] = static_ram_internal(Path(a.map))
    if a.task_stack:
        report["task_stack_bytes"] = a.task_stack
        report["task_stack_in"] = "psram" if a.task_stack_psram == "y" else "internal"

    if part is not None and len(image) > part:
        fail(
            f"the data image does not fit: image {len(image)} B, partition {part} B, "
            f"over by {len(image) - part} B"
        )
    if report["psram_peak_bytes"] > report["psram_budget_bytes"]:
        fail(
            f"the estimated PSRAM peak {report['psram_peak_bytes']} B is above the budget "
            f"{report['psram_budget_bytes']} B (CONFIG_ESPK_PSRAM_BUDGET_KB={a.budget_kb}) of PSRAM"
        )
    for what, used, limit in (
        ("the data image", len(image), part),
        ("the PSRAM peak", report["psram_peak_bytes"], report["psram_budget_bytes"]),
    ):
        if limit and used * 100 > limit * a.warn_pct:
            print(
                f"WARNING: {what} uses {used * 100 / limit:.1f} % of its limit ({used} of {limit} B), "
                f"over the {a.warn_pct} % mark"
            )
    return report, image


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--languages", default="en")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--default-voice", default="en")
    ap.add_argument("--partition-bytes", type=int, default=0)
    ap.add_argument("--partitions")
    ap.add_argument("--label", default="espeak")
    ap.add_argument("--budget-kb", type=int, default=2048)
    ap.add_argument("--warn-pct", type=int, default=90)
    ap.add_argument("--map")
    ap.add_argument("--task-stack", type=int, default=0)
    ap.add_argument("--task-stack-psram", default="y")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--report", type=Path)
    a = ap.parse_args(argv)
    report, image = analyse(a)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_bytes(image)
    if a.report:
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(json.dumps(report, indent=1) + "\n")
    print("capacity report:")
    for k, v in report.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
