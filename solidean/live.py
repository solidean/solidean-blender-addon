from __future__ import annotations

import traceback
from dataclasses import dataclass

import bpy

from .utils import (
    BoolOperation,
    build_mesh_from_arrays,
    invalidate_mesh_cache,
    run_boolean,
)


@dataclass
class LiveSession:
    result_obj: bpy.types.Object
    active: bpy.types.Object
    operand: bpy.types.Object
    bool_operation: BoolOperation
    bypass_cache: bool = False


_sessions: list[LiveSession] = []
_updating: bool = False  # re-entry guard: updating the result mesh triggers another depsgraph event


def _replace_mesh(result_obj: bpy.types.Object, positions_f32, tri_indices) -> None:
    old_mesh = result_obj.data
    name = old_mesh.name
    new_mesh = bpy.data.meshes.new("__solidean_live_tmp__")
    build_mesh_from_arrays(new_mesh, positions_f32, tri_indices)
    result_obj.data = new_mesh
    bpy.data.meshes.remove(old_mesh)
    new_mesh.name = name


def _refresh(session: LiveSession) -> None:
    positions, indices = run_boolean(
        session.active, session.operand, session.bool_operation,
        bypass_cache=session.bypass_cache,
    )
    _replace_mesh(session.result_obj, positions, indices)


def _all_alive(*objects: bpy.types.Object) -> bool:
    """Return False if any object's underlying RNA has been freed."""
    try:
        for o in objects:
            o.name
        return True
    except ReferenceError:
        return False


@bpy.app.handlers.persistent
def _on_depsgraph_update(scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph) -> None:
    global _updating
    if _updating or not _sessions:
        return

    updated_transforms: set[str] = set()
    updated_geometry: set[str] = set()
    for update in depsgraph.updates:
        if isinstance(update.id, bpy.types.Object):
            if update.is_updated_transform:
                updated_transforms.add(update.id.name)
            if update.is_updated_geometry:
                updated_geometry.add(update.id.name)

    if not (updated_transforms or updated_geometry):
        return

    dead: list[LiveSession] = []
    for session in _sessions:
        if not _all_alive(session.active, session.operand, session.result_obj):
            dead.append(session)
            continue

        active_name = session.active.name
        operand_name = session.operand.name

        needs_refresh = False
        if active_name in updated_geometry:
            invalidate_mesh_cache(session.active.data)
            needs_refresh = True
        if operand_name in updated_geometry:
            invalidate_mesh_cache(session.operand.data)
            needs_refresh = True
        if active_name in updated_transforms or operand_name in updated_transforms:
            needs_refresh = True

        if needs_refresh:
            _updating = True
            try:
                _refresh(session)
            except Exception:
                # Without this, live-update errors are silently dropped and the
                # mesh stops updating with no console feedback.
                traceback.print_exc()
            finally:
                _updating = False

    for s in dead:
        _sessions.remove(s)


def start(
    active: bpy.types.Object,
    operand: bpy.types.Object,
    result_obj: bpy.types.Object,
    bool_operation: BoolOperation,
    bypass_cache: bool = False,
) -> None:
    stop(result_obj)  # replace any existing session for this result object
    _sessions.append(LiveSession(result_obj, active, operand, bool_operation, bypass_cache))


def stop(result_obj: bpy.types.Object) -> None:
    _sessions[:] = [s for s in _sessions if s.result_obj is not result_obj]


def register() -> None:
    if _on_depsgraph_update not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph_update)


def unregister() -> None:
    if _on_depsgraph_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_on_depsgraph_update)
    _sessions.clear()
    invalidate_mesh_cache()
