from __future__ import annotations

from typing import Literal

import bpy
import numpy as np
import numpy.typing as npt

from . import solidean

BoolOperation = Literal["INTERSECT", "UNION", "DIFFERENCE"]
MeshStatus = Literal["solid", "self-intersections", "needs-healing"]

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
    """Return the process-wide solidean Context, creating it on first call."""
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
    mesh.polygons.foreach_set("use_smooth", np.zeros(n_tris, dtype=bool))

    mesh.update(calc_edges=True)


def _extract_indexed_triangles(me: bpy.types.Mesh) -> CachedMesh:
    """Read local-space positions and triangle indices straight from a Blender mesh."""
    me.calc_loop_triangles()
    n_verts = len(me.vertices)
    positions_local = np.empty(n_verts * 3, dtype=np.float32)
    me.vertices.foreach_get("co", positions_local)
    positions_local = positions_local.reshape(n_verts, 3)

    n_tris = len(me.loop_triangles)
    indices = np.empty(n_tris * 3, dtype=np.int32)
    me.loop_triangles.foreach_get("vertices", indices)
    return positions_local, indices


def mesh_to_indexed_triangles(obj: bpy.types.Object) -> CachedMesh:
    """Return world-space vertex positions and flat triangle index array for obj.

    Caches local-space positions/indices per Mesh datablock; only re-applies
    the world transform on cache hits. The depsgraph handler in live.py is
    responsible for invalidation on geometry edits.
    """
    me = obj.data
    cached = _mesh_cache.get(me.session_uid)

    if cached is None:
        cached = _extract_indexed_triangles(me)
        _mesh_cache[me.session_uid] = cached

    positions_local, indices = cached
    mat = np.array(obj.matrix_world, dtype=np.float32)
    positions = np.ascontiguousarray(positions_local @ mat[:3, :3].T + mat[:3, 3])
    return positions, indices


def replace_mesh_data(
    obj: bpy.types.Object,
    positions_f32: npt.NDArray[np.float32],
    tri_indices: npt.NDArray[np.int32],
) -> None:
    """Swap obj's mesh datablock for fresh geometry, dropping the cache entry for the old mesh."""
    old_mesh = obj.data
    name = old_mesh.name
    # Drop the stale cache entry now; the new mesh's session_uid is fresh
    # so its first read will re-extract from Blender naturally.
    invalidate_mesh_cache(old_mesh)
    # Build under a temporary name and rename only after old_mesh is removed —
    # if both shared the target name simultaneously, Blender would uniquify
    # the new one (e.g. "Cube" -> "Cube.001") and we'd lose the original name.
    new_mesh = bpy.data.meshes.new("__solidean_tmp__")
    build_mesh_from_arrays(new_mesh, positions_f32, tri_indices)
    obj.data = new_mesh
    bpy.data.meshes.remove(old_mesh)
    new_mesh.name = name


def _input_mesh_type(
    *, allow_self_intersections: bool, heal_inputs: bool
) -> solidean.MeshType:
    """Pick the loosest MeshType implied by the user's solver flags.

    Heal requires NonSupersolid input; otherwise self-intersections need
    Supersolid; the strictest Solid is the fast default.
    """
    if heal_inputs:
        return solidean.MeshType.NonSupersolid
    if allow_self_intersections:
        return solidean.MeshType.Supersolid
    return solidean.MeshType.Solid


def run_boolean(
    active: bpy.types.Object,
    operand: bpy.types.Object,
    bool_operation: BoolOperation,
    bypass_cache: bool = False,
    allow_self_intersections: bool = False,
    heal_inputs: bool = False,
) -> CachedMesh:
    """Run a solidean boolean and return (positions_f32, indices_int32)."""
    ctx = get_context()

    if bypass_cache:
        invalidate_mesh_cache(active.data)
        invalidate_mesh_cache(operand.data)

    verts_a, indices_a = mesh_to_indexed_triangles(active)
    verts_b, indices_b = mesh_to_indexed_triangles(operand)

    # Pick a coordinate bound for the exact arithmetic kernel. 1.5x the
    # observed max gives headroom for intermediate vertices generated by
    # the boolean (which can lie slightly outside both input AABBs); the
    # 10.0 floor keeps tiny meshes from collapsing to a degenerate kernel.
    max_coord = max(float(np.abs(verts_a).max()), float(np.abs(verts_b).max()))
    max_coord = max(max_coord * 1.5, 10.0)
    arithmetic = ctx.create_exact_arithmetic(max_coord)

    mesh_type = _input_mesh_type(
        allow_self_intersections=allow_self_intersections,
        heal_inputs=heal_inputs,
    )

    # Build a command buffer: import both inputs, optionally heal, then
    # combine. The `with` block executes the buffer on exit.
    with ctx.create_operation(arithmetic) as op:
        mA = op.import_from_indexed_triangles_f32(verts_a, indices_a, mesh_type=mesh_type)
        mB = op.import_from_indexed_triangles_f32(verts_b, indices_b, mesh_type=mesh_type)

        if heal_inputs:
            mA = op.heal(mA)
            mB = op.heal(mB)

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


def check_mesh(obj: bpy.types.Object) -> MeshStatus:
    """Classify a Blender mesh as solid, self-intersecting, or in need of healing."""
    ctx = get_context()
    verts, indices = mesh_to_indexed_triangles(obj)

    max_coord = max(float(np.abs(verts).max()) if verts.size else 0.0, 10.0) * 1.5
    arithmetic = ctx.create_exact_arithmetic(max_coord)

    # NonSupersolid is the most permissive type, which is what query_is_supersolid
    # requires; query_is_solid also accepts it. Stricter types would make one or
    # both queries trivially true.
    with ctx.create_operation(arithmetic) as op:
        m = op.import_from_indexed_triangles_f32(
            verts, indices, mesh_type=solidean.MeshType.NonSupersolid
        )
        is_supersolid_blob = op.query_is_supersolid(m)
        is_solid_blob = op.query_is_solid(m)

    # Order matters: a non-supersolid mesh has no defined "solid"-ness yet,
    # so check supersolidity first and only then narrow to the solid case.
    if not is_supersolid_blob.query_result_bool:
        return "needs-healing"
    if not is_solid_blob.query_result_bool:
        return "self-intersections"
    return "solid"


def heal_mesh(obj: bpy.types.Object) -> None:
    """Replace obj's mesh data with a Heal+SelfUnion'd solid version of itself.

    Operates entirely in local space so the result drops back into the mesh
    datablock unchanged by obj.matrix_world.
    """
    ctx = get_context()
    # Read directly from the mesh (skipping mesh_to_indexed_triangles) because
    # we need local-space coords — replace_mesh_data writes vertices straight
    # into obj.data, where the renderer applies matrix_world on top.
    verts_local, indices = _extract_indexed_triangles(obj.data)

    max_coord = max(float(np.abs(verts_local).max()) if verts_local.size else 0.0, 10.0) * 1.5
    arithmetic = ctx.create_exact_arithmetic(max_coord)

    with ctx.create_operation(arithmetic) as op:
        m = op.import_from_indexed_triangles_f32(
            verts_local, indices, mesh_type=solidean.MeshType.NonSupersolid
        )
        # Heal turns "bad input" into a supersolid mesh; SelfUnion then
        # collapses overlaps so the result is a true solid (per the
        # combination recommended in the Solidean docs).
        m = op.self_union(op.heal(m))
        blob = op.export_to_indexed_triangles_f32(m)

    try:
        new_positions = blob.positions_f32
        new_indices = blob.get_data(solidean.DataSlot.TrianglesIndexed).view(np.int32)
    except TypeError:
        # Same NULL-pointer signal as run_boolean — empty result.
        new_positions = np.empty(0, dtype=np.float32)
        new_indices = np.empty(0, dtype=np.int32)

    replace_mesh_data(obj, new_positions, new_indices)
