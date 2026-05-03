# 用途: 4種のライト（Point / Sun / Spot / Area）を順次レンダリング比較
# 動作確認: 2026-05-04 / Blender MCP
# 依存: シーンに被写体が既にある前提

import bpy
import math


def replace_light(light_type):
    """既存ライトを全削除して、指定タイプの1個を追加"""
    for o in list(bpy.context.scene.objects):
        if o.type == 'LIGHT':
            bpy.data.objects.remove(o, do_unlink=True)

    bpy.ops.object.light_add(type=light_type, location=(2, -2, 4))
    light = bpy.context.active_object
    light.rotation_euler = (math.radians(45), math.radians(20), math.radians(30))

    # タイプ別の代表値
    if light_type == 'POINT':
        light.data.energy = 800
        light.data.shadow_soft_size = 0.3
    elif light_type == 'SUN':
        light.data.energy = 4
        light.data.angle = math.radians(2)
    elif light_type == 'SPOT':
        light.data.energy = 1500
        light.data.spot_size = math.radians(50)
        light.data.spot_blend = 0.3
    elif light_type == 'AREA':
        light.data.energy = 600
        light.data.size = 2.5
        light.data.shape = 'RECTANGLE'
        light.data.size_y = 1.5
    return light


# 使い方: replace_light('SUN') してから render
# 4種を順次レンダリングするなら for で回す:
# for kind in ['POINT', 'SUN', 'SPOT', 'AREA']:
#     replace_light(kind)
#     bpy.ops.render.render(write_still=True)
