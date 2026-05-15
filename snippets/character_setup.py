"""character_setup.py
-------------------
Mixamo の "With Skin" FBX（Y Bot 等）を読み込み、ControlNet 入力画像の
量産パイプライン向けにシーンを正規化する初期セットアップ。

実行後の状態:
- シーンは空（既存オブジェクト全削除）
- Y Bot のアーマチュア + メッシュが原点に立っている（Z-up、適正スケール）
- ポートレート向け Camera（50mm, 縦長 768x1024）が腰高に設置
- Sun + Area の2灯ライト
- ワールドは無地グレー背景（ControlNet 入力に余計な情報を入れない）
- Render Engine = Eevee（バッチ速度優先）
- View Layer の Depth / Normal パスが有効化済み

使い方:
    1. CHARACTER_FBX を実ファイルパスに合わせて編集
    2. Blender で execute_blender_code 経由で実行 or テキストエディタから F5
"""

import bpy
import math
from mathutils import Vector

# ---- 設定 -----------------------------------------------------------------

CHARACTER_FBX = r"C:\Users\hoeho\Documents\Claude\BlenderSkill\blender\assets\vroid\base_motoko\base_motoko.fbx"

RENDER_WIDTH = 1024
RENDER_HEIGHT = 1024
CAMERA_FOCAL_MM = 50.0
CAMERA_HEIGHT = 1.0      # キャラ腰あたりを狙う
CAMERA_DISTANCE = 4.5    # キャラからの距離（m）
SUN_ENERGY = 3.0
AREA_ENERGY = 200.0
WORLD_BG_COLOR = (0.5, 0.5, 0.5, 1.0)  # ニュートラルグレー

# ---- ユーティリティ -------------------------------------------------------

def clear_scene():
    """Object Mode で全オブジェクト削除。コレクションは残す。"""
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # 残骸データブロックを掃除
    for block in list(bpy.data.meshes):
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in list(bpy.data.armatures):
        if block.users == 0:
            bpy.data.armatures.remove(block)
    for block in list(bpy.data.materials):
        if block.users == 0:
            bpy.data.materials.remove(block)


def import_mixamo_fbx(filepath):
    """Mixamo FBX をインポートし、スケール/向きを正規化して返す。

    Returns:
        (armature_object, mesh_objects)
    """
    # インポート前のオブジェクト集合を記録
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(
        filepath=filepath,
        use_anim=True,
        automatic_bone_orientation=True,
    )
    after = set(bpy.data.objects)
    new_objs = after - before

    armatures = [o for o in new_objs if o.type == 'ARMATURE']
    meshes = [o for o in new_objs if o.type == 'MESH']

    if not armatures:
        raise RuntimeError(f"アーマチュアが見つかりません: {filepath}")

    arm = armatures[0]
    arm.name = "Character"

    # T-pose の素体に「Layer0」アクションが付与されると、毎フレーム T-pose に巻き戻されて
    # copy_pose の結果が消える。インポート直後にアクションを外し、孤児アクションを掃除。
    if arm.animation_data:
        old_action = arm.animation_data.action
        arm.animation_data.action = None
        if old_action and old_action.users == 0:
            bpy.data.actions.remove(old_action)

    # Mixamo FBX は 100倍スケールで来ることが多い。実寸（約 1.8m）に近いなら不要、
    # 100x なら 0.01 をかけて Apply。
    if arm.dimensions.z > 50.0:
        arm.scale = (0.01, 0.01, 0.01)
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # 足元を Z=0 に
    min_z = min((arm.matrix_world @ Vector(corner)).z
                for m in meshes
                for corner in m.bound_box) if meshes else 0.0
    arm.location.z -= min_z

    # メッシュをアーマチュアの子として位置整合（既に parent されているはず）
    return arm, meshes


def setup_camera_and_light():
    """ポートレート向けカメラ + 2灯ライトを設置。"""
    # Camera
    bpy.ops.object.camera_add(
        location=(0, -CAMERA_DISTANCE, CAMERA_HEIGHT + 0.5),
        rotation=(math.radians(82), 0, 0),
    )
    cam = bpy.context.active_object
    cam.name = "PortraitCam"
    cam.data.lens = CAMERA_FOCAL_MM
    cam.data.sensor_width = 36.0
    bpy.context.scene.camera = cam

    # Sun（メイン）
    bpy.ops.object.light_add(type='SUN', location=(4, -4, 6),
                             rotation=(math.radians(45), 0, math.radians(30)))
    sun = bpy.context.active_object
    sun.name = "KeySun"
    sun.data.energy = SUN_ENERGY

    # Area（フィル、正面から）
    bpy.ops.object.light_add(type='AREA', location=(0, -3, 1.5))
    area = bpy.context.active_object
    area.name = "FillArea"
    area.data.energy = AREA_ENERGY
    area.data.size = 3.0

    return cam, sun, area


def setup_world():
    """ワールド背景をニュートラルグレーに。"""
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = WORLD_BG_COLOR
        bg.inputs["Strength"].default_value = 1.0


def setup_render():
    """レンダー設定（解像度・エンジン・View Layer パス）。"""
    scn = bpy.context.scene
    scn.render.resolution_x = RENDER_WIDTH
    scn.render.resolution_y = RENDER_HEIGHT
    scn.render.resolution_percentage = 100
    scn.render.film_transparent = False
    scn.render.image_settings.file_format = 'PNG'
    scn.render.image_settings.color_mode = 'RGBA'
    scn.render.image_settings.color_depth = '16'

    # Eevee に切り替え（4.x では 'BLENDER_EEVEE_NEXT'、3.x では 'BLENDER_EEVEE'）
    try:
        scn.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError:
        scn.render.engine = 'BLENDER_EEVEE'

    # View Layer パスを有効化
    vl = scn.view_layers[0]
    vl.use_pass_z = True
    vl.use_pass_normal = True
    vl.use_pass_combined = True

    # コンポジタは別スクリプトで構築するため、ここでは use_nodes だけON
    scn.use_nodes = True


# ---- メイン ---------------------------------------------------------------

def main():
    clear_scene()
    arm, meshes = import_mixamo_fbx(CHARACTER_FBX)
    setup_camera_and_light()
    setup_world()
    setup_render()
    print(f"[character_setup] Done. Armature='{arm.name}', meshes={[m.name for m in meshes]}")
    print(f"[character_setup] Armature bones={len(arm.data.bones)}")


if __name__ == "__main__":
    main()
