# loopcut_bevel_box.py

Cube に **ループカット（subdivide）→ 全エッジにベベル** をかけて、滑らかな角丸の箱を作る基本パターン。

## コード

```python
--8<-- "snippets/loopcut_bevel_box.py"
```

## ループカットと subdivide の関係

Blender UIの「ループカット」は対話的な操作で、Pythonでは `bpy.ops.mesh.loopcut(...)` だが座標指定が面倒。**コードから安全に使うなら `bpy.ops.mesh.subdivide(number_cuts=N)`** が実用的。全エッジに均等にループが入る。

## ベベルの主要パラメータ

| パラメータ | 意味 |
|---|---|
| `offset` | ベベル幅（広いほど大きく丸くなる）|
| `segments` | 分割数（多いほど滑らか、重い）|
| `profile` | 形状（0.5=円弧、1.0=鋭角、0.0=凹）|
| `affect` | `'EDGES'` または `'VERTICES'` |

## なぜ subdivide → bevel の順？

ループカットなしで Cube に直接ベベルをかけると、エッジが少なすぎて思ったほど丸くならない。**先に細分化してエッジを増やしておく** と、ベベルが広く効いて柔らかい形になる。

## 落とし穴

- `bpy.ops.object.shade_smooth()` を **オブジェクトモードで** 呼ぶこと。編集モード中だとエラー。
- セグメント数が大きすぎるとビューポートが重くなる。学習中は3〜4で十分。
