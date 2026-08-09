#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
ADDON_ROOT = ROOT / "addons" / "world_transvoxel_terrain"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_bytes(path: Path) -> bytes:
    content = path.read_bytes()
    if b"\0" in content:
        return content
    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        return content
    return content.replace(b"\r\n", b"\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(path: Path) -> str:
    return hashlib.sha256(canonical_bytes(path)).hexdigest()


def git_output(repository: Path, *arguments: str) -> str:
    return subprocess.check_output(
        [
            "git",
            "-c",
            f"safe.directory={repository.as_posix()}",
            "-C",
            str(repository),
            *arguments,
        ],
        text=True,
    ).strip()


def tracked_addon_files() -> dict[PurePosixPath, Path]:
    prefix = ADDON_ROOT.relative_to(ROOT).as_posix()
    output = git_output(ROOT, "ls-files", "--", prefix)
    files: dict[PurePosixPath, Path] = {}
    for line in output.splitlines():
        repository_relative = PurePosixPath(line)
        package_relative = repository_relative.relative_to(prefix)
        path = ROOT / Path(repository_relative)
        if path.is_file():
            files[package_relative] = path
    return files


def package_digest(files: dict[PurePosixPath, Path] | None = None) -> str:
    value = hashlib.sha256()
    for relative, path in sorted((files or tracked_addon_files()).items()):
        value.update(str(relative).encode("utf-8"))
        value.update(b"\0")
        value.update(canonical_bytes(path))
        value.update(b"\0")
    return value.hexdigest()


def write_deterministic_addon_zip(output: Path) -> dict[str, object]:
    files = tracked_addon_files()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w") as archive:
        for relative, path in sorted(files.items()):
            archive_path = PurePosixPath("addons/world_transvoxel_terrain") / relative
            info = zipfile.ZipInfo(str(archive_path), date_time=(1980, 1, 1, 0, 0, 0))
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


def run_python(relative: str, *arguments: str) -> None:
    command = ["python", str(ROOT / relative), *arguments]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    output = result.stdout + result.stderr
    print(output, end="" if output.endswith("\n") else "\n")
    if result.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(command)}")
