# 用途: 同じシーンを Cycles と Eevee の両方でレンダリングして比較
# 動作確認: 2026-05-04 / Blender MCP

import bpy

scene = bpy.context.scene
scene.render.resolution_x = 700
scene.render.resolution_y = 450

# === Cycles ===
scene.render.engine = 'CYCLES'
scene.cycles.samples = 96
scene.cycles.use_denoising = True
scene.render.filepath = "/tmp/cycles.png"
scene.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)

# === Eevee（バージョンに応じて Eevee Next か旧 Eevee）===
available = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
eevee_engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in available else 'BLENDER_EEVEE'
scene.render.engine = eevee_engine
scene.render.filepath = "/tmp/eevee.png"
bpy.ops.render.render(write_still=True)
