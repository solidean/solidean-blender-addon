from __future__ import annotations

import importlib
import sys

import bpy
import numpy as np
import numpy.typing as npt

# Force-reload submodules cached from a previous addon load. The Blender Dev
# VSCode extension's reload-on-save re-imports __init__.py fresh, so checking
# `if "utils" in locals()` misses the cached submodules and stale code keeps
# running. Reload via sys.modules in dependency order instead.
for _name in ("utils", "live"):
    _full = f"{__name__}.{_name}"
    if _full in sys.modules:
        importlib.reload(sys.modules[_full])

from . import live
from .utils import build_mesh_from_arrays, run_boolean


def _create_result_mesh(
    name: str,
    positions_f32: npt.NDArray[np.float32],
    tri_indices: npt.NDArray[np.int32],
) -> bpy.types.Object:
    """Create a new Blender mesh object from positions and triangle indices arrays."""
    mesh = bpy.data.meshes.new(name)
    build_mesh_from_arrays(mesh, positions_f32, tri_indices)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


class SOLIDEAN_OT_boolean(bpy.types.Operator):
    """Solidean - Exact Mesh Booleans"""

    bl_idname = "modifier.solidean_boolean"
    bl_label = "Solidean"
    bl_options = {"REGISTER", "UNDO"}

    bool_operation: bpy.props.EnumProperty(
        name="Boolean Operation",
        items=[
            ("INTERSECT", "Intersect", ""),
            ("UNION", "Union", ""),
            ("DIFFERENCE", "Difference", ""),
        ],
        description="Which boolean operation to apply",
        options=set(),
    )

    show_solver_options: bpy.props.BoolProperty(name="Solver Options")
    self_intersection: bpy.props.BoolProperty(
        name="Self Intersection",
        description="Enable if input meshes have self-intersections",
    )
    live_update: bpy.props.BoolProperty(
        name="Live Update",
        description="Re-run boolean whenever either input is transformed",
        default=True,
    )
    bypass_cache: bpy.props.BoolProperty(
        name="Bypass Cache",
        description="Re-extract mesh data from Blender on every run instead of using the cached arrays",
        default=False,
    )

    is_done: bpy.props.BoolProperty()

    def execute(self, context: bpy.types.Context) -> set[str]:
        operand = context.scene.solidean_operand
        active = context.active_object

        if operand is None:
            self.report({"ERROR"}, "No operand mesh selected")
            return {"CANCELLED"}

        try:
            result_positions, result_indices = run_boolean(
                active, operand, self.bool_operation, bypass_cache=self.bypass_cache
            )

            result_name = f"{active.name}_{self.bool_operation.lower()}_{operand.name}"
            result_obj = _create_result_mesh(result_name, result_positions, result_indices)

            if self.live_update:
                live.start(active, operand, result_obj, self.bool_operation, self.bypass_cache)
            else:
                active.hide_set(True)
                operand.hide_set(True)
                context.view_layer.objects.active = result_obj
                result_obj.select_set(True)

            n_tris = len(result_indices) // 3
            level = "WARNING" if n_tris == 0 else "INFO"
            self.report(
                {level},
                f"Boolean {self.bool_operation.lower()} completed: {n_tris} triangles",
            )

        except Exception as e:
            self.report({"ERROR"}, f"Solidean error: {e}")
            return {"CANCELLED"}

        self.is_done = True
        return {"FINISHED"}

    def draw(self, context: bpy.types.Context) -> None:
        if self.is_done:
            self.layout.label(text="Shortcut: Shift+E to apply again", icon="LIGHT")
            return

        layout = self.layout
        layout.label(text="Exact Mesh Booleans")

        col = layout.column()
        col.label(text=f"Active object: {context.active_object.name}")
        col.row().prop(self, "bool_operation", expand=True)
        col.prop(context.scene, "solidean_operand")
        row = col.row(align=True)
        row.prop(self, "live_update")
        row.prop(self, "bypass_cache")
        col.prop(
            self,
            "show_solver_options",
            text="Solver Options",
            icon="TRIA_DOWN" if self.show_solver_options else "TRIA_RIGHT",
        )

        if self.show_solver_options:
            col.box().prop(self, "self_intersection")

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        if context.active_object == context.scene.solidean_operand:
            context.scene.solidean_operand = None

        # Mirror Blender's own boolean tools: if exactly one other mesh is
        # selected alongside the active object, treat it as the operand.
        if context.scene.solidean_operand is None:
            candidates = [
                o for o in context.selected_objects
                if o != context.active_object and o.type == "MESH"
            ]
            if len(candidates) == 1:
                context.scene.solidean_operand = candidates[0]

        self.is_done = False
        return context.window_manager.invoke_props_dialog(self)

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.active_object is not None and context.active_object.type == "MESH"


def menu_func(self, context: bpy.types.Context) -> None:
    self.layout.operator(SOLIDEAN_OT_boolean.bl_idname)


def _operand_poll(self, obj: bpy.types.Object) -> bool:
    return (
        obj != bpy.context.active_object
        and obj.type == "MESH"
        and obj.name in bpy.context.scene.objects
    )


addon_keymaps: list[tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]] = []


def register() -> None:
    bpy.types.Scene.solidean_operand = bpy.props.PointerProperty(
        name="Operand",
        poll=_operand_poll,
        type=bpy.types.Object,
    )

    bpy.utils.register_class(SOLIDEAN_OT_boolean)
    bpy.types.VIEW3D_MT_object.append(menu_func)
    live.register()

    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="Object Mode", space_type="EMPTY")
        kmi = km.keymap_items.new(SOLIDEAN_OT_boolean.bl_idname, "E", "PRESS", shift=True)
        addon_keymaps.append((km, kmi))


def unregister() -> None:
    live.unregister()

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bpy.utils.unregister_class(SOLIDEAN_OT_boolean)
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    del bpy.types.Scene.solidean_operand
