# 用途: Plane を起点に「上 → 奥」を繰り返し押し出して階段状の形を作る
# 動作確認: 2026-05-04 / Blender MCP
# 依存: scene_utils.py（または事前にシーンクリア）

import bpy

bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "stairs"

bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')

STEP_RISE = 0.4   # 1段の高さ
STEP_RUN = 1.0    # 1段の奥行き

for i in range(5):
    # ① 上方向に押し出し（蹴上）
    bpy.ops.mesh.extrude_region_move(
        TRANSFORM_OT_translate={"value": (0, 0, STEP_RISE)}
    )
    # ② 奥方向に押し出し（踏み面）
    bpy.ops.mesh.extrude_region_move(
        TRANSFORM_OT_translate={"value": (0, STEP_RUN, 0)}
    )

bpy.ops.object.mode_set(mode='OBJECT')
