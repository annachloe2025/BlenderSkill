# bmesh_basics.py

`bmesh` モジュールで **メッシュの頂点を直接操作** する基本パターン。Phase 2（モデリング編）の入口。

## コード

```python
--8<-- "snippets/bmesh_basics.py"
```

## bmesh の基本フロー

```python
import bmesh

# 1. 編集モードに入る
bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode='EDIT')

# 2. 編集中メッシュから bmesh を取得
bm = bmesh.from_edit_mesh(obj.data)

# 3. 頂点・辺・面を操作
for v in bm.verts:
    v.co.z += 1   # 全頂点を Z 方向に持ち上げる

# 4. 反映
bmesh.update_edit_mesh(obj.data)

# 5. オブジェクトモードに戻す
bpy.ops.object.mode_set(mode='OBJECT')
```

## 主要なAPI

| アクセス | 内容 |
|---|---|
| `bm.verts` | 頂点コレクション。`v.co` が `Vector(x, y, z)` |
| `bm.edges` | 辺コレクション。`e.verts` で2頂点を取得 |
| `bm.faces` | 面コレクション。`f.verts` / `f.normal` などにアクセス |
| `v.select` | 選択状態の取得・設定（True/False）|
| `v.co.x` / `.y` / `.z` | 頂点座標。直接代入で動かせる |

## 編集モード内のオペレータ

`bpy.ops.mesh.*` は編集モード内でのみ動作する:

- `bpy.ops.mesh.select_all(action='SELECT' / 'DESELECT')`
- `bpy.ops.mesh.subdivide(number_cuts=N)` — 細分化
- `bpy.ops.mesh.extrude_region_move(...)` — 押し出し
- `bpy.ops.mesh.bevel(...)` — 面取り

## 落とし穴

- **`bmesh.from_edit_mesh()` はオブジェクトモードでは使えない**。必ず先に `mode_set(mode='EDIT')`。
- 編集後の **`bmesh.update_edit_mesh(obj.data)` を忘れると変更が反映されない**。
- 大量の頂点をループで動かすときは、ビューポート更新を一時的に止めると速くなる（Phase 5 で扱う）。
