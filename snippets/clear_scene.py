# 用途: シーンの全オブジェクトを削除（ライト・カメラ含めて完全クリア）
# 動作確認: 2026-05-04 / Blender MCP
# 依存: なし

import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
