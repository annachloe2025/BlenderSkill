# 用途: NxN グリッド配置（ループでオブジェクトを大量生成する基本パターン）
# 動作確認: 2026-05-04 / Blender MCP
# 依存: clear_scene.py

import bpy
import math

N = 5
spacing = 1.5

for ix in range(N):
    for iy in range(N):
        x = (ix - (N - 1) / 2) * spacing  # 中心を原点に
        y = (iy - (N - 1) / 2) * spacing
        # 中心からの距離で高さを変える（波模様）
        dist = math.sqrt(x**2 + y**2)
        z = math.sin(dist * 1.2) * 0.6

        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.4, location=(x, y, z))
        obj = bpy.context.active_object
        obj.name = f"grid_{ix}_{iy}"
        bpy.ops.object.shade_smooth()
