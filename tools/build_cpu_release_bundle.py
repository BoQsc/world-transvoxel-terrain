#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import zipfile

import a4_phase3_terrain_world_lifecycle_smoke as harness
from tqp_release_common import ROOT, canonical_bytes, git_output, load_json, run_python, sha256, tracked_addon_files


CONTRACT_PATH = ROOT / "CPU_RELEASE_BUNDLE_CONTRACT.json"
ARTIFACT_ROOT = ROOT / "artifacts" / "cpu_release_bundle"
ZIP_PATH = ARTIFACT_ROOT / "world-transvoxel-terrain-cpu-1.1.0-rc1.zip"
MANIFEST_PATH = ARTIFACT_ROOT / "world-transvoxel-terrain-cpu-1.1.0-rc1.manifest.json"
REPORT_PATH = ARTIFACT_ROOT / "cpu_release_bundle_report.json"
FIXTURE_ROOT = ARTIFACT_ROOT / "clean_project"
SMOKE_SCRIPT = "res://tests/cpu_release_bundle_smoke.gd"
MARKER = "WT_TERRAIN_CPU_RELEASE_BUNDLE_GODOT_PASS"


def bundle_files(contract: dict[str, object]) -> dict[PurePosixPath, Path]:
    files: dict[PurePosixPath, Path] = {}
    terrain_prefix = PurePosixPath(contract["terrain_addon_root"])
    for relative, path in tracked_addon_files().items():
        files[terrain_prefix / relative] = path
    authority_root = ROOT.parent / contract["authority"]["repository"] / contract["authority"]["addon_root"]
    authority_prefix = PurePosixPath(contract["authority"]["addon_root"])
    for relative_text in contract["authority_runtime_files"]:
        relative = PurePosixPath(relative_text)
        path = authority_root.joinpath(*relative.parts)
        if not path.is_file():
            raise RuntimeError(f"release authority file is missing: {relative}")
        files[authority_prefix / relative] = path
    return files


def package_digest(files: dict[PurePosixPath, Path]) -> str:
    value = hashlib.sha256()
    for relative, path in sorted(files.items()):
        value.update(str(relative).encode("utf-8"))
        value.update(b"\0")
        value.update(canonical_bytes(path))
        value.update(b"\0")
    return value.hexdigest()


def write_bundle(output: Path, contract: dict[str, object]) -> dict[str, object]:
    files = bundle_files(contract)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w") as archive:
        for relative, path in sorted(files.items()):
            info = zipfile.ZipInfo(str(relative), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, canonical_bytes(path), compresslevel=9)
    return {
        "path": output.relative_to(ROOT).as_posix(),
        "files": len(files),
        "package_digest_sha256": package_digest(files),
        "zip_sha256": sha256(output),
        "zip_bytes": output.stat().st_size,
    }


def prepare_clean_project() -> None:
    if FIXTURE_ROOT.exists():
        shutil.rmtree(FIXTURE_ROOT)
    FIXTURE_ROOT.mkdir(parents=True)
    with zipfile.ZipFile(ZIP_PATH) as archive:
        archive.extractall(FIXTURE_ROOT)
    tests = FIXTURE_ROOT / "tests"
    tests.mkdir()
    shutil.copy2(ROOT / "tests/cpu_release_bundle_smoke.gd", tests)
    (FIXTURE_ROOT / "project.godot").write_text(
        "\n".join(
            [
                "config_version=5",
                "",
                "[application]",
                'config/name="World Transvoxel Terrain CPU Release Bundle Smoke"',
                'config/features=PackedStringArray("4.7", "Forward Plus")',
                "",
                "[editor_plugins]",
                'enabled=PackedStringArray("res://addons/world_transvoxel_terrain/plugin.cfg")',
                "",
            ]
        ),
        encoding="utf-8",
    )


def run_clean_smoke(engine: Path) -> dict[str, object]:
    environment = {**os.environ, "GODOT_AUDIO_DRIVER": "Dummy"}
    import_result = subprocess.run(
        [str(engine), "--headless", "--path", str(FIXTURE_ROOT), "--import"],
        cwd=FIXTURE_ROOT,
        check=False,
        text=True,
        capture_output=True,
        errors="replace",
        env=environment,
        timeout=180,
    )
    import_output = import_result.stdout + import_result.stderr
    (ARTIFACT_ROOT / "godot-4.7-clean-import.log").write_text(import_output, encoding="utf-8")
    extension_cache = FIXTURE_ROOT / ".godot/extension_list.cfg"
    if import_result.returncode != 0 or harness.has_godot_error(import_output):
        raise RuntimeError("clean release bundle import failed")
    if not extension_cache.is_file() or "world_transvoxel.gdextension" not in extension_cache.read_text(encoding="utf-8"):
        raise RuntimeError("clean release bundle did not discover the authority extension")
    smoke_result = subprocess.run(
        [str(engine), "--headless", "--path", str(FIXTURE_ROOT), "--script", SMOKE_SCRIPT],
        cwd=FIXTURE_ROOT,
        check=False,
        text=True,
        capture_output=True,
        errors="replace",
        env=environment,
        timeout=180,
    )
    output = smoke_result.stdout + smoke_result.stderr
    (ARTIFACT_ROOT / "godot-4.7-clean-smoke.log").write_text(output, encoding="utf-8")
    print(output, end="" if output.endswith("\n") else "\n")
    if smoke_result.returncode != 0 or MARKER not in output or harness.has_godot_error(output):
        raise RuntimeError("clean release bundle runtime smoke failed")
    return {
        "status": "PASS",
        "marker": next(line for line in output.splitlines() if line.startswith(MARKER)),
        "project": FIXTURE_ROOT.relative_to(ROOT).as_posix(),
        "sibling_repository_dependency": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot", type=Path, action="append", default=[])
    arguments = parser.parse_args()
    run_python("tools/validate_cpu_production_closure.py", "--require-report")
    contract = load_json(CONTRACT_PATH)
    authority = ROOT.parent / contract["authority"]["repository"]
    if git_output(authority, "rev-parse", "HEAD") != contract["authority"]["revision"]:
        raise RuntimeError("release bundle authority revision drifted")
    package = write_bundle(ZIP_PATH, contract)
    files = bundle_files(contract)
    manifest = {
        "schema": "world_transvoxel_terrain.cpu_release_bundle_manifest.v1",
        "release_id": contract["release_id"],
        "version": contract["version"],
        "terrain_revision": git_output(ROOT, "rev-parse", "HEAD"),
        "authority_revision": git_output(authority, "rev-parse", "HEAD"),
        "package": package,
        "files": [
            {"path": relative.as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)}
            for relative, path in sorted(files.items())
        ],
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    engines = harness.discover_engines(arguments.godot)
    if len(engines) != 1:
        raise RuntimeError("release bundle requires one Godot 4.7 executable")
    version, engine = engines[0]
    version_output = subprocess.check_output([str(engine), "--version"], text=True)
    if not version_output.startswith("4.7"):
        raise RuntimeError("release bundle smoke requires Godot 4.7")
    prepare_clean_project()
    smoke = run_clean_smoke(engine)
    report = {
        "schema": "world_transvoxel_terrain.cpu_release_bundle_evidence.v1",
        "milestone": "TQP-R06",
        "status": "PASS",
        "release_id": contract["release_id"],
        "version": contract["version"],
        "engine": version_output.strip(),
        "platform": contract["platform"],
        "architecture": contract["architecture"],
        "terrain_revision": git_output(ROOT, "rev-parse", "HEAD"),
        "authority_revision": git_output(authority, "rev-parse", "HEAD"),
        "package": package,
        "manifest": MANIFEST_PATH.relative_to(ROOT).as_posix(),
        "clean_install_smoke": smoke,
        "qualified_scope": contract["qualified_scope"],
        "explicitly_unqualified_scope": contract["explicitly_unqualified_scope"],
        "failures": [],
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    run_python("tools/validate_cpu_release_bundle.py", "--require-report")
    print(
        "WT_TERRAIN_CPU_RELEASE_BUNDLE_PASS "
        f"files={package['files']} bytes={package['zip_bytes']} zip={package['zip_sha256']}"
    )


if __name__ == "__main__":
    main()
