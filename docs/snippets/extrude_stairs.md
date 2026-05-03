# extrude_stairs.py

`bpy.ops.mesh.extrude_region_move` を使って、Plane から階段状の形を作る。

## コード

```python
--8<-- "snippets/extrude_stairs.py"
```

## 押し出しオペレータの基本

`bpy.ops.mesh.extrude_region_move()` は **編集モードで現在選択されている領域を押し出して、続けて移動** するオペレータ。引数は2層構造になっていて、移動量はネストされた `TRANSFORM_OT_translate` に渡す:

```python
bpy.ops.mesh.extrude_region_move(
    TRANSFORM_OT_translate={"value": (dx, dy, dz)}
)
```

## ループで階段を作る発想

「上に押し出す → 奥に押し出す」を1セットにして繰り返すだけで階段ができる。一段ずつのパラメータを `STEP_RISE`, `STEP_RUN` として定数化しておくと、後から段数や寸法をいじりやすい。

## 応用パターン

- **螺旋階段**: 各ループで Z 回転を入れれば螺旋構造に（後の Phase 2 課題で扱える）
- **手すり**: 押し出し → 細い柱を `Array` モディファイアで複製
- **段差のある地形**: 同じ要領で「広い面 → 狭い面 → 広い面」を作れば段々畑風

## 落とし穴

- `extrude_region_move` は **「選択中の領域」** に対して効く。最初に `bpy.ops.mesh.select_all(action='SELECT')` で全選択しておくのが安全。
- 押し出した直後はその新しい面が選択状態になる。連続押し出しは選択を解除しないこと。
