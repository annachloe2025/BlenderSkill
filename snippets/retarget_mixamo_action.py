"""retarget_mixamo_action.py
--------------------------
Mixamo FBX のアニメーションを「Apply All Transforms 済み」Armature に
当てるためのユーティリティ。

背景:
Apply All Transforms した Armature (rotation=0, scale=1) では、Mixamo FBX を
通常 import 後に action をそのまま当てると以下の 2 問題が出る:

1. **ボーン名衝突** — 既存 Armature と同じ `mixamorig:` プレフィックスがあると
   新 import は `mixamorig1:` などにリネームされる。action の fcurves は
   その新名を参照するので、既存 Armature の `mixamorig:` には当たらない。

2. **Hips location が 100 倍** — Mixamo のアニメは cm 単位で keyframe が
   保存されており、import 時は armature scale=0.01 でつじつまを合わせている。
   Apply Scale 後は armature scale=1 になるので、Hips の location キーが
   そのまま 100 倍の値に見えてしまう (キャラが地下数十 m に潜る)。

このユーティリティは上記 2 つを自動補正して、新 Armature に当てられる
action を返す。

使い方:
    # Blender テキストエディタから:
    import sys
    sys.path.insert(0, r'C:\\Users\\hoeho\\Documents\\Claude\\BlenderSkill\\snippets')
    from retarget_mixamo_action import retarget_mixamo_action, batch_retarget

    # 単一 FBX を Character に当てる:
    action = retarget_mixamo_action(
        fbx_path=r"...\\Hook.fbx",
        target_armature_name='Character',
    )

    # フォルダ全体を読み込む (assign はしない):
    actions = batch_retarget(
        folder=r"...\\assets\\animations\\attacks",
        target_armature_name='Character',
    )

Tested on Blender 5.x (slotted Actions API).
"""

import bpy
import os
import re
import glob


# Mixamo の cm 単位 → Blender の m 単位への変換比率
# Apply Scale 済みなら 0.01 を使う
DEFAULT_HIPS_SCALE = 0.01

# `mixamorigN:` (N は 0 個以上の数字) を `mixamorig:` に正規化する regex
_MIXAMORIG_RENAME = re.compile(r'mixamorig\d+:')


def _normalize_bone_paths(action):
    """action 内の全 fcurve の data_path を mixamorigN: → mixamorig: に置換。"""
    fixed = 0
    for layer in action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    new_path = _MIXAMORIG_RENAME.sub('mixamorig:', fc.data_path)
                    if new_path != fc.data_path:
                        fc.data_path = new_path
                        fixed += 1
    return fixed


def _scale_hips_location(action, scale):
    """Hips の location キーフレーム値を scale 倍する。"""
    hips_path = 'pose.bones["mixamorig:Hips"].location'
    fixed = 0
    for layer in action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    if fc.data_path == hips_path:
                        for kp in fc.keyframe_points:
                            kp.co[1] *= scale
                            kp.handle_left[1] *= scale
                            kp.handle_right[1] *= scale
                        fc.update()
                        fixed += 1
    return fixed


def _slugify_filename(fbx_path):
    """'Jab Cross.fbx' → 'anim_jab_cross' のような名前に。"""
    base = os.path.splitext(os.path.basename(fbx_path))[0]
    base = re.sub(r'[^\w]+', '_', base).lower().strip('_')
    return f"anim_{base}"


def _cleanup_imported_objects(new_objs):
    """import で増えたオブジェクトと孤立 datablock を削除。"""
    for o in list(new_objs):
        if o.name not in bpy.data.objects:
            continue
        if o.type == 'ARMATURE':
            arm_data = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if arm_data and arm_data.users == 0:
                bpy.data.armatures.remove(arm_data)
        else:
            mesh_data = o.data if hasattr(o, 'data') else None
            bpy.data.objects.remove(o, do_unlink=True)
            if mesh_data and hasattr(mesh_data, 'name') and mesh_data.users == 0:
                # Mesh など
                try:
                    bpy.data.meshes.remove(mesh_data)
                except (TypeError, ReferenceError):
                    pass


def retarget_mixamo_action(
    fbx_path,
    target_armature_name='Character',
    action_rename=None,
    assign=True,
    hips_scale=DEFAULT_HIPS_SCALE,
    set_frame_range=True,
):
    """Mixamo FBX を import → action を補正 → target armature に当てる。

    Args:
        fbx_path: Mixamo FBX ファイルパス
        target_armature_name: 当てたい既存 armature の object 名
        action_rename: action の新名。None なら fbx 名から自動命名
        assign: True なら target.animation_data.action に自動セット
        hips_scale: Hips location の倍率
            - Apply Scale 済み armature なら 0.01 (デフォルト)
            - Apply 前の armature (scale=0.01 のまま) なら 1.0
        set_frame_range: True なら scene の frame_start/end を action の range に合わせる

    Returns:
        bpy.types.Action: 補正済み action
    """
    if not os.path.exists(fbx_path):
        raise FileNotFoundError(f"FBX not found: {fbx_path}")

    target = bpy.data.objects.get(target_armature_name)
    if target is None:
        raise ValueError(f"Target armature '{target_armature_name}' not found in scene")
    if target.type != 'ARMATURE':
        raise ValueError(f"'{target_armature_name}' is not an ARMATURE (type={target.type})")

    # ---- import 前の状態を記録 ----
    before_objs = set(bpy.data.objects)
    before_actions = set(bpy.data.actions)

    # ---- FBX import ----
    bpy.ops.import_scene.fbx(
        filepath=fbx_path,
        use_anim=True,
        automatic_bone_orientation=True,
    )

    new_objs = set(bpy.data.objects) - before_objs
    new_actions = set(bpy.data.actions) - before_actions

    if not new_actions:
        _cleanup_imported_objects(new_objs)
        raise RuntimeError(f"No new action imported from {fbx_path}")

    # Mixamo の素のアニメは action 1 つだけのはず
    action = next(iter(new_actions))

    # ---- 1. ボーン名衝突補正 ----
    bone_fixes = _normalize_bone_paths(action)

    # ---- 2. Hips location 値補正 ----
    hips_fixes = _scale_hips_location(action, hips_scale)

    # ---- action リネーム & fake user ----
    if action_rename is None:
        action_rename = _slugify_filename(fbx_path)
    # 衝突するなら .001 などにせず、上書きさせない。既存があれば一旦消す。
    if action_rename in bpy.data.actions and bpy.data.actions[action_rename] is not action:
        existing = bpy.data.actions[action_rename]
        existing.user_clear()
        bpy.data.actions.remove(existing)
    action.name = action_rename
    action.use_fake_user = True

    # ---- 一時 import object を削除 ----
    _cleanup_imported_objects(new_objs)

    # ---- target armature に assign ----
    if assign:
        if not target.animation_data:
            target.animation_data_create()
        target.animation_data.action = action

        if set_frame_range:
            scn = bpy.context.scene
            scn.frame_start = int(action.frame_range[0])
            scn.frame_end = int(action.frame_range[1])
            scn.frame_set(int(action.frame_range[0]))

    print(f"[retarget] '{action.name}' <- {os.path.basename(fbx_path)}")
    print(f"           bone-name fixes={bone_fixes}, hips-location fixes={hips_fixes}")
    print(f"           frame range: {int(action.frame_range[0])}-{int(action.frame_range[1])}")
    return action


def batch_retarget(
    folder,
    target_armature_name='Character',
    recursive=True,
    hips_scale=DEFAULT_HIPS_SCALE,
):
    """フォルダ内の全 .fbx を順次取り込む (assign はしない)。

    Args:
        folder: 検索するルートフォルダ
        target_armature_name: ボーン名検証用 (実際の assign はしない)
        recursive: True なら再帰検索
        hips_scale: Hips location 倍率

    Returns:
        list[bpy.types.Action]: 補正済み action 群
    """
    pattern = '**/*.fbx' if recursive else '*.fbx'
    fbx_files = sorted(glob.glob(os.path.join(folder, pattern), recursive=recursive))
    print(f"[batch_retarget] Found {len(fbx_files)} FBX files in {folder}")

    actions = []
    for fbx in fbx_files:
        try:
            action = retarget_mixamo_action(
                fbx_path=fbx,
                target_armature_name=target_armature_name,
                assign=False,
                hips_scale=hips_scale,
                set_frame_range=False,
            )
            actions.append(action)
        except Exception as e:
            print(f"[batch_retarget] FAILED for {fbx}: {e}")

    print(f"[batch_retarget] Done. {len(actions)} / {len(fbx_files)} actions imported.")
    return actions


# ---- スタンドアロン実行例 ----
if __name__ == "__main__":
    # 単一 FBX をテスト
    action = retarget_mixamo_action(
        fbx_path=r"C:\Users\hoeho\Documents\Claude\BlenderSkill\blender\assets\animations\attacks\Jab Cross.fbx",
        target_armature_name='Character',
    )
    print(f"\nLoaded: {action.name}")
