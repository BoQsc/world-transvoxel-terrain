#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import time

import psutil

import a4_phase3_terrain_world_lifecycle_smoke as harness


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts" / "human_terrain_inspection"
FIXTURE_ROOT = ARTIFACT_ROOT / "project"
MAIN_SCENE = (
    "res://addons/world_transvoxel_terrain/debug/"
    "wt_terrain_human_inspection_scene.tscn"
)
SMOKE_SCRIPT = "res://tests/human_terrain_inspection_smoke.gd"
SMOKE_MARKER = "WT_TERRAIN_HUMAN_INSPECTION_SMOKE_PASS"
STEAM_GODOT = Path(
    "C:/Program Files (x86)/Steam/steamapps/common/Godot Engine/"
    "godot.windows.opt.tools.64.exe"
)


def constrain_cpu_affinity() -> list[int]:
    process = psutil.Process()
    available = process.cpu_affinity()
    selected = available[: min(3, len(available))]
    if not selected:
        raise RuntimeError("No logical CPUs are available to the inspection process")
    process.cpu_affinity(selected)
    return selected


def engine_version(engine: Path) -> str:
    result = subprocess.run(
        [str(engine), "--version"],
        check=False,
        text=True,
        capture_output=True,
        errors="replace",
        timeout=30,
    )
    version = (result.stdout + result.stderr).strip().splitlines()
    if result.returncode != 0 or not version:
        raise RuntimeError(f"Could not read Godot version: {engine}")
    if not version[0].startswith("4.7"):
        raise RuntimeError(f"Human inspection requires Godot 4.7 or newer: {version[0]}")
    return version[0]


def prepare_fixture() -> None:
    harness.ARTIFACT_ROOT = ARTIFACT_ROOT
    harness.FIXTURE_ROOT = FIXTURE_ROOT
    for attempt in range(10):
        try:
            harness.prepare_fixture()
            break
        except PermissionError:
            if attempt == 9:
                raise
            time.sleep(0.5)
    project = FIXTURE_ROOT / "project.godot"
    harness.copy_file(
        ROOT / "tests" / "human_terrain_inspection_smoke.gd",
        FIXTURE_ROOT / "tests" / "human_terrain_inspection_smoke.gd",
    )
    project.write_text(
        "\n".join(
            [
                "config_version=5",
                "",
                "[application]",
                'config/name="World Transvoxel Human Terrain Inspection"',
                f'run/main_scene="{MAIN_SCENE}"',
                'config/features=PackedStringArray("4.7", "Forward Plus")',
                "",
                "[display]",
                "window/size/viewport_width=1280",
                "window/size/viewport_height=720",
                "window/size/mode=3",
                "window/stretch/mode=\"canvas_items\"",
                "",
                "[editor_plugins]",
                'enabled=PackedStringArray("res://addons/world_transvoxel_terrain/plugin.cfg")',
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Launch the authority-backed large-terrain human inspection fixture."
    )
    parser.add_argument("--godot", type=Path, default=STEAM_GODOT)
    parser.add_argument("--editor", action="store_true")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--wait", action="store_true")
    arguments = parser.parse_args()

    logical_cpus = constrain_cpu_affinity()
    engine = arguments.godot.resolve()
    if not engine.is_file():
        raise FileNotFoundError(engine)
    version = engine_version(engine)
    prepare_fixture()
    harness.run_import("4.7", engine)

    if arguments.prepare_only:
        print(
            "WT_TERRAIN_HUMAN_INSPECTION_READY "
            f"project={FIXTURE_ROOT} godot={version} logical_cpus={logical_cpus}"
        )
        return

    if arguments.smoke_test:
        result = subprocess.run(
            [str(engine), "--headless", "--path", str(FIXTURE_ROOT), "--script", SMOKE_SCRIPT],
            cwd=FIXTURE_ROOT,
            env={**os.environ, "WT_CPU_PROFILE": "balanced"},
            check=False,
            text=True,
            capture_output=True,
            errors="replace",
            timeout=120,
        )
        combined = result.stdout + result.stderr
        print(combined, end="")
        if (
            result.returncode != 0
            or SMOKE_MARKER not in combined
            or harness.has_godot_error(combined)
        ):
            raise SystemExit(result.returncode or 1)
        return

    command = [
        str(engine),
        "--path",
        str(FIXTURE_ROOT),
        "--fullscreen",
    ]
    if arguments.editor:
        command.append("--editor")
    environment = os.environ.copy()
    environment["WT_CPU_PROFILE"] = "balanced"
    process = subprocess.Popen(command, cwd=FIXTURE_ROOT, env=environment)
    print(
        "WT_TERRAIN_HUMAN_INSPECTION_LAUNCHED "
        f"pid={process.pid} project={FIXTURE_ROOT} godot={version} "
        f"logical_cpus={logical_cpus}"
    )
    if arguments.wait:
        raise SystemExit(process.wait())


if __name__ == "__main__":
    main()
