# 用途: パラメトリックなシンプル椅子モデル（座面・脚4本・背もたれ・床）
# 動作確認: 2026-05-04 / Blender MCP
# 依存: scene_utils.py で reset_scene() を呼んでから使うのが楽

import bpy
import math

# パラメータ（後から調整しやすく定数化）
SEAT_W, SEAT_D, SEAT_T = 1.0, 1.0, 0.08
SEAT_H = 0.9
LEG_R = 0.06
BACK_W, BACK_D, BACK_H = 1.0, 0.06, 0.9


def add_rounded_box(name, location, scale, bevel_offset=0.04, bevel_segments=3):
    """指定サイズの角丸ボックスを生成して返す"""
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.active_object
    obj.scale = scale
    obj.name = name
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bevel(offset=bevel_offset, segments=bevel_segments, affect='EDGES')
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.shade_smooth()
    return obj


# 座面
seat = add_rounded_box("seat", (0, 0, SEAT_H), (SEAT_W, SEAT_D, SEAT_T))

# 4本の脚
leg_offset_x = SEAT_W / 2 - LEG_R * 1.5
leg_offset_y = SEAT_D / 2 - LEG_R * 1.5
for i, (sx, sy) in enumerate([(1, 1), (1, -1), (-1, 1), (-1, -1)]):
    bpy.ops.mesh.primitive_cylinder_add(
        radius=LEG_R,
        depth=SEAT_H,
        location=(sx * leg_offset_x, sy * leg_offset_y, SEAT_H / 2),
    )
    bpy.context.active_object.name = f"leg_{i+1}"
    bpy.ops.object.shade_smooth()

# 背もたれ
back = add_rounded_box(
    "backrest",
    (0, -SEAT_D / 2 + BACK_D / 2, SEAT_H + BACK_H / 2),
    (BACK_W, BACK_D, BACK_H),
)

# 床（影を出すため）
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
bpy.context.active_object.name = "floor"

# ライト & カメラ
bpy.ops.object.light_add(type='SUN', location=(4, -3, 8))
bpy.context.active_object.data.energy = 4
bpy.context.active_object.rotation_euler = (math.radians(45), math.radians(20), math.radians(30))

bpy.ops.object.camera_add(
    location=(2.8, -3.5, 1.6),
    rotation=(math.radians(75), 0, math.radians(38)),
)
bpy.context.scene.camera = bpy.context.active_object
