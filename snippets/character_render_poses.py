"""character_render_poses.py
---------------------------
character_setup.py で準備したシーン（Y Bot キャラ + Camera + Light）に対し、
assets/mixamo/ 内の "Without Skin" ポーズFBX群を順に当てて、
ControlNet 入力用の4種類画像（Beauty/Depth/Normal/OpenPose）を出力する。

前提: character_setup.py を先に実行し、シーンに "Character" アーマチュアが存在すること。

出力先:
    outputs/character/poses/<pose_name>/
        beauty_0001.png        # 通常レンダー（Cannyの元）
        depth_0001.png         # 16bit BW、近=白
        normal_0001.png        # ワールド空間Normal（0.5+0.5でRGB化）
        openpose_0001.png      # 自前生成のOpenPose骨格画像
"""

import bpy
import math
import os
import re
import glob
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

import numpy as np

# ---- 設定 -----------------------------------------------------------------

POSE_FBX_ROOT = r"C:\Users\hoeho\Documents\Claude\BlenderSkill\blender\assets\animations"
POSE_FBX_GLOB = POSE_FBX_ROOT + r"\**\*.fbx"   # 再帰glob
OUTPUT_ROOT = r"C:\Users\hoeho\Documents\Claude\BlenderSkill\blender\outputs\single_render\base_motoko\poses"
CHARACTER_ARMATURE_NAME = "Character"

# ポーズごとの「決めフレーム」指定（slug 名 → frame番号）
# 指定が無いポーズはアニメの中央フレームが使われる
POSE_FRAMES = {
    "body_damaged_1": 10,
    "body_damaged_2": 10,
    "body_damaged_3": 6,
    "body_damaged_4": 8,
    "body_dameged_lib": 8,
    "body_jab_cross": 21,
    "bodyhook": 22,
    "bodyupper": 22,
    "defeat": 70,
    "dodging": 5,
    "down_kneel": 60,
    "entry": 110,
    "guard_up": 5,
    "head_damaged_1": 14,
    "head_damaged_2": 11,
    "head_damaged_3": 12,
    "head_damaged_4": 9,
    "hook": 37,
    "hook_2": 20,
    "hook_damaged_1": 9,
    "hook_damaged_2": 8,
    "idle": 1,
    "illegal_headbutt": 25,
    "illegal_knee": 24,
    "jab_2": 13,
    "jab_cross": 22,
    "jab_damaged_1": 6,
    "jab_damaged_2": 7,
    "knee": 33,
    "long_step_forward": 5,
    "onetwo": 20,
    "receiving_a_big_uppercut": 12,
    "running": 5,
    "short_left_side_step": 5,
    "short_right_side_step": 5,
    "step_backward": 5,
    "straight_2": 20,
    "upper": 22,
    "uppercut": 24,
    "victory": 52,
    "walking": 5,
}

# 5つの標準カメラアングル（キャラの胸付近をターゲット、2.0m距離）
# 2026-05-15 ユーザ依頼で距離を縮め、カメラ高さを胸レベルに変更
#   旧: distance=4.5m, height=1.5m （頭〜目線レベル、全身余白あり）
#   新: distance=2.0m, height=1.0m （胸レベル、足首から下が切れる詰まり構図）
STANDARD_CAMERA_ANGLES = [
    {"name": "front",      "offset_xy": (0.0, -2.0)},
    {"name": "left_45",    "offset_xy": (1.414, -1.414)},   # キャラの左前45度
    {"name": "right_45",   "offset_xy": (-1.414, -1.414)},  # キャラの右前45度
    {"name": "left_side",  "offset_xy": (2.0, 0.0)},        # キャラの左サイド
    {"name": "right_side", "offset_xy": (-2.0, 0.0)},       # キャラの右サイド
]
CAMERA_HEIGHT = 1.0
CAMERA_LENS = 50.0

# 攻撃系カテゴリは head を「正面（-Y方向）」に向け固定
CATEGORIES_HEAD_FACE_FORWARD = {"attacks"}

# === 拡張 framing（fullbody以外の追加構図）===
# distance, height, look_at_z, lens を各 framing で指定。
# 5アングル方向は make_framing_angles() で distance から自動生成（front/left_45/right_45/left_side/right_side）
FRAMING_CONFIGS = {
    "bustup": {
        "distance": 1.2,
        "height":   1.2,    # 顔レベル
        "look_at_z": 1.10,  # 顎〜首
        "lens":     50.0,
    },
    "lowangle": {
        "distance": 1.2,    # さらに寄せ
        "height":   0.3,    # ほぼ床、見上げ構図
        "look_at_z": 1.0,   # 胸あたり
        "lens":     50.0,
    },
    "topdown": {
        "distance": 1.4,
        "height":   1.8,    # 2.0 → 1.8 さらに緩く
        "look_at_z": 1.0,   # 胸あたり
        "lens":     50.0,
    },
}


def make_framing_angles(distance):
    """5方向の標準アングル offset を任意距離で生成。"""
    s = distance / math.sqrt(2)
    return [
        {"name": "front",      "offset_xy": (0.0, -distance)},
        {"name": "left_45",    "offset_xy": (s, -s)},
        {"name": "right_45",   "offset_xy": (-s, -s)},
        {"name": "left_side",  "offset_xy": (distance, 0.0)},
        {"name": "right_side", "offset_xy": (-distance, 0.0)},
    ]


# 旧変数も互換のため残す（既存呼び出しが動くように）
BUSTUP_CAMERA_ANGLES = make_framing_angles(FRAMING_CONFIGS["bustup"]["distance"])
BUSTUP_CAMERA_HEIGHT = FRAMING_CONFIGS["bustup"]["height"]
BUSTUP_LOOK_AT_Z = FRAMING_CONFIGS["bustup"]["look_at_z"]
BUSTUP_LENS = FRAMING_CONFIGS["bustup"]["lens"]

# ポーズ別「顔をグローブに向ける」上書き設定
# slug → 'L' / 'R' / 'auto'（autoはスパインから遠い方のグローブを選択＝伸ばしてる拳）
# このdictにあるポーズは CATEGORIES_HEAD_FACE_FORWARD より優先される
# 2026-05-16 motion_memo.md の r/l 表記に基づき明示化
POSE_HEAD_LOOK_AT_GLOVE = {
    "body_jab_cross": "R",
    "bodyhook":       "R",
    "bodyupper":      "R",
    "hook":           "L",
    "hook_2":         "L",
    "jab_2":          "L",
    "jab_cross":      "R",
    "onetwo":         "R",
    "straight_2":     "R",
    "upper":          "L",
    "uppercut":       "L",
    # 未指定（illegal_headbutt, illegal_knee, knee）は CATEGORIES_HEAD_FACE_FORWARD で正面固定
}

# ポーズごとのカメラ位置 / 回転（slug 名 → {"location": (x,y,z), "rotation_euler_deg": (rx,ry,rz)}）
# 指定が無いポーズは character_setup.py のデフォルトが使われる
POSE_CAMERAS = {
    "hook": {
        "location": (-1.168, -2.027, 1.448),
        "rotation_euler_deg": (73.54, 0.0, -54.08),
        "look_at_camera": False,
    },
    "idle": {
        "location": (0.0, -4.5, 1.5),
        "rotation_euler_deg": (82.0, 0.0, 0.0),
        "look_at_camera": True,
    },
    "upper": {
        "location": (0.0, -4.5, 1.5),
        "rotation_euler_deg": (82.0, 0.0, 0.0),
        "look_at_camera": True,
    },
    "victory": {
        "location": (0.0, -4.5, 1.5),
        "rotation_euler_deg": (82.0, 0.0, 0.0),
        "look_at_camera": True,
    },
    # ...
}

# ポーズごとの表情（VRoid shape keys 名 → value 0..1）
# 個別指定があれば最優先（CATEGORIES_DEFAULT_EXPRESSION より優先される）
POSE_EXPRESSIONS = {
    "victory": {"Fcl_ALL_Joy": 1.0},
    # "idle": {"Fcl_ALL_Neutral": 1.0},
    # body 系ダメージは Damaged_body（カテゴリデフォルト Damaged より優先）
    "body_damaged_1":    {"Fcl_ALL_Damaged_body": 1.0},
    "body_damaged_2":    {"Fcl_ALL_Damaged_body": 1.0},
    "body_damaged_3":    {"Fcl_ALL_Damaged_body": 1.0},
    "body_damaged_4":    {"Fcl_ALL_Damaged_body": 1.0},
    "body_dameged_lib":  {"Fcl_ALL_Damaged_body": 1.0},
}

# カテゴリ単位のデフォルト表情。POSE_EXPRESSIONS に個別指定が無い場合に適用される
CATEGORIES_DEFAULT_EXPRESSION = {
    "attacks":  {"Fcl_ALL_Angry": 1.0},
    "damaged":  {"Fcl_ALL_Damaged": 1.0},
}

# 表情単独レンダー用の出力先・リスト・カメラ
EXPRESSIONS_OUTPUT_ROOT = r"C:\Users\hoeho\Documents\Claude\BlenderSkill\blender\outputs\single_render\base_motoko\expressions"

# (slug, シェイプキー名 or dict) のリスト
# slugに "/" 含めるとカテゴリ別サブフォルダになる: "brw/angry" -> expressions/brw/angry/
# 値が dict なら複数シェイプキーを同時適用（組み合わせ表情用）
EXPRESSION_LIST = [
    # === ALL系（全6 + ユーザ追加5） ===
    ("all/neutral",     "Fcl_ALL_Neutral"),
    ("all/joy",         "Fcl_ALL_Joy"),
    ("all/fun",         "Fcl_ALL_Fun"),
    ("all/angry",       "Fcl_ALL_Angry"),
    ("all/sorrow",      "Fcl_ALL_Sorrow"),
    ("all/surprised",   "Fcl_ALL_Surprised"),
    # --- ユーザ追加 ---
    ("all/damaged",      "Fcl_ALL_Damaged"),
    ("all/damaged_body", "Fcl_ALL_Damaged_body"),
    ("all/pain",         "Fcl_ALL_Pain"),
    ("all/straggle",     "Fcl_ALL_Straggle"),
    ("all/confused",     "Fcl_All_Confused"),
    # === BRW (眉のみ) 5個 ===
    ("brw/angry",     "Fcl_BRW_Angry"),
    ("brw/fun",       "Fcl_BRW_Fun"),
    ("brw/joy",       "Fcl_BRW_Joy"),
    ("brw/sorrow",    "Fcl_BRW_Sorrow"),
    ("brw/surprised", "Fcl_BRW_Surprised"),
    # === EYE (目のみ) 14個 + ユーザ追加3 ===
    ("eye/natural",        "Fcl_EYE_Natural"),
    ("eye/angry",          "Fcl_EYE_Angry"),
    ("eye/close",          "Fcl_EYE_Close"),
    ("eye/close_r",        "Fcl_EYE_Close_R"),
    ("eye/close_l",        "Fcl_EYE_Close_L"),
    ("eye/fun",            "Fcl_EYE_Fun"),
    ("eye/joy",            "Fcl_EYE_Joy"),
    ("eye/joy_r",          "Fcl_EYE_Joy_R"),
    ("eye/joy_l",          "Fcl_EYE_Joy_L"),
    ("eye/sorrow",         "Fcl_EYE_Sorrow"),
    ("eye/surprised",      "Fcl_EYE_Surprised"),
    ("eye/spread",         "Fcl_EYE_Spread"),
    ("eye/iris_hide",      "Fcl_EYE_Iris_Hide"),
    ("eye/highlight_hide", "Fcl_EYE_Highlight_Hide"),
    # --- ユーザ追加 ---
    ("eye/angly_2",        "Fcl_EYE_Angly_2"),
    ("eye/joy_2",          "Fcl_EYE_Joy_2"),
    ("eye/sanpaku",        "Fcl_EYE_Sanpaku"),
    # === MTH (口のみ) 19個 ===
    ("mth/close",       "Fcl_MTH_Close"),
    ("mth/up",          "Fcl_MTH_Up"),
    ("mth/down",        "Fcl_MTH_Down"),
    ("mth/angry",       "Fcl_MTH_Angry"),
    ("mth/small",       "Fcl_MTH_Small"),
    ("mth/large",       "Fcl_MTH_Large"),
    ("mth/neutral",     "Fcl_MTH_Neutral"),
    ("mth/fun",         "Fcl_MTH_Fun"),
    ("mth/joy",         "Fcl_MTH_Joy"),
    ("mth/sorrow",      "Fcl_MTH_Sorrow"),
    ("mth/surprised",   "Fcl_MTH_Surprised"),
    ("mth/skinfung",    "Fcl_MTH_SkinFung"),
    ("mth/skinfung_r",  "Fcl_MTH_SkinFung_R"),
    ("mth/skinfung_l",  "Fcl_MTH_SkinFung_L"),
    ("mth/a",           "Fcl_MTH_A"),
    ("mth/i",           "Fcl_MTH_I"),
    ("mth/u",           "Fcl_MTH_U"),
    ("mth/e",           "Fcl_MTH_E"),
    ("mth/o",           "Fcl_MTH_O"),
    # --- ユーザ追加 ---
    ("mth/e2",          "Fcl_MTH_e2"),
    ("mth/he",          "Fcl_MTH_he"),
    ("mth/ii",          "Fcl_MTH_ii"),
    # === HA (髪) 13個 ===
    ("ha/hide",       "Fcl_HA_Hide"),
    ("ha/fung1",      "Fcl_HA_Fung1"),
    ("ha/fung1_low",  "Fcl_HA_Fung1_Low"),
    ("ha/fung1_up",   "Fcl_HA_Fung1_Up"),
    ("ha/fung2",      "Fcl_HA_Fung2"),
    ("ha/fung2_low",  "Fcl_HA_Fung2_Low"),
    ("ha/fung2_up",   "Fcl_HA_Fung2_Up"),
    ("ha/fung3",      "Fcl_HA_Fung3"),
    ("ha/fung3_up",   "Fcl_HA_Fung3_Up"),
    ("ha/fung3_low",  "Fcl_HA_Fung3_Low"),
    ("ha/short",      "Fcl_HA_Short"),
    ("ha/short_up",   "Fcl_HA_Short_Up"),
    ("ha/short_low",  "Fcl_HA_Short_Low"),

    # === COMPOUND (BRW + EYE + MTH の組み合わせ) ===
    # ここにユーザが手動作成したシェイプキーを追加して使う
    # 例: ("compound/my_angry_smug", "Custom_AngrySmug"),
]

# 顔クローズアップ用カメラ設定（ユーザ調整版）
FACE_CAMERA_CONFIG = {
    "location": (0.0194, -0.4435, 1.4578),
    "rotation_euler_deg": (91.2, 0.0, 3.0),
    "lens": 50.0,
}


def apply_pose_expression(pose_slug, category=None):
    """ポーズ別シェイプキー値を顔メッシュに適用。
    優先順位:
      1. POSE_EXPRESSIONS[pose_slug] あればそれ
      2. CATEGORIES_DEFAULT_EXPRESSION[category] あればそれ
      3. 何も無ければ全シェイプキー=0でリセット
    """
    face = None
    for o in bpy.context.scene.objects:
        if o.type == 'MESH' and 'face' in o.name.lower() and o.data.shape_keys:
            face = o
            break
    if not face:
        return
    sk = face.data.shape_keys
    # 全シェイプキーをリセット
    for kb in sk.key_blocks:
        if kb.name != 'Basis':
            kb.value = 0.0
    # 1. ポーズ個別 → 2. カテゴリデフォルト の順で参照
    expr = POSE_EXPRESSIONS.get(pose_slug)
    if expr is None and category is not None:
        expr = CATEGORIES_DEFAULT_EXPRESSION.get(category)
    if not expr:
        return
    for name, value in expr.items():
        kb = sk.key_blocks.get(name)
        if kb:
            kb.value = float(value)


def apply_pose_camera(pose_slug):
    """ポーズ別カメラ設定があれば適用、無ければデフォルトのまま。"""
    cfg = POSE_CAMERAS.get(pose_slug)
    if not cfg:
        return
    cam = bpy.context.scene.camera
    if not cam:
        return
    cam.location = cfg["location"]
    rx, ry, rz = cfg["rotation_euler_deg"]
    cam.rotation_euler = (math.radians(rx), math.radians(ry), math.radians(rz))


def apply_head_look_at_camera(arm, pose_slug):
    """ポーズ別に Head ボーンの Track To 制約をON/OFF。"""
    cam = bpy.context.scene.camera
    head = _find_head_bone(arm)
    if not head:
        return
    # 既存LookAt系制約を一旦削除
    for c in list(head.constraints):
        if c.name in ('LookAtCam', 'LookAtForward'):
            head.constraints.remove(c)
    cfg = POSE_CAMERAS.get(pose_slug, {})
    if cfg.get("look_at_camera") and cam:
        track = head.constraints.new('TRACK_TO')
        track.name = 'LookAtCam'
        track.target = cam
        track.track_axis = 'TRACK_Z'
        track.up_axis = 'UP_Y'


def _find_head_bone(arm):
    for pb in arm.pose.bones:
        if pb.name.endswith(":Head") or pb.name == "Head":
            return pb
    return None


def _get_or_create_forward_target():
    """Head が向き続ける固定 -Y target empty を取得 or 生成。"""
    name = "HeadForwardTarget"
    obj = bpy.data.objects.get(name)
    if obj is None:
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, -10, 1.5))
        obj = bpy.context.active_object
        obj.name = name
    return obj


def apply_head_face_forward(arm, enable):
    """攻撃系で head を -Y方向（正面）に固定して向けるTrack To constraint。"""
    head = _find_head_bone(arm)
    if not head:
        return
    # 既存LookAt系を全部除去
    for c in list(head.constraints):
        if c.name in ('LookAtCam', 'LookAtForward', 'LookAtGlove'):
            head.constraints.remove(c)
    if enable:
        target = _get_or_create_forward_target()
        track = head.constraints.new('TRACK_TO')
        track.name = 'LookAtForward'
        track.target = target
        track.track_axis = 'TRACK_Z'
        track.up_axis = 'UP_Y'


def _resolve_glove_target(arm, spec):
    """spec が 'L'/'R'/'auto' のときに対応する boxing_gloves オブジェクトを返す。"""
    if spec == 'L':
        return bpy.data.objects.get('boxing_gloves.L')
    if spec == 'R':
        return bpy.data.objects.get('boxing_gloves.R')
    if spec == 'auto':
        # spine2 中心から遠いほうのグローブを選ぶ（伸びてる方の拳が打撃方向）
        spine_pb = None
        for pb in arm.pose.bones:
            if pb.name.endswith(':Spine2') or pb.name == 'Spine2':
                spine_pb = pb
                break
        if spine_pb is None:
            return None
        spine_world = arm.matrix_world @ spine_pb.head
        gl = bpy.data.objects.get('boxing_gloves.L')
        gr = bpy.data.objects.get('boxing_gloves.R')
        if not (gl and gr):
            return None
        dl = (gl.matrix_world.translation - spine_world).length
        dr = (gr.matrix_world.translation - spine_world).length
        return gl if dl > dr else gr
    return None


def apply_head_target(arm, pose_slug, category):
    """Head ボーンに Track To 制約を適用。
    優先順位:
      1. POSE_HEAD_LOOK_AT_GLOVE にあれば そのグローブを向く
      2. CATEGORIES_HEAD_FACE_FORWARD なら 正面 -Y を向く
      3. それ以外は制約なし
    """
    head = _find_head_bone(arm)
    if not head:
        return
    # 既存LookAt系を全部除去
    for c in list(head.constraints):
        if c.name in ('LookAtCam', 'LookAtForward', 'LookAtGlove'):
            head.constraints.remove(c)
    # 1. グローブ追従最優先
    if pose_slug in POSE_HEAD_LOOK_AT_GLOVE:
        spec = POSE_HEAD_LOOK_AT_GLOVE[pose_slug]
        target_glove = _resolve_glove_target(arm, spec)
        if target_glove:
            track = head.constraints.new('TRACK_TO')
            track.name = 'LookAtGlove'
            track.target = target_glove
            track.track_axis = 'TRACK_Z'
            track.up_axis = 'UP_Y'
            return
    # 2. 攻撃カテゴリは正面固定
    if category in CATEGORIES_HEAD_FACE_FORWARD:
        target = _get_or_create_forward_target()
        track = head.constraints.new('TRACK_TO')
        track.name = 'LookAtForward'
        track.target = target
        track.track_axis = 'TRACK_Z'
        track.up_axis = 'UP_Y'


def get_character_center():
    """キャラの spine/chest world position を返す（カメラのlook-at基準）。"""
    arm = bpy.data.objects.get(CHARACTER_ARMATURE_NAME)
    if not arm:
        return Vector((0, 0, 1.0))
    for sname in ('Spine2', 'Spine1', 'Spine', 'Hips'):
        pb = find_bone(arm, sname)
        if pb:
            return arm.matrix_world @ pb.head
    return Vector((0, 0, 1.0))


def apply_standard_camera_angle(angle_config):
    """STANDARD_CAMERA_ANGLES の1個を適用。キャラ位置基準でカメラ配置＋ターゲット注視。"""
    cam = bpy.context.scene.camera
    if not cam:
        return
    center = get_character_center()
    ox, oy = angle_config["offset_xy"]
    cam.location = (center.x + ox, center.y + oy, CAMERA_HEIGHT)
    cam.data.lens = CAMERA_LENS
    direction = center - Vector(cam.location)
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


def apply_bustup_camera_angle(angle_config):
    """BUSTUP_CAMERA_ANGLES の1個を適用。胸から上のクローズアップ構図。"""
    cam = bpy.context.scene.camera
    if not cam:
        return
    center = get_character_center()  # spine2 = chest
    ox, oy = angle_config["offset_xy"]
    cam.location = (center.x + ox, center.y + oy, BUSTUP_CAMERA_HEIGHT)
    cam.data.lens = BUSTUP_LENS
    # 注視点は胸X,Y, 顎〜首あたりの高さ
    look_at = Vector((center.x, center.y, BUSTUP_LOOK_AT_Z))
    direction = look_at - Vector(cam.location)
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


def apply_framing_camera_angle(angle_config, framing_cfg):
    """汎用 framing カメラ適用。framing_cfg は FRAMING_CONFIGS の1エントリ。"""
    cam = bpy.context.scene.camera
    if not cam:
        return
    center = get_character_center()
    ox, oy = angle_config["offset_xy"]
    cam.location = (center.x + ox, center.y + oy, framing_cfg["height"])
    cam.data.lens = framing_cfg["lens"]
    look_at = Vector((center.x, center.y, framing_cfg["look_at_z"]))
    direction = look_at - Vector(cam.location)
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

# OpenPose body 18 ボーン接尾辞マップ（Mixamoの "mixamorig:" / "mixamorig1:" 等の
# プレフィックスはインポート順で変わるので、コロンの後の名前だけで照合する）
OPENPOSE_BONE_SUFFIX = {
    1:  "Neck",
    2:  "RightArm",      # R Shoulder = 上腕の根本
    3:  "RightForeArm",  # R Elbow
    4:  "RightHand",     # R Wrist
    5:  "LeftArm",
    6:  "LeftForeArm",
    7:  "LeftHand",
    8:  "RightUpLeg",    # R Hip
    9:  "RightLeg",      # R Knee
    10: "RightFoot",     # R Ankle
    11: "LeftUpLeg",
    12: "LeftLeg",
    13: "LeftFoot",
}
# 0=Nose, 14=REye, 15=LEye, 16=REar, 17=LEar は Head ボーンから幾何的に近似


def find_bone(arm, suffix):
    """ボーンを接尾辞で検索（"mixamorig:XX" でも "mixamorig1:XX" でもヒット）。"""
    target = ":" + suffix
    for pb in arm.pose.bones:
        if pb.name.endswith(target) or pb.name == suffix:
            return pb
    return None

OPENPOSE_LIMBS = [
    (1, 2), (1, 5), (2, 3), (3, 4), (5, 6), (6, 7),
    (1, 8), (8, 9), (9, 10), (1, 11), (11, 12), (12, 13),
    (1, 0), (0, 14), (14, 16), (0, 15), (15, 17),
]
OPENPOSE_LIMB_COLORS = [
    (153, 0, 0), (153, 51, 0), (153, 102, 0), (153, 153, 0),
    (102, 153, 0), (51, 153, 0), (0, 153, 0), (0, 153, 51),
    (0, 153, 102), (0, 153, 153), (0, 102, 153), (0, 51, 153),
    (0, 0, 153), (51, 0, 153), (102, 0, 153), (153, 0, 153),
    (153, 0, 102),
]
OPENPOSE_KP_COLORS = [
    (255, 0, 0), (255, 85, 0), (255, 170, 0), (255, 255, 0),
    (170, 255, 0), (85, 255, 0), (0, 255, 0), (0, 255, 85),
    (0, 255, 170), (0, 255, 255), (0, 170, 255), (0, 85, 255),
    (0, 0, 255), (85, 0, 255), (170, 0, 255), (255, 0, 255),
    (255, 0, 170), (255, 0, 85),
]


# ---- ポーズ転写 -----------------------------------------------------------

def import_pose_fbx(filepath):
    """ポーズ専用 FBX をインポート。元のオブジェクトは衝突しないよう名前変更。"""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=filepath, use_anim=True,
                             automatic_bone_orientation=True)
    after = set(bpy.data.objects)
    new = after - before
    armatures = [o for o in new if o.type == 'ARMATURE']
    if not armatures:
        # 削除してから例外
        for o in new:
            bpy.data.objects.remove(o, do_unlink=True)
        raise RuntimeError(f"ポーズFBXにアーマチュアがない: {filepath}")
    src = armatures[0]
    src.name = "_PoseSrc"
    # Mixamo 100x スケール補正
    if src.dimensions.z > 50.0:
        src.scale = (0.01, 0.01, 0.01)
        bpy.context.view_layer.objects.active = src
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return src, [o for o in new if o.type != 'ARMATURE']


def pick_pose_frame(src_arm, pose_slug=None):
    """ポーズ用フレームを選ぶ。POSE_FRAMES に指定があればそれ、なければ中央。"""
    if pose_slug and pose_slug in POSE_FRAMES:
        return int(POSE_FRAMES[pose_slug])
    ad = src_arm.animation_data
    if ad and ad.action:
        s, e = ad.action.frame_range
        return int((s + e) // 2)
    return 1


def copy_pose(src_arm, dst_arm, frame):
    """src のポーズを dst に転写。両アーマチュアのプレフィックスが違っても接尾辞で照合。

    重要: dst にアクションが残っているとレンダー直前の frame_set で T-pose に
    巻き戻されるので、コピー前にアクションを外す。
    """
    if dst_arm.animation_data and dst_arm.animation_data.action:
        dst_arm.animation_data.action = None

    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()

    # dst 側のボーンを接尾辞で索引
    def suffix_of(name):
        return name.split(":", 1)[-1]

    dst_index = {suffix_of(pb.name): pb for pb in dst_arm.pose.bones}

    for src_pb in src_arm.pose.bones:
        dst_pb = dst_index.get(suffix_of(src_pb.name))
        if dst_pb is None:
            continue
        dst_pb.rotation_mode = src_pb.rotation_mode
        if src_pb.rotation_mode == 'QUATERNION':
            dst_pb.rotation_quaternion = src_pb.rotation_quaternion.copy()
        else:
            dst_pb.rotation_euler = src_pb.rotation_euler.copy()
        # 位置は Hips だけ（Mixamoの慣習）
        if src_pb.name.endswith("Hips"):
            dst_pb.location = src_pb.location.copy()
    bpy.context.view_layer.update()


def remove_obj_tree(arm_obj, extras):
    """ポーズ用に持ち込んだオブジェクト一式を削除。"""
    targets = [arm_obj] + list(extras)
    for o in targets:
        if o.name in bpy.data.objects:
            bpy.data.objects.remove(o, do_unlink=True)


# ---- コンポジタ設定 -------------------------------------------------------

def _get_compositor_tree(scn):
    """Blender 3.x/4.x の scene.node_tree と 5.x の compositing_node_group 両対応。"""
    scn.use_nodes = True
    if hasattr(scn, 'compositing_node_group'):
        # Blender 5.x
        if scn.compositing_node_group is None:
            ng = bpy.data.node_groups.new("CompositorTree", 'CompositorNodeTree')
            scn.compositing_node_group = ng
        return scn.compositing_node_group
    return scn.node_tree


def _make_image_output(tree, directory, file_name, fmt, color_mode, color_depth, socket_type):
    """1ノード = 1ファイル の OutputFile を作成（Blender 5.x 仕様）。

    要点:
      - format.media_type = 'IMAGE' でないと OPEN_EXR_MULTILAYER に固定される
      - file_output_items.new(socket_type, '') で実スロットを作る必要あり
      - 接続先は inputs[0]（item 追加後に出てくるソケット）
    """
    n = tree.nodes.new('CompositorNodeOutputFile')
    n.directory = directory
    n.file_name = file_name
    n.format.media_type = 'IMAGE'
    n.format.file_format = fmt
    n.format.color_mode = color_mode
    n.format.color_depth = color_depth
    n.file_output_items.new(socket_type, '')
    return n


def setup_compositor(output_dir):
    """Beauty(PNG) と Depth/Normal(EXR float) を 3 ノードで分割出力。

    Blender 5.x の新コンポジタは MixRGB / MapRange 等が未実装のため、
    Depth/Normal は生の EXR で出力し、render 後に numpy で PNG に変換する。
    """
    scn = bpy.context.scene
    tree = _get_compositor_tree(scn)
    for n in list(tree.nodes):
        tree.nodes.remove(n)

    rl = tree.nodes.new('CompositorNodeRLayers')
    rl.location = (-400, 0)

    beauty = _make_image_output(tree, output_dir, "beauty",
                                'PNG', 'RGB', '8', 'RGBA')
    beauty.location = (200, 300)
    tree.links.new(rl.outputs['Image'], beauty.inputs[0])

    depth = _make_image_output(tree, output_dir, "depth_raw",
                               'OPEN_EXR', 'BW', '32', 'FLOAT')
    depth.location = (200, 50)
    tree.links.new(rl.outputs['Depth'], depth.inputs[0])

    normal = _make_image_output(tree, output_dir, "normal_raw",
                                'OPEN_EXR', 'RGB', '32', 'VECTOR')
    normal.location = (200, -200)
    tree.links.new(rl.outputs['Normal'], normal.inputs[0])


def _save_png_via_blender(rgba_float_topdown, filepath, color_depth='8'):
    """numpy 配列(H,W,4) 0..1 を Blender の image API 経由で PNG 保存。

    Blender の image.pixels は **下から上** の順なので、入力（上から下）を反転して入れる。
    """
    h, w = rgba_float_topdown.shape[:2]
    flipped = np.flipud(rgba_float_topdown).astype(np.float32)

    use_float = (color_depth == '16')
    img = bpy.data.images.new("_tmp_save", width=w, height=h,
                              alpha=True, float_buffer=use_float)
    img.pixels.foreach_set(flipped.ravel())
    img.filepath_raw = filepath
    img.file_format = 'PNG'
    # PNG ビット深度
    scn = bpy.context.scene
    orig_depth = scn.render.image_settings.color_depth
    orig_mode = scn.render.image_settings.color_mode
    orig_fmt = scn.render.image_settings.file_format
    scn.render.image_settings.file_format = 'PNG'
    scn.render.image_settings.color_mode = 'RGBA'
    scn.render.image_settings.color_depth = color_depth
    try:
        img.save_render(filepath)
    finally:
        scn.render.image_settings.color_depth = orig_depth
        scn.render.image_settings.color_mode = orig_mode
        scn.render.image_settings.file_format = orig_fmt
    bpy.data.images.remove(img)


def postprocess_passes(pose_dir, depth_near=0.5, depth_far=20.0):
    """生 EXR を読み込んで ControlNet 向け PNG に変換（Pillow 不要、Blender image API）。

    - depth_raw*.exr -> depth.png (16bit BW, 近=白)
    - normal_raw*.exr -> normal.png (8bit RGB, +0.5 シフト)
    """
    for tag, processor in (("depth_raw", "depth"), ("normal_raw", "normal")):
        for f in sorted(glob.glob(os.path.join(pose_dir, tag + "*.exr"))):
            img = bpy.data.images.load(f, check_existing=False)
            w, h = img.size
            px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, -1)
            bpy.data.images.remove(img)

            # 反転（pixels は下から上なので、トップダウンに直す）
            px = np.flipud(px)

            if processor == "depth":
                d = px[:, :, 0]
                d = np.where(d > 1e6, depth_far, d)
                norm = 1.0 - np.clip((d - depth_near) / (depth_far - depth_near), 0, 1)
                rgba = np.zeros((h, w, 4), dtype=np.float32)
                rgba[:, :, 0] = rgba[:, :, 1] = rgba[:, :, 2] = norm
                rgba[:, :, 3] = 1.0
                out_path = f.replace("depth_raw", "depth").replace(".exr", ".png")
                _save_png_via_blender(rgba, out_path, color_depth='16')
            else:
                n = px[:, :, :3]
                rgb = np.clip(n * 0.5 + 0.5, 0, 1)
                rgba = np.ones((h, w, 4), dtype=np.float32)
                rgba[:, :, :3] = rgb
                out_path = f.replace("normal_raw", "normal").replace(".exr", ".png")
                _save_png_via_blender(rgba, out_path, color_depth='8')

            os.remove(f)
            print(f"[postprocess] {os.path.basename(out_path)} 生成")


def update_compositor_paths(output_dir):
    """各 File Output ノードの directory をポーズごとに切り替え。"""
    tree = _get_compositor_tree(bpy.context.scene)
    for n in tree.nodes:
        if n.type == 'OUTPUT_FILE':
            n.directory = output_dir


# ---- OpenPose 生成 --------------------------------------------------------

def _proj(scene, cam, point_world):
    co = world_to_camera_view(scene, cam, point_world)
    w = scene.render.resolution_x
    h = scene.render.resolution_y
    x = co.x * w
    y = (1.0 - co.y) * h
    visible = (0.0 <= co.x <= 1.0) and (0.0 <= co.y <= 1.0) and co.z > 0
    return (x, y, visible)


def collect_openpose_keypoints(arm):
    """アーマチュアから18点の (x, y, visible) を返す。プレフィックス非依存。"""
    scn = bpy.context.scene
    cam = scn.camera
    kps = [None] * 18

    # 1..13 は接尾辞マップから
    for idx, suf in OPENPOSE_BONE_SUFFIX.items():
        pb = find_bone(arm, suf)
        if pb is None:
            continue
        head_w = arm.matrix_world @ pb.head
        kps[idx] = _proj(scn, cam, head_w)

    # 0 (Nose), 14/15 (Eyes), 16/17 (Ears) は Head ボーンから近似
    head = find_bone(arm, "Head")
    if head is not None:
        head_top = find_bone(arm, "HeadTop_End")
        head_pos_w = arm.matrix_world @ head.head
        top_pos_w  = arm.matrix_world @ (head_top.head if head_top else head.tail)

        head_mat3 = (arm.matrix_world @ head.matrix).to_3x3()
        axis_x = head_mat3.col[0].normalized()
        axis_y = head_mat3.col[1].normalized()
        axis_z = head_mat3.col[2].normalized()

        face_center = (head_pos_w + top_pos_w) * 0.5
        forward = axis_z
        up = axis_y
        right = axis_x

        nose_w  = face_center + forward * 0.10
        reye_w  = nose_w + up * 0.03 - right * 0.03
        leye_w  = nose_w + up * 0.03 + right * 0.03
        rear_w  = face_center - right * 0.08
        lear_w  = face_center + right * 0.08

        kps[0]  = _proj(scn, cam, nose_w)
        kps[14] = _proj(scn, cam, reye_w)
        kps[15] = _proj(scn, cam, leye_w)
        kps[16] = _proj(scn, cam, rear_w)
        kps[17] = _proj(scn, cam, lear_w)

    return kps


def _np_draw_line(arr, x0, y0, x1, y1, color01, width=6):
    """太線を numpy で描く（円ブラシをパラメトリックに敷き詰める）。

    arr: (H, W, 4) float32 RGBA, トップダウン。
    color01: (r, g, b) in 0..1
    """
    h, w = arr.shape[:2]
    dx, dy = x1 - x0, y1 - y0
    length = max(abs(dx), abs(dy))
    if length < 0.5:
        return
    steps = int(length * 2) + 1
    half = width / 2.0
    half_sq = half * half
    rr_y, rr_x = np.mgrid[-int(half + 1):int(half + 2),
                          -int(half + 1):int(half + 2)]
    brush_mask = (rr_x * rr_x + rr_y * rr_y) <= half_sq
    bh, bw = brush_mask.shape
    for i in range(steps + 1):
        t = i / steps
        cx = int(round(x0 + t * dx))
        cy = int(round(y0 + t * dy))
        x_a = cx - bw // 2
        y_a = cy - bh // 2
        x0c = max(0, x_a); y0c = max(0, y_a)
        x1c = min(w, x_a + bw); y1c = min(h, y_a + bh)
        if x0c >= x1c or y0c >= y1c:
            continue
        sx0 = x0c - x_a; sy0 = y0c - y_a
        sx1 = sx0 + (x1c - x0c); sy1 = sy0 + (y1c - y0c)
        m = brush_mask[sy0:sy1, sx0:sx1]
        arr[y0c:y1c, x0c:x1c, 0][m] = color01[0]
        arr[y0c:y1c, x0c:x1c, 1][m] = color01[1]
        arr[y0c:y1c, x0c:x1c, 2][m] = color01[2]
        arr[y0c:y1c, x0c:x1c, 3][m] = 1.0


def _np_draw_disc(arr, cx, cy, r, color01):
    """塗り潰し円を numpy で。"""
    h, w = arr.shape[:2]
    x0c = max(0, int(cx - r)); x1c = min(w, int(cx + r + 1))
    y0c = max(0, int(cy - r)); y1c = min(h, int(cy + r + 1))
    if x0c >= x1c or y0c >= y1c:
        return
    yy, xx = np.mgrid[y0c:y1c, x0c:x1c]
    mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r
    arr[y0c:y1c, x0c:x1c, 0][mask] = color01[0]
    arr[y0c:y1c, x0c:x1c, 1][mask] = color01[1]
    arr[y0c:y1c, x0c:x1c, 2][mask] = color01[2]
    arr[y0c:y1c, x0c:x1c, 3][mask] = 1.0


def draw_openpose_image(kps, out_path, width, height):
    """OpenPose形式（黒背景、色付き骨格と関節点）を numpy で描いて PNG 保存。"""
    arr = np.zeros((height, width, 4), dtype=np.float32)
    arr[:, :, 3] = 1.0  # 黒背景でも α=1

    for (i, j), color in zip(OPENPOSE_LIMBS, OPENPOSE_LIMB_COLORS):
        if kps[i] is None or kps[j] is None:
            continue
        x1, y1, v1 = kps[i]
        x2, y2, v2 = kps[j]
        if not (v1 and v2):
            continue
        c01 = (color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)
        _np_draw_line(arr, x1, y1, x2, y2, c01, width=6)

    for idx, kp in enumerate(kps):
        if kp is None:
            continue
        x, y, v = kp
        if not v:
            continue
        col = OPENPOSE_KP_COLORS[idx]
        c01 = (col[0] / 255.0, col[1] / 255.0, col[2] / 255.0)
        _np_draw_disc(arr, x, y, 5, c01)

    _save_png_via_blender(arr, out_path, color_depth='8')
    print(f"[openpose] saved {out_path}")


# ---- メイン ---------------------------------------------------------------

def slugify(name):
    """ポーズ名をフォルダ名向けに正規化。"""
    s = os.path.splitext(os.path.basename(name))[0]
    s = re.sub(r'[^A-Za-z0-9._-]+', '_', s)
    return s.strip('_').lower() or "pose"


def render_all_poses():
    scn = bpy.context.scene
    cam = scn.camera
    char_arm = bpy.data.objects.get(CHARACTER_ARMATURE_NAME)
    if char_arm is None or char_arm.type != 'ARMATURE':
        raise RuntimeError(
            f"アーマチュア '{CHARACTER_ARMATURE_NAME}' が見つかりません。"
            "character_setup.py を先に実行してください。"
        )

    setup_compositor(OUTPUT_ROOT)
    os.makedirs(OUTPUT_ROOT, exist_ok=True)

    pose_files = sorted(glob.glob(POSE_FBX_GLOB, recursive=True))

    if not pose_files:
        print(f"[warn] ポーズFBXが見つかりません: {POSE_FBX_GLOB}")
        return

    for fbx in pose_files:
        render_single_pose(fbx, char_arm, scn)

    print("\n[done] all poses rendered.")


def apply_saved_pose_action(arm, pose_slug):
    """保存された `pose_<slug>` Action があれば Character に適用。

    動作:
      1. 全ボーンを identity (T-pose) にリセット
      2. action を assign して frame 1 を set
      3. Action が無いボーンは T-pose のまま、Action のあるボーンはその値になる

    Returns:
      True: Action が見つかって適用した
      False: 該当 Action 無し（FBXインポートにフォールバックすべし）
    """
    action_name = f"pose_{pose_slug}"
    action = bpy.data.actions.get(action_name)
    if not action:
        return False
    # 全ボーンをリセット（既存のアクション影響を除去）
    for pb in arm.pose.bones:
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    print(f"  [saved pose] using '{action_name}' instead of FBX")
    return True


def render_single_pose_framing(fbx, framing_name, char_arm=None, scn=None):
    """1つのFBXを指定 framing の5アングルでレンダー。
    framing_name は FRAMING_CONFIGS のキー（'bustup', 'lowangle', 'topdown' 等）。
    出力先は `poses/<rel_dir>/<pose_name>/<framing_name>/<angle>/`。
    """
    cfg = FRAMING_CONFIGS[framing_name]
    angles = make_framing_angles(cfg["distance"])

    if char_arm is None:
        char_arm = bpy.data.objects[CHARACTER_ARMATURE_NAME]
    if scn is None:
        scn = bpy.context.scene

    pose_name = slugify(fbx)
    rel_dir = os.path.relpath(os.path.dirname(fbx), POSE_FBX_ROOT)
    if rel_dir == ".":
        rel_dir = ""
    category = rel_dir.split(os.sep)[0] if rel_dir else ""
    pose_dir = os.path.join(OUTPUT_ROOT, rel_dir, pose_name, framing_name)
    os.makedirs(pose_dir, exist_ok=True)
    print(f"\n=== [{category}] {pose_name}  {framing_name.upper()} ===")

    # ポーズ転写: 保存 Action 優先、無ければ FBX フォールバック
    if not apply_saved_pose_action(char_arm, pose_name):
        src_arm, extras = import_pose_fbx(fbx)
        frame = pick_pose_frame(src_arm, pose_slug=pose_name)
        print(f"  frame {frame}")
        copy_pose(src_arm, char_arm, frame)
        remove_obj_tree(src_arm, extras)

    apply_head_target(char_arm, pose_name, category)
    apply_pose_expression(pose_name, category=category)

    for angle_cfg in angles:
        angle_name = angle_cfg["name"]
        angle_dir = os.path.join(pose_dir, angle_name)
        os.makedirs(angle_dir, exist_ok=True)

        apply_framing_camera_angle(angle_cfg, cfg)
        bpy.context.view_layer.update()

        update_compositor_paths(angle_dir)
        scn.frame_set(1)
        bpy.ops.render.render(write_still=False)
        postprocess_passes(angle_dir)

        kps = collect_openpose_keypoints(char_arm)
        op_path = os.path.join(angle_dir, "openpose.png")
        draw_openpose_image(kps, op_path, scn.render.resolution_x, scn.render.resolution_y)
        print(f"  -> {framing_name}/{angle_name}")


def render_single_pose_bustup(fbx, char_arm=None, scn=None):
    """1つのFBXを bustup 5アングルでレンダー。
    fullbody の `render_single_pose` を実行した直後に呼ぶ前提（pose 転写は1回で済む）でも
    単体でも動くよう、ポーズ転写・表情・head制約まで自前でやる。
    出力先は `poses/<rel_dir>/<pose_name>/bustup/<angle>/{beauty,depth,normal,openpose}.png`
    """
    if char_arm is None:
        char_arm = bpy.data.objects[CHARACTER_ARMATURE_NAME]
    if scn is None:
        scn = bpy.context.scene

    pose_name = slugify(fbx)
    rel_dir = os.path.relpath(os.path.dirname(fbx), POSE_FBX_ROOT)
    if rel_dir == ".":
        rel_dir = ""
    category = rel_dir.split(os.sep)[0] if rel_dir else ""
    pose_dir = os.path.join(OUTPUT_ROOT, rel_dir, pose_name, "bustup")
    os.makedirs(pose_dir, exist_ok=True)
    print(f"\n=== [{category}] {pose_name}  BUSTUP ===")

    # ポーズ転写: 保存 Action 優先、無ければ FBX フォールバック
    if not apply_saved_pose_action(char_arm, pose_name):
        src_arm, extras = import_pose_fbx(fbx)
        frame = pick_pose_frame(src_arm, pose_slug=pose_name)
        print(f"  frame {frame}")
        copy_pose(src_arm, char_arm, frame)
        remove_obj_tree(src_arm, extras)

    apply_head_target(char_arm, pose_name, category)
    apply_pose_expression(pose_name, category=category)

    # 5アングル × bustup 構図
    for angle_cfg in BUSTUP_CAMERA_ANGLES:
        angle_name = angle_cfg["name"]
        angle_dir = os.path.join(pose_dir, angle_name)
        os.makedirs(angle_dir, exist_ok=True)

        apply_bustup_camera_angle(angle_cfg)
        bpy.context.view_layer.update()

        update_compositor_paths(angle_dir)
        scn.frame_set(1)
        bpy.ops.render.render(write_still=False)
        postprocess_passes(angle_dir)

        kps = collect_openpose_keypoints(char_arm)
        op_path = os.path.join(angle_dir, "openpose.png")
        draw_openpose_image(kps, op_path, scn.render.resolution_x, scn.render.resolution_y)
        print(f"  -> bustup/{angle_name}")


def render_single_pose(fbx, char_arm=None, scn=None):
    """1つのFBXを5アングルでレンダー。"""
    if char_arm is None:
        char_arm = bpy.data.objects[CHARACTER_ARMATURE_NAME]
    if scn is None:
        scn = bpy.context.scene

    pose_name = slugify(fbx)
    rel_dir = os.path.relpath(os.path.dirname(fbx), POSE_FBX_ROOT)
    if rel_dir == ".":
        rel_dir = ""
    category = rel_dir.split(os.sep)[0] if rel_dir else ""
    # 2026-05-16: fullbody も `fullbody/` サブフォルダ配下に出力するように変更
    # （bustup/lowangle/topdown と階層を揃える）
    pose_dir = os.path.join(OUTPUT_ROOT, rel_dir, pose_name, "fullbody")
    os.makedirs(pose_dir, exist_ok=True)
    print(f"\n=== [{category}] {pose_name}  FULLBODY ===")

    # ポーズ転写: 保存 Action 優先、無ければ FBX フォールバック
    if not apply_saved_pose_action(char_arm, pose_name):
        src_arm, extras = import_pose_fbx(fbx)
        frame = pick_pose_frame(src_arm, pose_slug=pose_name)
        print(f"  frame {frame}")
        copy_pose(src_arm, char_arm, frame)
        remove_obj_tree(src_arm, extras)

    # head ターゲット適用（グローブ追従 > 正面固定 > 制約なし）
    apply_head_target(char_arm, pose_name, category)

    # 表情（カテゴリデフォルト含む）
    apply_pose_expression(pose_name, category=category)

    # 5アングルでループ
    for angle_cfg in STANDARD_CAMERA_ANGLES:
        angle_name = angle_cfg["name"]
        angle_dir = os.path.join(pose_dir, angle_name)
        os.makedirs(angle_dir, exist_ok=True)

        apply_standard_camera_angle(angle_cfg)
        bpy.context.view_layer.update()

        update_compositor_paths(angle_dir)
        scn.frame_set(1)
        bpy.ops.render.render(write_still=False)
        postprocess_passes(angle_dir)

        kps = collect_openpose_keypoints(char_arm)
        op_path = os.path.join(angle_dir, "openpose.png")
        draw_openpose_image(kps, op_path, scn.render.resolution_x, scn.render.resolution_y)
        print(f"  -> {angle_name}")


# ---- 表情単独レンダー ------------------------------------------------------

def _find_face_mesh():
    for o in bpy.context.scene.objects:
        if o.type == 'MESH' and 'face' in o.name.lower() and o.data.shape_keys:
            return o
    return None


def render_all_expressions():
    """T-pose固定＋顔クローズアップで、各表情を expressions/<name>/ に出力。"""
    scn = bpy.context.scene
    char_arm = bpy.data.objects.get(CHARACTER_ARMATURE_NAME)
    cam = scn.camera
    face = _find_face_mesh()
    if not (char_arm and cam and face):
        raise RuntimeError("Character / Camera / Face mesh が見つかりません")

    # T-pose に
    if char_arm.animation_data and char_arm.animation_data.action:
        char_arm.animation_data.action = None
    for pb in char_arm.pose.bones:
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
        pb.location = (0, 0, 0)
    # 頭のLookAtCam も外す（正面顔で固定）
    head = None
    for pb in char_arm.pose.bones:
        if pb.name.endswith(":Head") or pb.name == "Head":
            head = pb
            break
    if head:
        for c in list(head.constraints):
            if c.name == 'LookAtCam':
                head.constraints.remove(c)

    # カメラ保存して顔クローズアップに切替
    old_cam = {
        "location": cam.location.copy(),
        "rotation_euler": cam.rotation_euler.copy(),
        "lens": cam.data.lens,
    }
    cam.location = FACE_CAMERA_CONFIG["location"]
    cam.rotation_euler = tuple(math.radians(x) for x in FACE_CAMERA_CONFIG["rotation_euler_deg"])
    cam.data.lens = FACE_CAMERA_CONFIG["lens"]

    os.makedirs(EXPRESSIONS_OUTPUT_ROOT, exist_ok=True)
    setup_compositor(EXPRESSIONS_OUTPUT_ROOT)

    sk = face.data.shape_keys
    for short_name, sk_spec in EXPRESSION_LIST:
        # 文字列なら単一適用、dictなら複数同時適用
        if isinstance(sk_spec, str):
            apply_map = {sk_spec: 1.0}
        else:
            apply_map = dict(sk_spec)
        print(f"\n=== expression: {short_name} ({apply_map}) ===")
        # slug に "/" 含まれる場合はサブフォルダに展開
        short_parts = short_name.split('/')
        out_dir = os.path.join(EXPRESSIONS_OUTPUT_ROOT, *short_parts)
        os.makedirs(out_dir, exist_ok=True)

        # 全シェイプキーをリセット
        for kb in sk.key_blocks:
            if kb.name != 'Basis':
                kb.value = 0.0
        # 該当のみON
        applied_any = False
        for sk_name, val in apply_map.items():
            kb = sk.key_blocks.get(sk_name)
            if kb:
                kb.value = float(val)
                applied_any = True
            else:
                print(f"  [warn] shape key '{sk_name}' not found")
        if not applied_any:
            continue

        bpy.context.view_layer.update()
        update_compositor_paths(out_dir)
        scn.frame_set(1)
        bpy.ops.render.render(write_still=False)
        postprocess_passes(out_dir)
        kps = collect_openpose_keypoints(char_arm)
        draw_openpose_image(kps, os.path.join(out_dir, "openpose.png"),
                           scn.render.resolution_x, scn.render.resolution_y)

    # カメラ復元
    cam.location = old_cam["location"]
    cam.rotation_euler = old_cam["rotation_euler"]
    cam.data.lens = old_cam["lens"]

    # シェイプキー全リセット（次の作業に影響しないように）
    for kb in sk.key_blocks:
        if kb.name != 'Basis':
            kb.value = 0.0

    print(f"\n[done] all expressions rendered to {EXPRESSIONS_OUTPUT_ROOT}")


if __name__ == "__main__":
    render_all_poses()
