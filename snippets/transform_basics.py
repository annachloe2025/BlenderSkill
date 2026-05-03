# 用途: トランスフォーム（位置・回転・スケール）の基本パターン
# 動作確認: 2026-05-04 / Blender MCP
# 依存: clear_scene.py

import bpy
import math
from mathutils import Vector, Euler

# ① 直接タプル代入
bpy.ops.mesh.primitive_cube_add()
obj = bpy.context.active_object
obj.location = (1, 2, 0)
obj.rotation_euler = (math.radians(0), math.radians(45), math.radians(30))
obj.scale = (1.5, 0.5, 1.0)

# ② Vector / Euler を使った書き方（読みやすい）
bpy.ops.mesh.primitive_cube_add()
obj = bpy.context.active_object
obj.location       = Vector((3, 0, 1))
obj.rotation_euler = Euler((math.radians(20), 0, math.radians(45)), 'XYZ')
obj.scale          = Vector((1, 1, 1.8))

# 度数⇔ラジアン
deg = 45
rad = math.radians(deg)        # 0.785...
back = math.degrees(rad)       # 45.0
