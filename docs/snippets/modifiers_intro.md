# modifiers_intro.py

代表的なモディファイア3種（Subdivision Surface / Bevel / Mirror）をコードで適用する。

## コード

```python
--8<-- "snippets/modifiers_intro.py"
```

## モディファイア基本API

```python
m = obj.modifiers.new(name="任意の名前", type='TYPE')
m.プロパティ = 値
```

`type` には `'SUBSURF'`, `'BEVEL'`, `'MIRROR'`, `'ARRAY'`, `'SOLIDIFY'`, `'BOOLEAN'` など多数。

## 3種の使い分け

| 種類 | 用途 | 主要プロパティ |
|---|---|---|
| **Subdivision Surface** | カクカクのメッシュを滑らかな曲面に | `levels`（表示）, `render_levels`（レンダー）|
| **Bevel** | エッジを面取りして角を丸める | `width`, `segments` |
| **Mirror** | 半分作って対称コピー（左右対称キャラ作成の定番）| `use_axis[0/1/2]` |

## 適用 vs 非破壊

モディファイアは **非破壊**（実メッシュは変わらない）が、**「適用」すれば実メッシュ化** されて編集モードで触れるようになる:

```python
bpy.context.view_layer.objects.active = obj
bpy.ops.object.modifier_apply(modifier="モディファイア名")
```

## 注意点

- Subsurf は **`shade_smooth()` と併用するとさらに滑らか** に見える
- Bevel は元のメッシュにループが多すぎると重くなる。Subsurf と併用する場合は順序に注意（Bevel → Subsurf が一般的）
- Mirror は **オブジェクトの原点が対称軸** になる。原点をずらすとミラー結果も変わる
