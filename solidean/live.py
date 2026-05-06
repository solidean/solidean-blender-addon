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
    active_display_type: str = "SOLID"  # original values captured at start() so stop() can restore them
    operand_display_type: str = "SOLID"


_sessions: list[LiveSession] = []
_updating: bool = False  # re-entry guard: updating the result mesh triggers another depsgraph event
_last_frame: int = globals().get("_last_frame", -1)  # frame seen on last depsgraph tick


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
def _on_frame_change(scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph) -> None:
    """Refresh all live sessions on frame changes (animation playback)."""
    global _updating
    if _updating or not _sessions:
        return
    dead: list[LiveSession] = []
    _updating = True
    try:
        for session in _sessions:
            if not _all_alive(session.active, session.operand, session.result_obj):
                dead.append(session)
                continue
            try:
                _refresh(session)
            except Exception:
                traceback.print_exc()
    finally:
        _updating = False
    for s in dead:
        _sessions.remove(s)
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


@bpy.app.handlers.persistent
def _on_depsgraph_update(scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph) -> None:
    """Refresh any live session whose inputs were transformed or had their geometry edited."""
    global _updating, _last_frame
    if _updating or not _sessions:
        return

    # Phase 1: collect what changed in this depsgraph tick. We iterate the
    # update list once and key by object name (rather than the bpy.types.Object
    # itself) because `update.id` is an evaluated copy from the depsgraph and
    # comparing against the orig object stored on the session is unreliable.
    #
    # Frame changes during animation don't produce per-Object transform entries —
    # Blender reports a Scene update instead. Detect them by comparing the frame
    # counter so animated inputs are caught the same way as interactive moves.
    current_frame = scene.frame_current
    frame_changed = current_frame != _last_frame
    _last_frame = current_frame

    updated_transforms: set[str] = set()
    updated_geometry: set[str] = set()
    for update in depsgraph.updates:
        if isinstance(update.id, bpy.types.Object):
            if update.is_updated_transform:
                updated_transforms.add(update.id.name)
            if update.is_updated_geometry:
                updated_geometry.add(update.id.name)

    if not (frame_changed or updated_transforms or updated_geometry):
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
        needs_refresh = frame_changed
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
        # Restore input object display types and enable depth check for result object
        for obj, display_type in (
            (s.active, s.active_display_type),
            (s.operand, s.operand_display_type),
        ):
            try:
                obj.display_type = display_type
            except ReferenceError:
                pass
        try:
            s.result_obj.show_in_front = False
        except ReferenceError:
            pass


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
            active_display_type=active.display_type,  # capture before overwriting
            operand_display_type=operand.display_type,
        )
    )
    # Inputs show as wire while live so the result stays visually dominant
    active.display_type = "WIRE"
    operand.display_type = "WIRE"
    result_obj.show_in_front = True


def stop(result_obj: bpy.types.Object) -> None:
    """Drop any sessions whose result object matches result_obj, restoring input display types."""
    for s in _sessions:
        if s.result_obj is result_obj:
            try:
                s.active.display_type = s.active_display_type
                s.operand.display_type = s.operand_display_type
                result_obj.show_in_front = False
            except ReferenceError:
                pass
            break
    _sessions[:] = [s for s in _sessions if s.result_obj is not result_obj]


def has_session(result_obj: bpy.types.Object) -> bool:
    """Return True if result_obj is currently tracked by a live session."""
    return any(s.result_obj is result_obj for s in _sessions)


def register() -> None:
    """Attach the depsgraph and frame-change handlers if they aren't already attached."""
    if _on_depsgraph_update not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph_update)
    if _on_frame_change not in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.append(_on_frame_change)


def unregister() -> None:
    """Detach all handlers and discard all live sessions and cached mesh data."""
    if _on_depsgraph_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_on_depsgraph_update)
    if _on_frame_change in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(_on_frame_change)
    _sessions.clear()
    invalidate_mesh_cache()
