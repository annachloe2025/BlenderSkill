# 用途: bmesh で頂点を直接操作する基本パターン
# 動作確認: 2026-05-04 / Blender MCP
# 依存: scene_utils.py（clear_all 等）

import bpy
import bmesh
import math

# --- ① Cube の上面を縮めて台形化 ---
bpy.ops.mesh.primitive_cube_add(size=2)
obj = bpy.context.active_object

bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode='EDIT')

bm = bmesh.from_edit_mesh(obj.data)
for v in bm.verts:
    if v.co.z > 0:               # 上面の頂点だけ
        v.co.x *= 0.5             # 中心に寄せる
        v.co.y *= 0.5
bmesh.update_edit_mesh(obj.data)

bpy.ops.object.mode_set(mode='OBJECT')


# --- ② Plane を細分化して sin 波で凹凸を付ける ---
bpy.ops.mesh.primitive_plane_add(size=4)
obj = bpy.context.active_object

bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode='EDIT')

# 編集モード内で全選択 → サブディビ
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.subdivide(number_cuts=20)

bm = bmesh.from_edit_mesh(obj.data)
for v in bm.verts:
    dist = math.sqrt(v.co.x**2 + v.co.y**2)
    v.co.z = math.sin(dist * 3) * 0.3
bmesh.update_edit_mesh(obj.data)

bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.shade_smooth()
