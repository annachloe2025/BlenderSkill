# 用途: Principled BSDF マテリアルをコードで作成・割り当て
# 動作確認: 2026-05-04 / Blender MCP

import bpy


def make_material(name, base_color, metallic=0.0, roughness=0.5):
    """色・メタリック・粗さの3パラメータで Principled BSDF を作る"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def assign_material(obj, mat):
    """既存スロットがあれば置き換え、なければ追加"""
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


# 使用例: 木製・金属・床の3種類
mat_wood  = make_material("Wood",  (0.40, 0.22, 0.10), metallic=0.0, roughness=0.6)
mat_metal = make_material("Metal", (0.55, 0.55, 0.58), metallic=1.0, roughness=0.3)
mat_floor = make_material("Floor", (0.85, 0.78, 0.65), metallic=0.0, roughness=0.85)

# 適用例:
# assign_material(some_cube, mat_wood)
