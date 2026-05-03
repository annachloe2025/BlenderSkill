# 用途: キーフレームアニメーション基本（移動・回転）
# 動作確認: 2026-05-04 / Blender MCP

import bpy
import math

obj = bpy.context.active_object   # 対象オブジェクト

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 60
scene.render.fps = 24

# フレーム1: 初期状態
obj.location = (0, 0, 1)
obj.rotation_euler = (0, 0, 0)
obj.keyframe_insert(data_path="location",       frame=1)
obj.keyframe_insert(data_path="rotation_euler", frame=1)

# フレーム30: 中間ポーズ
obj.location = (0, 0, 1.8)
obj.rotation_euler = (0, 0, math.radians(180))
obj.keyframe_insert(data_path="location",       frame=30)
obj.keyframe_insert(data_path="rotation_euler", frame=30)

# フレーム60: 最終ポーズ（ループ可能にするため初期と同じ）
obj.location = (0, 0, 1)
obj.rotation_euler = (0, 0, math.radians(360))
obj.keyframe_insert(data_path="location",       frame=60)
obj.keyframe_insert(data_path="rotation_euler", frame=60)

# 単一フレームをレンダリング: scene.frame_set(N) → render
# 動画レンダリング: scene.render.image_settings.file_format = 'FFMPEG' など
