# 用途: 5種類のプリミティブを X 軸に等間隔で並べて配置（基本シーン用）
# 動作確認: 2026-05-04 / Blender MCP
# 依存: clear_scene.py を先に実行するとクリーンに始められる

import bpy

primitives = [
    ("cube",     lambda: bpy.ops.mesh.primitive_cube_add(size=1)),
    ("sphere",   lambda: bpy.ops.mesh.primitive_uv_sphere_add(radius=0.6)),
    ("cylinder", lambda: bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1.2)),
    ("cone",     lambda: bpy.ops.mesh.primitive_cone_add(radius1=0.6, depth=1.2)),
    ("torus",    lambda: bpy.ops.mesh.primitive_torus_add(major_radius=0.5, minor_radius=0.18)),
]

spacing = 1.8
for i, (name, op) in enumerate(primitives):
    op()
    obj = bpy.context.active_object
    obj.name = name
    obj.location = ((i - (len(primitives) - 1) / 2) * spacing, 0, 0)

# 基本ライト＆カメラ
bpy.ops.object.light_add(type='SUN', location=(4, -4, 6))
bpy.context.active_object.data.energy = 3
bpy.ops.object.camera_add(location=(0, -8, 3), rotation=(1.2, 0, 0))
bpy.context.scene.camera = bpy.context.active_object
