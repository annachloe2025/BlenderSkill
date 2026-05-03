# 用途: 雪片を多数散布（パーティクルの代替・確実版）
# 動作確認: 2026-05-04 / Blender MCP

import bpy
import random


def make_snow_mat():
    if "Snow" in bpy.data.materials:
        return bpy.data.materials["Snow"]
    mat = bpy.data.materials.new(name="Snow")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.95, 0.97, 1.0, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.4
    return mat


def scatter_snow(count=600, area=(-5, 5, -5, 5), z_range=(0.1, 6.0), seed=42):
    """指定範囲に雪片を散布。Linked Duplicate でメモリ節約"""
    snow_mat = make_snow_mat()

    # テンプレートを1個だけ作る
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.05, subdivisions=1, location=(0, 0, 0))
    template = bpy.context.active_object
    template.name = "snow_template"
    template.data.materials.append(snow_mat)
    template.hide_render = True
    template.hide_viewport = True

    random.seed(seed)
    x_min, x_max, y_min, y_max = area
    z_min, z_max = z_range
    for i in range(count):
        new = template.copy()        # データはリンクで共有（軽い）
        bpy.context.collection.objects.link(new)
        new.location = (
            random.uniform(x_min, x_max),
            random.uniform(y_min, y_max),
            random.uniform(z_min, z_max),
        )
        s = random.uniform(0.5, 1.5)
        new.scale = (s, s, s)
        new.name = f"flake_{i:03d}"
