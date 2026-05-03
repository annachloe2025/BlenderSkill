# 用途: World に Sky Texture（Hosek/Wilkie）を設定して空からの光で照らす
# 動作確認: 2026-05-04 / Blender MCP（HOSEK_WILKIE 利用）
# Blender 2.90+ なら 'NISHITA' のほうが綺麗（より物理ベース）

import bpy
import math


def setup_sky_world(turbidity=2.5, ground_albedo=0.3,
                    sun_dir=(0.3, -0.7, 0.6), strength=1.0):
    """World ノードを Hosek/Wilkie 空モデルで再構築"""
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree

    for n in list(nt.nodes):
        nt.nodes.remove(n)

    output = nt.nodes.new('ShaderNodeOutputWorld');  output.location = (400, 0)
    bg     = nt.nodes.new('ShaderNodeBackground');   bg.location     = (200, 0)
    sky    = nt.nodes.new('ShaderNodeTexSky');       sky.location    = (-100, 0)
    sky.sky_type      = 'HOSEK_WILKIE'   # 'NISHITA' があるならそちら推奨
    sky.turbidity     = turbidity        # 1=澄んだ空, 10=曇りに近い
    sky.ground_albedo = ground_albedo    # 地面反射色
    sky.sun_direction = sun_dir          # 太陽方向のベクトル
    bg.inputs['Strength'].default_value = strength

    nt.links.new(sky.outputs['Color'],     bg.inputs['Color'])
    nt.links.new(bg.outputs['Background'], output.inputs['Surface'])
    return world
