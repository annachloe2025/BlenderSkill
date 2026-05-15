# 用途: Phase 1〜5 の集大成 — 雪景色の椅子を1本のスクリプトで再現
# 動作確認: 2026-05-04 / Blender MCP / Cycles 128samples + denoising
#
# 使用技術（全フェーズ統合）:
#   Phase 1: Plane / Cube / Cylinder / for ループ配置
#   Phase 2: 角丸ボックス（subdivide+bevel）/ UV smart_project
#   Phase 3: Principled BSDF / プロシージャル木目（コードでノードグラフ）
#   Phase 4: Sky Texture(Hosek/Wilkie) / Sun ライト / カメラDoF / Cycles
#   Phase 5: Linked Duplicate で雪片散布

import bpy
import math
import random


# ============ マテリアル ============
def make_principled(name, color, metallic=0.0, roughness=0.5):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def make_procedural_wood(name, base_color=(0.55, 0.32, 0.15),
                          dark_color=(0.20, 0.10, 0.04), grain_scale=12.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    output = nt.nodes.new('ShaderNodeOutputMaterial');     output.location = (600, 0)
    bsdf   = nt.nodes.new('ShaderNodeBsdfPrincipled');     bsdf.location   = (300, 0)
    ramp   = nt.nodes.new('ShaderNodeValToRGB');           ramp.location   = (0, 100)
    wave   = nt.nodes.new('ShaderNodeTexWave');            wave.location   = (-300, 100)
    noise  = nt.nodes.new('ShaderNodeTexNoise');           noise.location  = (-600, 100)
    coord  = nt.nodes.new('ShaderNodeTexCoord');           coord.location  = (-900, 100)
    bump   = nt.nodes.new('ShaderNodeBump');               bump.location   = (0, -200)
    noise.inputs['Scale'].default_value = grain_scale
    wave.inputs['Scale'].default_value = grain_scale * 0.4
    wave.inputs['Distortion'].default_value = 6.0
    ramp.color_ramp.elements[0].position = 0.40
    ramp.color_ramp.elements[0].color    = (*base_color, 1.0)
    ramp.color_ramp.elements[1].position = 0.60
    ramp.color_ramp.elements[1].color    = (*dark_color, 1.0)
    bsdf.inputs['Metallic'].default_value  = 0.0
    bsdf.inputs['Roughness'].default_value = 0.55
    bump.inputs['Strength'].default_value = 0.15
    L = nt.links.new
    L(coord.outputs['Object'], noise.inputs['Vector'])
    L(noise.outputs['Fac'],    wave.inputs['Vector'])
    L(wave.outputs['Fac'],     ramp.inputs['Fac'])
    L(ramp.outputs['Color'],   bsdf.inputs['Base Color'])
    L(wave.outputs['Fac'],     bump.inputs['Height'])
    L(bump.outputs['Normal'],  bsdf.inputs['Normal'])
    L(bsdf.outputs['BSDF'],    output.inputs['Surface'])
    return mat


def assign_mat(obj, mat):
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


def add_rounded_box(name, location, scale, bevel_offset=0.04, bevel_segments=3):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.active_object
    obj.scale = scale
    obj.name = name
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bevel(offset=bevel_offset, segments=bevel_segments, affect='EDGES')
    bpy.ops.uv.smart_project(angle_limit=66, island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.shade_smooth()
    return obj


def setup_sky_world(turbidity=4.0, sun_dir=(-0.3, 0.5, 0.5), strength=0.4):
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
    sky.sky_type = 'HOSEK_WILKIE'
    sky.turbidity = turbidity
    sky.sun_direction = sun_dir
    bg.inputs['Strength'].default_value = strength
    nt.links.new(sky.outputs['Color'], bg.inputs['Color'])
    nt.links.new(bg.outputs['Background'], output.inputs['Surface'])


# ============ シーン構築 ============
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

mat_wood  = make_procedural_wood("Wood")
mat_metal = make_principled("Metal", (0.60, 0.60, 0.62), metallic=1.0, roughness=0.25)
mat_snow  = make_principled("Snow",  (0.95, 0.97, 1.0), metallic=0.0, roughness=0.3)

# 床
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "snow_floor"
assign_mat(floor, mat_snow)

# 椅子（座面 / 脚×4 / 背もたれ）
SEAT_W, SEAT_D, SEAT_T = 1.0, 1.0, 0.08
SEAT_H = 0.9
LEG_R = 0.06
BACK_W, BACK_D, BACK_H = 1.0, 0.06, 0.9

seat = add_rounded_box("seat", (0, 0, SEAT_H), (SEAT_W, SEAT_D, SEAT_T))
assign_mat(seat, mat_wood)
leg_offset_x = SEAT_W / 2 - LEG_R * 1.5
leg_offset_y = SEAT_D / 2 - LEG_R * 1.5
for i, (sx, sy) in enumerate([(1, 1), (1, -1), (-1, 1), (-1, -1)]):
    bpy.ops.mesh.primitive_cylinder_add(
        radius=LEG_R, depth=SEAT_H,
        location=(sx * leg_offset_x, sy * leg_offset_y, SEAT_H / 2),
    )
    bpy.context.active_object.name = f"leg_{i+1}"
    bpy.ops.object.shade_smooth()
    assign_mat(bpy.context.active_object, mat_metal)
back = add_rounded_box("backrest", (0, -SEAT_D / 2 + BACK_D / 2, SEAT_H + BACK_H / 2),
                       (BACK_W, BACK_D, BACK_H))
assign_mat(back, mat_wood)

# 雪片を Linked Duplicate で散布
bpy.ops.mesh.primitive_ico_sphere_add(radius=0.04, subdivisions=1, location=(0, 0, 0))
template = bpy.context.active_object
template.name = "snow_template"
assign_mat(template, mat_snow)
template.hide_render = True
template.hide_viewport = True

random.seed(2026)
for i in range(800):
    new = template.copy()
    bpy.context.collection.objects.link(new)
    new.location = (
        random.uniform(-6, 6),
        random.uniform(-6, 6),
        random.uniform(0.05, 5.5),
    )
    s = random.uniform(0.4, 1.6)
    new.scale = (s, s, s)
    new.name = f"flake_{i:03d}"

# 環境光
setup_sky_world(turbidity=4.0, sun_dir=(-0.3, 0.5, 0.5), strength=0.4)

# Sun（寒色寄り）
bpy.ops.object.light_add(type='SUN', location=(0, 0, 8))
sun = bpy.context.active_object
sun.data.energy = 2.5
sun.data.color = (0.95, 0.95, 1.0)
sun.rotation_euler = (math.radians(60), math.radians(15), math.radians(-30))

# カメラ + DoF
bpy.ops.object.camera_add(location=(4.0, -5.0, 2.0),
                           rotation=(math.radians(80), 0, math.radians(38)))
cam = bpy.context.active_object
bpy.context.scene.camera = cam
cam.data.lens = 50.0
cam.data.dof.use_dof = True
cam.data.dof.focus_object = seat
cam.data.dof.aperture_fstop = 4.0

# レンダリング設定
scene = bpy.context.scene
scene.render.resolution_x = 900
scene.render.resolution_y = 600
scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.cycles.use_denoising = True

# 実行例:
# scene.render.filepath = r"C:\path\to\output.png"
# scene.render.image_settings.file_format = 'PNG'
# bpy.ops.render.render(write_still=True)
