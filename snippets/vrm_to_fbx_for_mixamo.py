"""vrm_to_fbx_for_mixamo.py
--------------------------
VRoid Studio で書き出した VRM を読み込み、Mixamo の auto-rigger が
受け入れられる FBX に書き出すユーティリティ。

前提:
- Blender 5.x
- VRM Add-on for Blender が有効 (bpy.ops.import_scene.vrm が使える)

処理:
1. シーンを空にする
2. VRM をインポート（テクスチャ・MToon マテリアル・アーマチュア込み）
3. アーマチュア状態を確認（A-Poseのままで先にMixamoに投げてみるのが現実的）
4. Selected Objects（アーマチュア + メッシュ全部）で FBX エクスポート
   - Embed Textures, -Z Forward / Y Up, Apply Scalings='FBX_SCALE_NONE'

Mixamo 側の作業:
- mixamo.com → UPLOAD CHARACTER → 出力 FBX をドロップ
- 顎/手首x2/肘x2/膝x2/股 のジョイントマーカーを配置
- Auto-Rigger 完了 → With Skin（T-Pose）で再 DL
"""

import bpy
import os

# ---- 設定 -----------------------------------------------------------------

VRM_PATH = r"C:\Users\hoeho\Documents\Claude\BlenderSkill\blender\assets\characters\base_motoko\base_motoko.vrm"
OUT_FBX  = r"C:\Users\hoeho\Documents\Claude\BlenderSkill\blender\assets\characters\base_motoko\base_motoko_for_mixamo.fbx"


# ---- ヘルパー -------------------------------------------------------------

def clear_scene():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for coll in (bpy.data.meshes, bpy.data.armatures, bpy.data.materials,
                 bpy.data.images, bpy.data.actions):
        for block in list(coll):
            if block.users == 0:
                coll.remove(block)


def import_vrm(filepath):
    bpy.ops.import_scene.vrm(filepath=filepath)
    arms = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    return arms, meshes


def select_for_export(arm, meshes):
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    for m in meshes:
        m.select_set(True)
    bpy.context.view_layer.objects.active = arm


def export_fbx_for_mixamo(filepath):
    """Mixamo の auto-rigger が要求する設定で FBX を書き出す。

    重要: object_types は MESH のみ。アーマチュアを含めると Mixamo が
    「これはもうリグ済み」と判定して auto-rigger を省略してしまい、
    元のリグ（VRoid Humanoid）のまま FBX が返ってくる罠がある。
    use_mesh_modifiers=True で T-Pose のバインド状態を焼き付けて書き出す。
    """
    bpy.ops.export_scene.fbx(
        filepath=filepath,
        use_selection=True,
        apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_NONE',
        axis_forward='-Z',
        axis_up='Y',
        bake_space_transform=False,
        object_types={'MESH'},
        use_mesh_modifiers=True,
        mesh_smooth_type='OFF',
        path_mode='COPY',
        embed_textures=True,
        bake_anim=False,
    )


def main():
    if not os.path.exists(VRM_PATH):
        raise FileNotFoundError(f"VRM not found: {VRM_PATH}")
    clear_scene()
    arms, meshes = import_vrm(VRM_PATH)
    if not arms:
        raise RuntimeError("VRM をインポートしたがアーマチュアが見つからない")
    arm = arms[0]
    print(f"[vrm] armature='{arm.name}', meshes={[m.name for m in meshes]}")
    print(f"[vrm] bone count={len(arm.data.bones)}")
    print(f"[vrm] dimensions={tuple(round(x,3) for x in arm.dimensions)}")

    os.makedirs(os.path.dirname(OUT_FBX), exist_ok=True)
    select_for_export(arm, meshes)
    export_fbx_for_mixamo(OUT_FBX)
    size_kb = os.path.getsize(OUT_FBX) / 1024
    print(f"[done] Exported FBX -> {OUT_FBX} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
