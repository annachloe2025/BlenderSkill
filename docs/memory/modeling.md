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

## Extrude（押し出し）

`bpy.ops.mesh.extrude_region_move` は **編集モードで現在の選択領域を押し出して移動** するオペレータ。引数は2層になっていて、移動量はネストされたキーに渡す:

```python
bpy.ops.mesh.extrude_region_move(
    TRANSFORM_OT_translate={"value": (dx, dy, dz)}
)
```

**「上に押し出す → 奥に押し出す」を for ループで繰り返すだけで階段ができる**。`STEP_RISE` / `STEP_RUN` のように寸法を定数化しておくと改造しやすい。

応用:
- 螺旋階段: 各ループで Z 回転を入れる
- 段々畑: 「広い面 → 狭い面」を交互に押し出し

## ループカット + ベベル

ループカットUI (`bpy.ops.mesh.loopcut`) は対話的で扱いにくいので、**Pythonからは `bpy.ops.mesh.subdivide(number_cuts=N)`** が実用的。全エッジに均等にループが入る。

```python
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.subdivide(number_cuts=1)
bpy.ops.mesh.bevel(offset=0.15, segments=4, profile=0.5, affect='EDGES')
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.shade_smooth()
```

**先に細分化してから bevel** をかけると、エッジが多くなった分だけベベルが広く効いて柔らかい形になる。素の Cube に直接ベベルだとカクカク感が残りやすい。

`bevel` の主要パラメータ:

| 引数 | 意味 |
|---|---|
| `offset` | 幅 |
| `segments` | 分割数（多いほど滑らか）|
| `profile` | 0.5=円弧、1.0=鋭角、0.0=凹 |
| `affect` | `'EDGES'` or `'VERTICES'` |

## パーツ組み立てモデリングのコツ

家具のような複合モデルを作るときの実践パターン:

1. **寸法をすべて定数化**（`SEAT_W = 1.0` など）。後から微調整しやすい。
2. **繰り返しパターンは関数化**（角丸ボックスを2個作るなら `add_rounded_box()` ヘルパーに）。
3. **対称配置は符号反転 for ループ**: `for sx, sy in [(1,1), (1,-1), (-1,1), (-1,-1)]` で4隅。
4. **床 + ライト + カメラ** までスクリプトに含めると、再実行で完成画像まで一発再現できる。
