# 用途: シーン管理ユーティリティ（毎回コピペで使う基本パターン群）
# 動作確認: 2026-05-04 / Blender MCP
# 依存: なし

import bpy
import math


def clear_all():
    """全オブジェクトを削除（ライト・カメラ含む）。Object Mode で実行する前提。"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def clear_meshes_only():
    """メッシュだけ削除。ライト・カメラは残す。"""
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    bpy.ops.object.delete()


def setup_basic_scene(sun_energy=3.0, cam_loc=(0, -8, 4), cam_pitch_deg=70):
    """空シーンに Sun ライト + アクティブカメラを追加。"""
    bpy.ops.object.light_add(type='SUN', location=(4, -4, 6))
    bpy.context.active_object.data.energy = sun_energy
    bpy.ops.object.camera_add(
        location=cam_loc,
        rotation=(math.radians(cam_pitch_deg), 0, 0),
    )
    bpy.context.scene.camera = bpy.context.active_object


def reset_scene():
    """全消し → 基本ライト・カメラ。学習セッションの定型スタート。"""
    clear_all()
    setup_basic_scene()


# 使用例:
# reset_scene()
# bpy.ops.mesh.primitive_cube_add()
