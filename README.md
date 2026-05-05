# Solidean Blender Plugin

Exact mesh boolean operations for Blender 5.1+, powered by [Solidean](https://solidean.com).

## Features

- **Intersect**, **Union**, and **Difference** boolean operations
- Exact arithmetic — no floating-point errors or mesh artifacts
- Popup dialog with operand picker (Shift+E shortcut)
- Auto-picks the operand from the current selection (active = subject, other selected mesh = operand)
- **Live Update** — result re-evaluates as you transform either input
- **Bypass Cache** — fallback for the rare case where third-party plugins mutate mesh data without notifying Blender's depsgraph (see Usage)
- Accessible from the Object menu in the 3D viewport

## Requirements

- Blender 5.1 or later
- Solidean native library (`solidean.dll` on Windows, `libsolidean.so` on Linux, `libsolidean.dylib` on macOS)

## Project Structure

```
solidean/                         # Blender extension package
  __init__.py                     # Addon entry point (operator, UI, Blender integration)
  blender_manifest.toml           # Blender 5.1+ extension manifest
  live.py                         # Depsgraph handler driving live updates
  utils.py                        # Mesh <-> numpy conversion, run_boolean
  solidean.py                     # Solidean Python SDK (auto-generated, do not edit)
  solidean.dll                    # Solidean native library (add this — or .so / .dylib)
```

## Installation

1. [Download the Solidean native library](https://solidean.com/download/solidean/) for your OS and place it inside the `solidean/` folder next to `__init__.py` (see [Project Structure](#project-structure)).
   Note: Solidean is commercial software and generally requires a paid license — see [solidean.com](https://solidean.com) for terms and trial availability.
2. Build `solidean.zip`. The build scripts verify that all required files
   (including the native library) are present before zipping:
   - Windows (PowerShell): `./build.ps1`
   - macOS / Linux: `./build.sh`
3. In Blender, go to **Edit > Preferences > Add-ons**.
4. Click **Install from Disk** and select `solidean.zip`.
5. Enable the **Solidean** addon in the list.

## Usage

1. Select two mesh objects: the **active object** is the subject, the other
   selected mesh is auto-picked as the **operand**. (You can also select just
   the active and pick the operand manually in the dialog.)
2. Press **Shift+E** or go to **Object > Solidean** in the 3D viewport menu.
3. In the popup dialog:
   - Choose a boolean operation (Intersect / Union / Difference).
   - Confirm or change the **operand** mesh.
   - **Live Update** (on by default) keeps the result in sync as you
     transform either input. Turn it off for a one-shot bake — the inputs
     are then hidden and the result becomes the active selection.
   - **Bypass Cache** forces a fresh mesh extraction on every run; leave off
     for normal use. In Live Update mode we cache each input in our internal
     format because copying mesh data out of Blender every frame is expensive,
     and we only re-read an input when it actually changes. We detect changes
     via Blender's depsgraph update notifications (the `is_updated_geometry`
     flag on `bpy.types.DepsgraphUpdate`). Native Blender operations set this
     correctly, but some third-party plugins mutate mesh data without going
     through the depsgraph, so the change is invisible to us and the cache
     goes stale. If a result looks wrong while live-updating alongside such
     a plugin, enable Bypass Cache.
4. Click **OK** to execute. The result appears as a new object.

## Development

For development you most likely want to directly edit the files installed into
Blender's user extensions directory (the copy Blender actually loads, not the
files in this repo). To apply changes, run **Blender > System > Reload Scripts**.

For debugging, **Window > Toggle System Console** can be helpful.

### VS Code: Blender Development extension (recommended)

The [Blender Development](https://marketplace.visualstudio.com/items?itemName=JacquesLucke.blender-development)
extension by Jacques Lucke streamlines this workflow — it launches Blender
with the addon installed, attaches a Python debugger, and reloads the addon
on demand without restarting Blender.

1. Install **Blender Development** from the VS Code marketplace.
2. Open this repo in VS Code.
3. Command Palette → **Blender: Start**, then point it at your `blender.exe`
   on first run.
4. Save any plugin file — the addon reloads automatically (this repo ships a
   `.vscode/settings.json` with `blender.addon.reloadOnSave` enabled). You can
   also trigger it manually via **Blender: Reload Addons**.
5. Set breakpoints in VS Code; they hit when the operator runs in Blender.

## License

The Python addon code in this repository is licensed under the MIT license
(see `LICENSE`). The required Solidean native library is proprietary
software distributed separately — see [solidean.com](https://solidean.com)
for terms.
