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
from .utils import build_mesh_from_arrays, check_mesh, heal_mesh, run_boolean

_STATUS_LABELS: dict[str, str] = {
    "solid": "solid",
    "self-intersections": "has self-intersections",
    "needs-healing": "needs healing",
}

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


class SOLIDEAN_OT_heal_meshes(bpy.types.Operator):
    """Apply Solidean Heal + SelfUnion in place on the active object (and operand if set)"""

    bl_idname = "modifier.solidean_heal_meshes"
    bl_label = "Heal"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.active_object is not None and context.active_object.type == "MESH"

    def execute(self, context: bpy.types.Context) -> set[str]:
        """Heal the active object, plus the operand when one is set and distinct from the active."""
        active = context.active_object
        operand = context.scene.solidean_operand

        targets = [active]
        if operand is not None and operand != active:
            targets.append(operand)

        for obj in targets:
            try:
                heal_mesh(obj)
            except Exception as e:
                self.report({"ERROR"}, f"Heal failed for {obj.name}: {e}")
                return {"CANCELLED"}

        # Stale check labels would suggest the input still has its pre-heal status.
        context.scene.solidean_check_active_status = ""
        context.scene.solidean_check_operand_status = ""

        names = ", ".join(o.name for o in targets)
        self.report({"INFO"}, f"Healed: {names}")
        return {"FINISHED"}


class SOLIDEAN_OT_check_meshes(bpy.types.Operator):
    """Check the active object and operand for self-intersections or healing needs"""

    bl_idname = "modifier.solidean_check_meshes"
    bl_label = "Check Meshes"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.active_object is not None and context.active_object.type == "MESH"

    def execute(self, context: bpy.types.Context) -> set[str]:
        """Classify each input and stash the labels on the scene for the dialog to render."""
        scene = context.scene
        active = context.active_object
        operand = scene.solidean_operand

        try:
            scene.solidean_check_active_status = _STATUS_LABELS[check_mesh(active)]
        except Exception as e:
            scene.solidean_check_active_status = ""
            self.report({"ERROR"}, f"Check failed for {active.name}: {e}")
            return {"CANCELLED"}

        if operand is not None:
            try:
                scene.solidean_check_operand_status = _STATUS_LABELS[check_mesh(operand)]
            except Exception as e:
                scene.solidean_check_operand_status = ""
                self.report({"ERROR"}, f"Check failed for {operand.name}: {e}")
                return {"CANCELLED"}
        else:
            scene.solidean_check_operand_status = ""

        msg = f"Active: {scene.solidean_check_active_status}"
        if scene.solidean_check_operand_status:
            msg += f"; Operand: {scene.solidean_check_operand_status}"
        self.report({"INFO"}, msg)
        return {"FINISHED"}


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
    allow_self_intersections: bpy.props.BoolProperty(
        name="Allow Self-Intersections",
        description=(
            "Tell Solidean that the input meshes may have self-intersections. "
            "Has a performance penalty; only enable if needed"
        ),
    )
    heal_inputs: bpy.props.BoolProperty(
        name="Heal Inputs (experimental)",
        description=(
            "Run Solidean's Heal pass on each input before the boolean. "
            "Use for non-manifold meshes with holes or other defects"
        ),
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
        """Run the boolean once, create the result object, and arm a live session if requested."""
        operand = context.scene.solidean_operand
        active = context.active_object

        if operand is None:
            self.report({"ERROR"}, "No operand mesh selected")
            return {"CANCELLED"}

        try:
            result_positions, result_indices = run_boolean(
                active,
                operand,
                self.bool_operation,
                bypass_cache=self.bypass_cache,
                allow_self_intersections=self.allow_self_intersections,
                heal_inputs=self.heal_inputs,
            )

            result_name = f"{active.name}_{self.bool_operation.lower()}_{operand.name}"
            result_obj = _create_result_mesh(result_name, result_positions, result_indices)

            if self.live_update:
                # Hand the result over to the depsgraph handler so it tracks
                # input edits and re-runs the boolean automatically.
                live.start(
                    active,
                    operand,
                    result_obj,
                    self.bool_operation,
                    bypass_cache=self.bypass_cache,
                    allow_self_intersections=self.allow_self_intersections,
                    heal_inputs=self.heal_inputs,
                )
            else:
                # One-shot bake: hide the source meshes and promote the result
                # to active so the user immediately sees just the new object.
                active.hide_set(True)
                operand.hide_set(True)
                context.view_layer.objects.active = result_obj
                result_obj.select_set(True)

            # An empty result is a likely-but-valid outcome (e.g. intersection
            # of disjoint meshes). Surface it as a warning rather than success.
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
        """Render the operator's popup contents (or the post-execute hint)."""
        if self.is_done:
            self.layout.label(text="Shortcut: Ctrl+Shift+B to apply again", icon="LIGHT")
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
            box = col.box()
            box.prop(self, "allow_self_intersections")
            box.prop(self, "heal_inputs")
            check_row = box.row(align=True)
            check_row.operator(SOLIDEAN_OT_check_meshes.bl_idname, icon="VIEWZOOM")
            check_row.operator(SOLIDEAN_OT_heal_meshes.bl_idname, icon="MODIFIER_DATA")
            scene = context.scene
            active_status = scene.solidean_check_active_status
            operand_status = scene.solidean_check_operand_status
            if active_status:
                box.label(text=f"Active: {active_status}")
            if operand_status:
                box.label(text=f"Operand: {operand_status}")

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        """Pre-fill the operand from the current selection and open the props dialog."""
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


class SOLIDEAN_OT_stop_live(bpy.types.Operator):
    """Stop live update tracking for the active result object and restore input display"""

    bl_idname = "modifier.solidean_stop_live"
    bl_label = "Stop Live Update"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # Only show in the menu when the active object is a live result, so the entry doesn't clutter other contexts
        return context.active_object is not None and live.has_session(context.active_object)

    def execute(self, context: bpy.types.Context) -> set[str]:
        live.stop(context.active_object)
        return {"FINISHED"}


def menu_func(self, context: bpy.types.Context) -> None:
    """Append Solidean entries to the 3D viewport's Object menu."""
    self.layout.operator(SOLIDEAN_OT_boolean.bl_idname)
    if context.active_object is not None and live.has_session(context.active_object):
        self.layout.operator(SOLIDEAN_OT_stop_live.bl_idname)


def _operand_poll(self, obj: bpy.types.Object) -> bool:
    """Restrict the operand picker to other mesh objects in the current scene."""
    return (
        obj != bpy.context.active_object
        and obj.type == "MESH"
        and obj.name in bpy.context.scene.objects
    )


addon_keymaps: list[tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]] = []


def register() -> None:
    """Install scene properties, operators, the menu entry, and the Ctrl+Shift+B keymap."""
    bpy.types.Scene.solidean_operand = bpy.props.PointerProperty(
        name="Operand",
        poll=_operand_poll,
        type=bpy.types.Object,
    )
    bpy.types.Scene.solidean_check_active_status = bpy.props.StringProperty()
    bpy.types.Scene.solidean_check_operand_status = bpy.props.StringProperty()

    bpy.utils.register_class(SOLIDEAN_OT_check_meshes)
    bpy.utils.register_class(SOLIDEAN_OT_heal_meshes)
    bpy.utils.register_class(SOLIDEAN_OT_boolean)
    bpy.utils.register_class(SOLIDEAN_OT_stop_live)
    bpy.types.VIEW3D_MT_object.append(menu_func)
    live.register()

    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="Object Mode", space_type="EMPTY")
        kmi = km.keymap_items.new(
            SOLIDEAN_OT_boolean.bl_idname, "B", "PRESS", ctrl=True, shift=True
        )
        addon_keymaps.append((km, kmi))


def unregister() -> None:
    """Tear down everything register() set up, in reverse order."""
    live.unregister()

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bpy.utils.unregister_class(SOLIDEAN_OT_stop_live)
    bpy.utils.unregister_class(SOLIDEAN_OT_boolean)
    bpy.utils.unregister_class(SOLIDEAN_OT_heal_meshes)
    bpy.utils.unregister_class(SOLIDEAN_OT_check_meshes)
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    del bpy.types.Scene.solidean_operand
    del bpy.types.Scene.solidean_check_active_status
    del bpy.types.Scene.solidean_check_operand_status
