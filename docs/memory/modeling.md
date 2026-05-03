# モデリング — modeling

編集モード（Edit Mode）でメッシュ自体を作り変えるノウハウ。Phase 2 で蓄積していく。

## bmesh モジュールの基本

`bmesh` は編集モードでメッシュ構造に直接アクセスできるモジュール。頂点・辺・面を Python で自由に操作できる。

```python
import bmesh

bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode='EDIT')

bm = bmesh.from_edit_mesh(obj.data)
for v in bm.verts:
    v.co.z += 1
bmesh.update_edit_mesh(obj.data)

bpy.ops.object.mode_set(mode='OBJECT')
```

ポイントは:

- `from_edit_mesh()` で取得 → 操作 → `update_edit_mesh()` で反映、の3ステップ
- `v.co` は `mathutils.Vector` で、`.x` / `.y` / `.z` 直接代入できる
- ループ中に頂点を追加・削除するなら、`bm.verts.ensure_lookup_table()` を間に挟む

## 編集モード内オペレータ

`bpy.ops.mesh.*` は編集モード内でのみ動作:

| オペレータ | 用途 |
|---|---|
| `mesh.select_all(action='SELECT' or 'DESELECT' or 'INVERT')` | 全選択/解除/反転 |
| `mesh.subdivide(number_cuts=N)` | 選択面を細分化 |
| `mesh.extrude_region_move(...)` | 押し出し（後の Phase 2 課題で扱う）|
| `mesh.bevel(offset=..., segments=...)` | 面取り |
| `mesh.merge(type='CENTER')` | 選択頂点をマージ |

## 「条件で選んで動かす」パターン

bmesh の真価は **「特定の条件にマッチする頂点だけ動かせる」** こと:

```python
# 上面（Z > 0）の頂点だけ縮める → 台形化
for v in bm.verts:
    if v.co.z > 0:
        v.co.x *= 0.5
        v.co.y *= 0.5
```

```python
# 中心からの距離で高さを変える → 波模様
for v in bm.verts:
    dist = math.sqrt(v.co.x**2 + v.co.y**2)
    v.co.z = math.sin(dist * 3) * 0.3
```

## 落とし穴メモ

- bmesh は **編集モードでしか取得できない**。先に `mode_set(mode='EDIT')`。
- `update_edit_mesh()` を忘れると見た目に反映されない。
- 編集モードのまま処理を終えると、次の `select_all` などが効かなくなる。**最後は必ず `mode_set(mode='OBJECT')` に戻す** のが安全。
- `subdivide` や `extrude_region_move` は **「現在の選択状態」** に対して動く。動かす前に `bpy.ops.mesh.select_all(action='SELECT')` などで意図した選択状態にしておくこと。
