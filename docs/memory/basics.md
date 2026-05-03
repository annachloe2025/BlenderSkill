# 基本操作 — basics

Blenderの基礎レベルのノウハウ。プリミティブの追加、シーン管理、トランスフォームなど。

## シーンの全クリア

ライト・カメラ含めてシーンを完全に空にする最短手順:

```python
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
```

注意: デフォルトのコレクションは残る。コレクションも消したい場合は `bpy.data.collections.remove(...)` を別途使う。

## プリミティブ追加 API（よく使う5種）

| 形状 | API | 主要パラメータ |
|---|---|---|
| Cube | `bpy.ops.mesh.primitive_cube_add` | `size` |
| UV Sphere | `bpy.ops.mesh.primitive_uv_sphere_add` | `radius`, `segments`, `ring_count` |
| Cylinder | `bpy.ops.mesh.primitive_cylinder_add` | `radius`, `depth`, `vertices` |
| Cone | `bpy.ops.mesh.primitive_cone_add` | `radius1`, `radius2`, `depth` |
| Torus | `bpy.ops.mesh.primitive_torus_add` | `major_radius`, `minor_radius` |

追加直後のオブジェクトは `bpy.context.active_object` で取得できる。

```python
bpy.ops.mesh.primitive_cube_add(size=1)
obj = bpy.context.active_object
obj.name = "MyCube"
obj.location = (1, 2, 0)
```

## トランスフォーム（位置・回転・スケール）

- `obj.location = (x, y, z)` — ワールド座標で設定（タプル/Vector）
- `obj.rotation_euler = (rx, ry, rz)` — ラジアン
- `obj.scale = (sx, sy, sz)` — 各軸スケール

度数で書きたいときは `math.radians(45)` を使う。

## ライト＆カメラの最小セットアップ

```python
# Sun ライト
bpy.ops.object.light_add(type='SUN', location=(4, -4, 6))
bpy.context.active_object.data.energy = 3

# カメラ（シーンのアクティブカメラに指定）
bpy.ops.object.camera_add(location=(0, -8, 3), rotation=(1.2, 0, 0))
bpy.context.scene.camera = bpy.context.active_object
```

ライトの種類: `'POINT'`, `'SUN'`, `'SPOT'`, `'AREA'`

## 落とし穴メモ

- `bpy.ops.object.select_all(action='SELECT')` は **編集モードでは効かない**。Object Mode で実行する前提。
- プリミティブを追加すると、それまでの選択は解除されてその新オブジェクトのみが選択される。
- `bpy.context.active_object` は最後に追加/選択したオブジェクトを返す。複数まとめて操作するときは事前にリストに保存しておく。
