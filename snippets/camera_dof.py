# 用途: カメラに被写界深度（DoF）を設定して作品風レンダリング
# 動作確認: 2026-05-04 / Blender MCP

import bpy
import math

cam = bpy.context.scene.camera   # 既存のアクティブカメラを取得
cam.data.lens = 50.0             # 焦点距離（mm）。35=広角、50=標準、85=ポートレート
cam.data.dof.use_dof = True
cam.data.dof.aperture_fstop = 2.0    # 小さいほどぼけが強い（f/1.4で大ボケ、f/8でほぼ全焦点）

# フォーカスの当て方は2通り:
# (A) 距離指定: cam.data.dof.focus_distance = 3.0
# (B) オブジェクト指定（移動に追従して常にピント）:
target_obj = bpy.data.objects.get("sphere_0")
if target_obj:
    cam.data.dof.focus_object = target_obj
