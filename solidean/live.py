from __future__ import annotations

import traceback
from dataclasses import dataclass

import bpy

from .utils import (
    BoolOperation,
    invalidate_mesh_cache,
    replace_mesh_data,
    run_boolean,
)


@dataclass
class LiveSession:
    """One result mesh tracked by the depsgraph handler, with the inputs and flags needed to refresh it."""

    result_obj: bpy.types.Object
    active: bpy.types.Object
    operand: bpy.types.Object
    bool_operation: BoolOperation
    bypass_cache: bool = False
    allow_self_intersections: bool = False
    heal_inputs: bool = False


_sessions: list[LiveSession] = []
_updating: bool = False  # re-entry guard: updating the result mesh triggers another depsgraph event


def _refresh(session: LiveSession) -> None:
    """Re-run the boolean for one session and write the result back into its output object."""
    positions, indices = run_boolean(
        session.active, session.operand, session.bool_operation,
        bypass_cache=session.bypass_cache,
        allow_self_intersections=session.allow_self_intersections,
        heal_inputs=session.heal_inputs,
    )
    replace_mesh_data(session.result_obj, positions, indices)


def _all_alive(*objects: bpy.types.Object) -> bool:
    """Return False if any object's underlying RNA has been freed (touching .name then raises)."""
    try:
        for o in objects:
            o.name
        return True
    except ReferenceError:
        return False


@bpy.app.handlers.persistent
def _on_depsgraph_update(scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph) -> None:
    """Refresh any live session whose inputs were transformed or had their geometry edited."""
    global _updating
    if _updating or not _sessions:
        return

    # Phase 1: collect what changed in this depsgraph tick. We iterate the
    # update list once and key by object name (rather than the bpy.types.Object
    # itself) because `update.id` is an evaluated copy from the depsgraph and
    # comparing against the orig object stored on the session is unreliable.
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

    # Phase 2: for each session, decide whether either input was touched
    # and refresh if so. Sessions whose inputs were deleted are reaped after
    # the loop — we can't mutate _sessions while iterating it.
    dead: list[LiveSession] = []
    for session in _sessions:
        if not _all_alive(session.active, session.operand, session.result_obj):
            dead.append(session)
            continue

        active_name = session.active.name
        operand_name = session.operand.name

        # Geometry edits invalidate the cached numpy arrays for that mesh;
        # transforms only need a re-run (the cached local-space data is still valid).
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
            # _refresh writes the result mesh, which fires another depsgraph
            # update — guard against re-entry so we don't recurse forever.
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
    allow_self_intersections: bool = False,
    heal_inputs: bool = False,
) -> None:
    """Begin tracking a result object so the depsgraph handler keeps it in sync with the inputs."""
    stop(result_obj)  # replace any existing session for this result object
    _sessions.append(
        LiveSession(
            result_obj=result_obj,
            active=active,
            operand=operand,
            bool_operation=bool_operation,
            bypass_cache=bypass_cache,
            allow_self_intersections=allow_self_intersections,
            heal_inputs=heal_inputs,
        )
    )


def stop(result_obj: bpy.types.Object) -> None:
    """Drop any sessions whose result object matches result_obj."""
    _sessions[:] = [s for s in _sessions if s.result_obj is not result_obj]


def register() -> None:
    """Attach the depsgraph handler if it isn't already attached."""
    if _on_depsgraph_update not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph_update)


def unregister() -> None:
    """Detach the depsgraph handler and discard all live sessions and cached mesh data."""
    if _on_depsgraph_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_on_depsgraph_update)
    _sessions.clear()
    invalidate_mesh_cache()
