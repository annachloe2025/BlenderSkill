"""combat_scene_setup.py
------------------------
combat_scenes/*.blend のシーン構築用ヘルパー。

前提:
- シーンに A_Character, B_Character (Armature) が居る
- camera_target (Empty), Camera (TrackTo with camera_target) が居る
- lighting_flat / lighting_dramatic Collection が居る
- world_flat / world_dramatic World が居る

使い方:
    import importlib.util
    spec = importlib.util.spec_from_file_location("cs",
        r"C:\\...\\snippets\\combat_scene_setup.py")
    cs = importlib.util.module_from_spec(spec); spec.loader.exec_module(cs)
    cs.setup_combat_shot(
        pose_A="hook", pose_B="head_damaged_1",
        loc_A=(-0.4, 0, 0), loc_B=(0.4, 0, 0),
        cam_loc=(2.0, -2.5, 1.3), cam_target=(0, 0, 1.2),
        lighting='flat',
    )
"""

import bpy
import math
from mathutils import Vector

CHAR_BLEND = r"C:\Users\hoeho\Documents\Claude\BlenderSkill\blender\library\characters\base_motoko\base_motoko.blend"

# キャラの基本回転（メッシュの -90° X 補正 + 向き）
# +90° X: 立たせる、Z回転: 向き
ROT_FACING_PLUS_X  = (math.pi/2, 0,  math.pi/2)   # +X方向を向く
ROT_FACING_MINUS_X = (math.pi/2, 0, -math.pi/2)   # -X方向を向く
ROT_FACING_PLUS_Y  = (math.pi/2, 0,  math.pi)     # +Y方向を向く（カメラ反対）
ROT_FACING_MINUS_Y = (math.pi/2, 0,  0)           # -Y方向を向く（カメラ正面）


# ---- Action ロード ----

def ensure_action_loaded(action_name):
    """指定 Action がローカルに無ければ library/characters/base_motoko/base_motoko.blend から append。"""
    a = bpy.data.actions.get(action_name)
    if a:
        return a
    with bpy.data.libraries.load(CHAR_BLEND, link=False) as (df, dt):
        if action_name in df.actions:
            dt.actions = [action_name]
    return bpy.data.actions.get(action_name)


# ---- ポーズ適用 ----

def apply_pose(arm_name, pose_slug):
    """指定アーマチュアに pose_<slug> を適用。"""
    arm = bpy.data.objects.get(arm_name)
    if not arm:
        print(f"  [error] armature '{arm_name}' not found")
        return False
    action_name = f"pose_{pose_slug}"
    action = ensure_action_loaded(action_name)
    if not action:
        print(f"  [error] action '{action_name}' not found")
        return False
    # 既存LookAt系制約除去
    for pb in arm.pose.bones:
        for c in list(pb.constraints):
            if c.name in ('LookAtCam', 'LookAtForward', 'LookAtGlove'):
                pb.constraints.remove(c)
    # 全ボーンを一旦リセット
    for pb in arm.pose.bones:
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
        pb.location = (0, 0, 0)
    # Action assign
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    print(f"  [pose] {arm_name} ← {action_name}")
    return True


# ---- キャラ配置 ----

def set_character(arm_name, location, facing='auto', is_char_a=True):
    """キャラのワールド位置と向きを設定。
    facing:
      'auto': A → +X方向 / B → -X方向（互いに向き合う）
      'A_to_B' / 'B_to_A': 明示
      'plus_y' / 'minus_y': Y軸方向
      number (radians): 直接 Z 回転値
    """
    arm = bpy.data.objects.get(arm_name)
    if not arm:
        print(f"  [error] armature '{arm_name}' not found")
        return
    arm.location = location
    if facing == 'auto':
        arm.rotation_euler = ROT_FACING_PLUS_X if is_char_a else ROT_FACING_MINUS_X
    elif facing == 'A_to_B':
        arm.rotation_euler = ROT_FACING_PLUS_X
    elif facing == 'B_to_A':
        arm.rotation_euler = ROT_FACING_MINUS_X
    elif facing == 'plus_y':
        arm.rotation_euler = ROT_FACING_PLUS_Y
    elif facing == 'minus_y':
        arm.rotation_euler = ROT_FACING_MINUS_Y
    elif isinstance(facing, (int, float)):
        arm.rotation_euler = (math.pi/2, 0, facing)


# ---- カメラ ----

def set_camera(location, target_location=None, lens=50.0):
    """カメラ位置・ターゲット・レンズを設定。"""
    cam = bpy.data.objects.get("Camera")
    target = bpy.data.objects.get("camera_target")
    if cam:
        cam.location = location
        cam.data.lens = lens
    if target and target_location is not None:
        target.location = target_location
    bpy.context.view_layer.update()


# ---- ライティング切替 ----

def set_lighting(mode):
    """'flat' or 'dramatic' に切替（World と View Layer Collection を同期）。"""
    if mode not in ('flat', 'dramatic'):
        print(f"  [error] lighting mode '{mode}' は 'flat' or 'dramatic'")
        return
    # World
    world = bpy.data.worlds.get(f"world_{mode}")
    if world:
        bpy.context.scene.world = world
    # Collection の表示
    for m in ('flat', 'dramatic'):
        layer = bpy.context.view_layer.layer_collection.children.get(f"lighting_{m}")
        if layer:
            layer.exclude = (m != mode)
    print(f"  [lighting] {mode}")


# ---- 1関数でフルセット ----

def setup_combat_shot(pose_A, pose_B,
                      loc_A=(-0.4, 0, 0), loc_B=(0.4, 0, 0),
                      facing_A='auto', facing_B='auto',
                      cam_loc=(0, -3, 1.3), cam_target=(0, 0, 1.0),
                      lens=50.0,
                      lighting='flat'):
    """1関数で1ショット構築。ポーズ・配置・カメラ・ライティングを一気に決める。"""
    print(f"\n=== combat shot: A=pose_{pose_A}, B=pose_{pose_B}, lighting={lighting} ===")
    set_character("A_Character", loc_A, facing=facing_A, is_char_a=True)
    set_character("B_Character", loc_B, facing=facing_B, is_char_a=False)
    apply_pose("A_Character", pose_A)
    apply_pose("B_Character", pose_B)
    set_camera(cam_loc, cam_target, lens)
    set_lighting(lighting)


# ---- レンダー ----

def render_to(output_path):
    """指定パスにレンダー保存（PNG）。"""
    scn = bpy.context.scene
    scn.use_nodes = False
    scn.render.image_settings.file_format = 'PNG'
    scn.render.image_settings.color_mode = 'RGB'
    scn.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  [render] {output_path}")


def render_flat_and_dramatic(out_dir, basename):
    """同じ構図で flat と dramatic 両方撮る。"""
    import os
    os.makedirs(out_dir, exist_ok=True)
    set_lighting('flat')
    render_to(os.path.join(out_dir, f"{basename}_flat.png"))
    set_lighting('dramatic')
    render_to(os.path.join(out_dir, f"{basename}_dramatic.png"))
    # 戻す
    set_lighting('flat')
