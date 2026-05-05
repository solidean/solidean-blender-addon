from __future__ import annotations

from typing import Literal

import bpy
import numpy as np
import numpy.typing as npt

from . import solidean

BoolOperation = Literal["INTERSECT", "UNION", "DIFFERENCE"]

CachedMesh = tuple[npt.NDArray[np.float32], npt.NDArray[np.int32]]

# Preserved across module reloads. importlib.reload re-executes the module
# body in the existing __dict__, so reading the prior value out of globals()
# keeps the live Context (and its DLL handle) alive. Without this, reloading
# utils.py orphans the old Context, GC frees its native handle, and the next
# DLL call crashes with an access violation. The mesh cache is preserved for
# the same reason — its session_uid keys remain valid for the whole Blender
# session, not just one addon load.
_ctx: "solidean.Context | None" = globals().get("_ctx", None)
_mesh_cache: dict[int, CachedMesh] = globals().get("_mesh_cache", {})


def get_context() -> "solidean.Context":
    global _ctx
    if _ctx is None:
        _ctx = solidean.Context.create()
    return _ctx


def invalidate_mesh_cache(me: bpy.types.Mesh | None = None) -> None:
    """Drop cached local-space mesh data. Pass None to clear all entries."""
    if me is None:
        _mesh_cache.clear()
    else:
        _mesh_cache.pop(me.session_uid, None)


def build_mesh_from_arrays(
    mesh: bpy.types.Mesh,
    positions_f32: npt.NDArray[np.float32],
    tri_indices: npt.NDArray[np.int32],
) -> None:
    """Populate an empty Blender mesh from flat numpy arrays via foreach_set."""
    n_verts = positions_f32.size // 3
    n_tris = tri_indices.size // 3

    if n_tris == 0:
        # The per-loop `.corner_vert` attribute only exists once loops have
        # been added, so for an empty result we can't go through the rest of
        # this function.
        mesh.update()
        return

    mesh.vertices.add(n_verts)
    mesh.vertices.foreach_set("co", positions_f32.ravel())

    mesh.loops.add(n_tris * 3)
    mesh.attributes[".corner_vert"].data.foreach_set("value", tri_indices.ravel())

    mesh.polygons.add(n_tris)
    mesh.polygons.foreach_set("loop_start", np.arange(0, n_tris * 3, 3, dtype=np.int32))
    mesh.polygons.foreach_set("loop_total", np.full(n_tris, 3, dtype=np.int32))

    mesh.update(calc_edges=True)


def mesh_to_indexed_triangles(obj: bpy.types.Object) -> CachedMesh:
    """Return world-space vertex positions and flat triangle index array for obj.

    Caches local-space positions/indices per Mesh datablock; only re-applies
    the world transform on cache hits. The depsgraph handler in live.py is
    responsible for invalidation on geometry edits.
    """
    me = obj.data
    cached = _mesh_cache.get(me.session_uid)

    if cached is None:
        me.calc_loop_triangles()
        n_verts = len(me.vertices)
        positions_local = np.empty(n_verts * 3, dtype=np.float32)
        me.vertices.foreach_get("co", positions_local)
        positions_local = positions_local.reshape(n_verts, 3)

        n_tris = len(me.loop_triangles)
        indices = np.empty(n_tris * 3, dtype=np.int32)
        me.loop_triangles.foreach_get("vertices", indices)

        cached = (positions_local, indices)
        _mesh_cache[me.session_uid] = cached

    positions_local, indices = cached
    mat = np.array(obj.matrix_world, dtype=np.float32)
    positions = np.ascontiguousarray(positions_local @ mat[:3, :3].T + mat[:3, 3])
    return positions, indices


def run_boolean(
    active: bpy.types.Object,
    operand: bpy.types.Object,
    bool_operation: BoolOperation,
    bypass_cache: bool = False,
) -> CachedMesh:
    """Run a solidean boolean and return (positions_f32, indices_int32)."""
    ctx = get_context()

    if bypass_cache:
        invalidate_mesh_cache(active.data)
        invalidate_mesh_cache(operand.data)

    verts_a, indices_a = mesh_to_indexed_triangles(active)
    verts_b, indices_b = mesh_to_indexed_triangles(operand)

    max_coord = max(float(np.abs(verts_a).max()), float(np.abs(verts_b).max()))
    max_coord = max(max_coord * 1.5, 10.0)
    arithmetic = ctx.create_exact_arithmetic(max_coord)

    with ctx.create_operation(arithmetic) as op:
        mA = op.import_from_indexed_triangles_f32(verts_a, indices_a)
        mB = op.import_from_indexed_triangles_f32(verts_b, indices_b)

        match bool_operation:
            case "INTERSECT":
                mR = op.intersection(mA, mB)
            case "UNION":
                mR = op.union(mA, mB)
            case "DIFFERENCE":
                mR = op.difference(mA, mB)

        blob = op.export_to_indexed_triangles_f32(mR)

    try:
        positions = blob.positions_f32
        indices = blob.get_data(solidean.DataSlot.TrianglesIndexed).view(np.int32)
    except TypeError:
        # Empty result: the native side returns a NULL data pointer, which
        # bottoms out in ctypes.from_address(None) raising "integer expected".
        # has_data() is unreliable here (returns True even for zero-byte data),
        # so catching the TypeError is the only robust signal.
        return (
            np.empty(0, dtype=np.float32),
            np.empty(0, dtype=np.int32),
        )
    return positions, indices
