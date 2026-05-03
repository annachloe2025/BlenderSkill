# 用途: Boolean モディファイアで Cube に円柱で穴を開ける（ブーリアン入門）
# 動作確認: 2026-05-04 / Blender MCP

import bpy
import math

# ベース Cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
base = bpy.context.active_object
base.name = "block"

# カッター（X軸方向に貫通する円柱）
bpy.ops.mesh.primitive_cylinder_add(
    radius=0.5,
    depth=4,
    location=(0, 0, 1),
    rotation=(0, math.radians(90), 0),
)
cutter = bpy.context.active_object
cutter.name = "cutter"

# Boolean DIFFERENCE で穴を抜く
bpy.context.view_layer.objects.active = base
m = base.modifiers.new(name="Hole", type='BOOLEAN')
m.operation = 'DIFFERENCE'   # 'UNION' / 'INTERSECT' も同様に使える
m.object = cutter
m.solver = 'EXACT'           # 'FAST' より綺麗（重め）

# モディファイアを適用 → 切り取り側を削除
bpy.ops.object.modifier_apply(modifier="Hole")
bpy.data.objects.remove(cutter, do_unlink=True)

# 仕上げのベベル
bpy.context.view_layer.objects.active = base
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.bevel(offset=0.03, segments=2, affect='EDGES')
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.shade_smooth()
