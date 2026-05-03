# 用途: プロシージャル木目マテリアルをコードでノードグラフ構築
# 動作確認: 2026-05-04 / Blender MCP
# 構成: TexCoord → Noise → Wave → ColorRamp → BSDF (BaseColor)
#                     └→ Bump → BSDF (Normal)

import bpy


def make_procedural_wood(name="ProcWood",
                         base_color=(0.55, 0.32, 0.15),
                         dark_color=(0.20, 0.10, 0.04),
                         grain_scale=12.0):
    """ノードグラフをゼロから構築する木目マテリアル"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree

    # デフォルトノードを全消し
    for n in list(nt.nodes):
        nt.nodes.remove(n)

    # ノードを生成（座標は UI 上で見やすくするため）
    output = nt.nodes.new('ShaderNodeOutputMaterial');     output.location = (600, 0)
    bsdf   = nt.nodes.new('ShaderNodeBsdfPrincipled');     bsdf.location   = (300, 0)
    ramp   = nt.nodes.new('ShaderNodeValToRGB');           ramp.location   = (0, 100)
    wave   = nt.nodes.new('ShaderNodeTexWave');            wave.location   = (-300, 100)
    noise  = nt.nodes.new('ShaderNodeTexNoise');           noise.location  = (-600, 100)
    coord  = nt.nodes.new('ShaderNodeTexCoord');           coord.location  = (-900, 100)
    bump   = nt.nodes.new('ShaderNodeBump');               bump.location   = (0, -200)

    # パラメータ
    noise.inputs['Scale'].default_value = grain_scale
    noise.inputs['Detail'].default_value = 4
    noise.inputs['Roughness'].default_value = 0.6
    wave.inputs['Scale'].default_value = grain_scale * 0.4
    wave.inputs['Distortion'].default_value = 6.0
    wave.inputs['Detail'].default_value = 2.0

    # カラーランプ: 明るい木地 → 濃い木目
    ramp.color_ramp.elements[0].position = 0.40
    ramp.color_ramp.elements[0].color    = (*base_color, 1.0)
    ramp.color_ramp.elements[1].position = 0.60
    ramp.color_ramp.elements[1].color    = (*dark_color, 1.0)

    # BSDF
    bsdf.inputs['Metallic'].default_value  = 0.0
    bsdf.inputs['Roughness'].default_value = 0.55

    # バンプ強度
    bump.inputs['Strength'].default_value = 0.15

    # リンク（接続）
    L = nt.links.new
    L(coord.outputs['Object'], noise.inputs['Vector'])
    L(noise.outputs['Fac'],    wave.inputs['Vector'])
    L(wave.outputs['Fac'],     ramp.inputs['Fac'])
    L(ramp.outputs['Color'],   bsdf.inputs['Base Color'])
    L(wave.outputs['Fac'],     bump.inputs['Height'])
    L(bump.outputs['Normal'],  bsdf.inputs['Normal'])
    L(bsdf.outputs['BSDF'],    output.inputs['Surface'])

    return mat
