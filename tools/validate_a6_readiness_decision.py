#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "docs/A6_GAME_REPOSITORY_READINESS_DECISION.md",
    "tools/validate_a6_readiness_decision.py",
    "tools/a6_readiness_decision.py",
    "addons/world_transvoxel_terrain/plugin.cfg",
    "addons/world_transvoxel_terrain/README.md",
)

REQUIRED_PHRASES = {
    "docs/A6_GAME_REPOSITORY_READINESS_DECISION.md": (
        "Status: complete",
        "WT_TERRAIN_A6_CONTRACT_PASS",
        "WT_TERRAIN_A6_READINESS_DECISION_PASS",
        "approve_validation_game_repository",
        "package boundary, local smoke evidence, and stable minimal API",
        "must not fork or copy `world-transvoxel-sandbox`",
        "does not claim production-ready terrain",
        "separate validation game repository when the user explicitly asks",
    ),
    "IMPLEMENTATION_CHARTER.md": (
        "Current phase: TQP-51 through TQP-53 qualified",
        "Definition of done for A6",
        "approve_validation_game_repository",
    ),
    "docs/ROADMAP.md": (
        "## A6 - Game repository readiness decision",
        "Status: complete",
        "WT_TERRAIN_A6_READINESS_DECISION_PASS",
        "separate validation game repository when the user explicitly asks",
    ),
    "README.md": (
        "Status: TQP-51 through TQP-53 qualified",
        "WT_TERRAIN_A6_CONTRACT_PASS",
        "WT_TERRAIN_A6_READINESS_DECISION_PASS",
        "python tools/a6_readiness_decision.py",
    ),
    "addons/world_transvoxel_terrain/README.md": (
        "Current status: TQP-51 through TQP-53 qualified",
        "approve_validation_game_repository",
        "not yet a production-ready terrain package",
    ),
    "tools/a6_readiness_decision.py": (
        "WT_TERRAIN_A6_READINESS_DECISION_PASS",
        "WT_TERRAIN_A5_PHASE5_EXIT_REVIEW_PASS",
        "approve_validation_game_repository",
    ),
}

REQUIRED_API = {
    "addons/world_transvoxel_terrain/runtime/wt_terrain_world.gd": (
        "class_name WtTerrainWorld",
        "func start_backend_world()",
        "func stop_backend_world()",
        "func submit_edit_batch(",
        "func update_viewer(",
        "func remove_viewer(",
        "func query_chunk_state(",
        "func get_runtime_metrics()",
        "func is_cold_idle()",
        "func get_dependency_status()",
    ),
    "addons/world_transvoxel_terrain/api/wt_terrain_profile.gd": (
        "class_name WtTerrainProfile",
        "horizontal_cells: int = 2048",
        "vertical_cells: int = 128",
    ),
    "addons/world_transvoxel_terrain/generation/wt_terrain_generation_profile.gd": (
        "class_name WtTerrainGenerationProfile",
        "supports_underground_volume: bool = true",
    ),
    "addons/world_transvoxel_terrain/material/wt_terrain_material_profile.gd": (
        "class_name WtTerrainMaterialProfile",
        "texture_resolution",
        "shader_mode",
    ),
    "addons/world_transvoxel_terrain/storage/wt_terrain_storage_profile.gd": (
        "class_name WtTerrainStorageProfile",
        "edit_journal_path",
        "persist_edits: bool = true",
    ),
    "addons/world_transvoxel_terrain/storage/wt_terrain_recovery_policy.gd": (
        "class_name WtTerrainRecoveryPolicy",
        "automatic_timed_regeneration_enabled: bool = false",
        "fluid_equilibrium_enabled: bool = false",
    ),
    "addons/world_transvoxel_terrain/edit/wt_terrain_edit_operation.gd": (
        "class_name WtTerrainEditOperation",
        "enum Mode",
        "enum BrushShape",
        "func to_bridge_command()",
    ),
    "addons/world_transvoxel_terrain/edit/wt_terrain_edit_batch.gd": (
        "class_name WtTerrainEditBatch",
        "func add_operation(",
        "func to_bridge_commands()",
    ),
    "addons/world_transvoxel_terrain/debug/wt_terrain_reference_scene.gd": (
        "class_name WtTerrainReferenceScene",
        "func start_reference_backend_world()",
        "func update_reference_viewer(",
        "func get_debug_status_text()",
    ),
    "addons/world_transvoxel_terrain/debug/wt_terrain_debug_snapshot.gd": (
        "class_name WtTerrainDebugSnapshot",
        "static func capture(",
    ),
    "addons/world_transvoxel_terrain/debug/wt_terrain_debug_overlay_formatter.gd": (
        "class_name WtTerrainDebugOverlayFormatter",
        "static func format_snapshot(",
    ),
}

FORBIDDEN_TRACKED_PATHS = (
    "addons/world_transvoxel/",
    "thirdparty/transvoxel_mit/",
)


def has_phrase(text: str, phrase: str) -> bool:
    return phrase in text or phrase in " ".join(text.split())


def iter_repo_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        rel = relative.as_posix()
        if ".git" in relative.parts:
            continue
        if "__pycache__" in relative.parts:
            continue
        if rel.startswith("references/downloaded/"):
            continue
        if rel.startswith("artifacts/"):
            continue
        if path.is_file():
            files.append(relative)
    return files


def main() -> None:
    errors: list[str] = []

    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            errors.append(f"missing A6 readiness file: {relative}")

    for relative, phrases in REQUIRED_PHRASES.items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing phrase input: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if not has_phrase(text, phrase):
                errors.append(f"{relative} missing phrase: {phrase}")

    for relative, phrases in REQUIRED_API.items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing minimal API file: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if not has_phrase(text, phrase):
                errors.append(f"{relative} missing API phrase: {phrase}")

    plugin_cfg = (ROOT / "addons/world_transvoxel_terrain/plugin.cfg").read_text(
        encoding="utf-8"
    )
    if 'name="World Transvoxel Terrain"' not in plugin_cfg:
        errors.append("plugin.cfg missing stable addon name")
    if 'script="editor/world_transvoxel_terrain_plugin.gd"' not in plugin_cfg:
        errors.append("plugin.cfg missing editor script path")

    for relative in iter_repo_files():
        rel = relative.as_posix()
        for forbidden in FORBIDDEN_TRACKED_PATHS:
            if forbidden in rel:
                errors.append(f"forbidden dependency path in repo: {rel}")
        if relative.name in {"Transvoxel.cpp", "Transvoxel.h"}:
            errors.append(f"forbidden MIT Transvoxel source name in repo: {rel}")
        if relative.suffix in {".gd", ".glsl", ".gdshader"}:
            lines = (ROOT / relative).read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()
            if len(lines) > 300:
                errors.append(f"source file exceeds A6 limit: {rel}")

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        raise SystemExit(1)

    print(
        "WT_TERRAIN_A6_CONTRACT_PASS "
        "decision=approve_validation_game_repository "
        "implementation=readiness_decision "
        "next=separate_validation_game_repository_when_user_approves"
    )


if __name__ == "__main__":
    main()
