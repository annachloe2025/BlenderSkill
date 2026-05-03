# 用途: ジオメトリノードでメッシュ表面にオブジェクトを散布
# 動作確認: 2026-05-04 / Blender MCP（Blender 4.0+ API）

import bpy
import math


def add_scatter_modifier(target_obj, instance_obj, density=50.0, seed=0):
    """target_obj のメッシュ表面に instance_obj を散布する Geometry Nodes モディファイア"""
    mod = target_obj.modifiers.new(name="Scatter", type='NODES')
    ng = bpy.data.node_groups.new(name="ScatterGroup", type='GeometryNodeTree')
    mod.node_group = ng

    # Blender 4.0+ の interface API
    ng.interface.new_socket(name="Geometry", in_out='INPUT',  socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # ノード生成
    nt = ng
    n_in   = nt.nodes.new('NodeGroupInput');                       n_in.location   = (-800, 0)
    n_out  = nt.nodes.new('NodeGroupOutput');                      n_out.location  = (800, 0)
    distrib = nt.nodes.new('GeometryNodeDistributePointsOnFaces'); distrib.location = (-400, 0)
    distrib.inputs['Density'].default_value = density
    iop    = nt.nodes.new('GeometryNodeInstanceOnPoints');         iop.location    = (-100, 0)
    objinfo = nt.nodes.new('GeometryNodeObjectInfo');              objinfo.location = (-400, -300)
    objinfo.inputs['Object'].default_value = instance_obj
    rand_rot   = nt.nodes.new('FunctionNodeRandomValue');          rand_rot.location  = (-400, -550)
    rand_rot.data_type = 'FLOAT_VECTOR'
    rand_rot.inputs['Min'].default_value = (0, 0, 0)
    rand_rot.inputs['Max'].default_value = (0, 0, math.radians(360))
    rand_scale = nt.nodes.new('FunctionNodeRandomValue');          rand_scale.location = (-400, -800)
    rand_scale.data_type = 'FLOAT'
    rand_scale.inputs[2].default_value = 0.5
    rand_scale.inputs[3].default_value = 1.5
    realize = nt.nodes.new('GeometryNodeRealizeInstances');        realize.location = (300, 0)
    join    = nt.nodes.new('GeometryNodeJoinGeometry');            join.location    = (550, 0)

    # リンク
    L = nt.links.new
    L(n_in.outputs[0],            distrib.inputs['Mesh'])
    L(distrib.outputs['Points'],  iop.inputs['Points'])
    L(objinfo.outputs['Geometry'], iop.inputs['Instance'])
    L(rand_rot.outputs[0],        iop.inputs['Rotation'])
    L(rand_scale.outputs[1],      iop.inputs['Scale'])
    L(iop.outputs['Instances'],   realize.inputs['Geometry'])
    L(n_in.outputs[0],            join.inputs['Geometry'])
    L(realize.outputs['Geometry'], join.inputs['Geometry'])
    L(join.outputs['Geometry'],   n_out.inputs[0])

    return mod


# 使用例:
# 1. 散布対象の Plane と、散布する小さなオブジェクトを用意（小オブジェクトは原点に置く）
# 2. add_scatter_modifier(target_plane, small_object, density=50.0)
# 3. 小オブジェクトは hide_render=True にしておく（テンプレート専用）
