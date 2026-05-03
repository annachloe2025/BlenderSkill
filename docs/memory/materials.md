# マテリアル — materials

Phase 3 マテリアル編のノウハウ蓄積。Principled BSDF を中心に、コードでマテリアルを構築する流儀。

## マテリアル作成の最小コード

```python
mat = bpy.data.materials.new(name="MyMat")
mat.use_nodes = True   # ← これを忘れるとノードベースで動かない
bsdf = mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.4, 0.22, 0.1, 1.0)
bsdf.inputs["Metallic"].default_value = 0.0
bsdf.inputs["Roughness"].default_value = 0.6
```

## オブジェクトに割り当てる

```python
if obj.data.materials:
    obj.data.materials[0] = mat
else:
    obj.data.materials.append(mat)
```

## Principled BSDF 主要入力

| 入力名 | 範囲 | 効果 |
|---|---|---|
| Base Color | RGBA | 基本色 |
| Metallic | 0〜1 | 金属度（1で鏡のような反射）|
| Roughness | 0〜1 | 粗さ（0=ピカピカ、1=つや消し）|
| IOR | 1.0〜2.5 | 屈折率（ガラスは1.45、水は1.33）|
| Transmission | 0〜1 | 透過（ガラス・水）|
| Emission | RGBA | 発光（自分から光を出す）|
| Subsurface | 0〜1 | 表面下散乱（肌・ワックス・葉）|

## レンダリングエンジン

| エンジン | 特徴 | 推奨用途 |
|---|---|---|
| Eevee Next | リアルタイム、軽い | プレビュー・学習中の確認 |
| Cycles | 物理ベース、光が綺麗 | 最終レンダリング・作品 |
| Workbench | シェーディング表示用 | デバッグ |

切り替え:

```python
scene.render.engine = 'CYCLES'   # or 'BLENDER_EEVEE_NEXT'
scene.cycles.samples = 64         # 多いほど綺麗、重い
scene.cycles.use_denoising = True
```

## マテリアル質感のレシピ

| 質感 | Metallic | Roughness | 補足 |
|---|---|---|---|
| 木 | 0.0 | 0.6〜0.8 | 茶系の色 |
| 金属（光沢）| 1.0 | 0.2〜0.4 | クロム・銀 |
| 金属（マット）| 1.0 | 0.6〜0.8 | アルミ・ヘアライン |
| プラスチック | 0.0 | 0.4〜0.5 | 鮮やかな色 |
| ゴム | 0.0 | 0.9 | 黒系、反射しない |
| ガラス | 0.0 | 0.0 | + Transmission=1 + IOR=1.45 |
| 水 | 0.0 | 0.0 | + Transmission=1 + IOR=1.33 |

## 落とし穴

- `Base Color` は **アルファ含む4要素タプル**: `(r, g, b, 1.0)`
- `mat.use_nodes = True` を忘れると BSDF にアクセスできない
- 同じマテリアルを複数オブジェクトに割り当ててもOK（リンク扱いになる）
- `obj.data.materials[0] = mat` は **データ（メッシュ）に紐づく** ので、Linked Duplicate に注意
