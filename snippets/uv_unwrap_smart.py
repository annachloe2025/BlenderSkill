# 用途: Smart UV Project でメッシュをUV展開する
# 動作確認: 2026-05-04 / Blender MCP
# 編集モードで全選択した状態で呼ぶ

import bpy

# 編集モードに入って全選択
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')

# Smart UV Project（角度ベースで自動展開）
# - angle_limit: シーム検出の閾値（度数）。低いほど分割が多い
# - island_margin: UVアイランド間の余白
bpy.ops.uv.smart_project(angle_limit=66, island_margin=0.02)

bpy.ops.object.mode_set(mode='OBJECT')
