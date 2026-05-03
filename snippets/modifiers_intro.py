# 用途: モディファイアの基本3種（Subdivision Surface / Bevel / Mirror）
# 動作確認: 2026-05-04 / Blender MCP
# 依存: clear_scene.py

import bpy

# --- Subdivision Surface（メッシュを滑らかに細分化）---
bpy.ops.mesh.primitive_cube_add(size=1.5, location=(-3, 0, 0))
obj = bpy.context.active_object
m = obj.modifiers.new(name="Subsurf", type='SUBSURF')
m.levels = 2          # ビューポート表示の細分化レベル
m.render_levels = 3   # レンダリング時の細分化レベル（より高品質）
bpy.ops.object.shade_smooth()  # スムーズシェードと併用すると効果大

# --- Bevel（エッジを面取り）---
bpy.ops.mesh.primitive_cube_add(size=1.5, location=(0, 0, 0))
obj = bpy.context.active_object
m = obj.modifiers.new(name="Bevel", type='BEVEL')
m.width = 0.15        # 面取り幅
m.segments = 4        # セグメント数（多いほど丸い）

# --- Mirror（指定軸で対称コピー）---
bpy.ops.mesh.primitive_cube_add(size=0.8, location=(3.5, 0.6, 0))
obj = bpy.context.active_object
m = obj.modifiers.new(name="Mirror", type='MIRROR')
m.use_axis[0] = False  # X軸ミラーOFF
m.use_axis[1] = True   # Y軸ミラーON（オブジェクトの原点を基準に対称）
m.use_axis[2] = False  # Z軸ミラーOFF

# モディファイアを「適用」して実メッシュ化したいときは：
# bpy.context.view_layer.objects.active = obj
# bpy.ops.object.modifier_apply(modifier="Mirror")
