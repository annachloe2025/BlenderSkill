# 用途: Cube → ループカット（subdivide）→ 全エッジにベベル → スムーズシェード
# 動作確認: 2026-05-04 / Blender MCP

import bpy

bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
obj = bpy.context.active_object
obj.name = "rounded_box"

bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode='EDIT')

# ループカット相当（全エッジを一様に細分化）
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.subdivide(number_cuts=1)

# 全エッジに丸みベベル
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.bevel(
    offset_type='OFFSET',
    offset=0.15,        # ベベル幅
    segments=4,         # セグメント数（多いほど滑らか）
    profile=0.5,        # 0.5 = 円弧、1.0 = 鋭角
    affect='EDGES',
)

bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.shade_smooth()
