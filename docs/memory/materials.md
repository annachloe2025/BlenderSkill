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

## コードでノードグラフを組む

`mat.node_tree` を使えば、UI 上で組むのと同じことを Python でできる:

```python
nt = mat.node_tree

# 1. ノード生成
noise = nt.nodes.new('ShaderNodeTexNoise')
noise.location = (-600, 100)
noise.inputs['Scale'].default_value = 12.0

# 2. ソケット接続
nt.links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
```

ノードタイプ名は `ShaderNodeXXX`（先頭大文字）。代表的なもの:

| タイプ名 | 種類 |
|---|---|
| `ShaderNodeBsdfPrincipled` | Principled BSDF |
| `ShaderNodeTexImage` | Image Texture（PBR画像用）|
| `ShaderNodeTexNoise` | Noise Texture |
| `ShaderNodeTexWave` | Wave Texture |
| `ShaderNodeValToRGB` | Color Ramp |
| `ShaderNodeBump` | Bump（高さ→ノーマル）|
| `ShaderNodeTexCoord` | Texture Coordinate |
| `ShaderNodeMixRGB` | カラーミックス |

ソケット名は **UI ラベルそのまま、大小区別あり**: `'Base Color'`, `'Fac'`, `'Vector'`, `'Surface'` など。

## プロシージャル木目のレシピ

```
TexCoord(Object) → Noise(Scale=12) → Wave(Scale=4.8, Distortion=6) → ColorRamp(明茶↔濃茶) → BSDF.BaseColor
                                                                  └→ Bump(Strength=0.15) → BSDF.Normal
```

樹種を変えたいときは `base_color` / `dark_color` を調整:

| 樹種 | base_color | dark_color |
|---|---|---|
| パイン（明）| (0.75, 0.55, 0.35) | (0.40, 0.25, 0.10) |
| オーク | (0.55, 0.32, 0.15) | (0.20, 0.10, 0.04) |
| ウォールナット（濃）| (0.30, 0.18, 0.10) | (0.10, 0.05, 0.02) |
| チェリー（赤）| (0.60, 0.25, 0.18) | (0.30, 0.08, 0.05) |

## UV アンラップ

テクスチャ画像を貼るときは UV 座標が必要。Smart UV Project で自動展開:

```python
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=66, island_margin=0.02)
bpy.ops.object.mode_set(mode='OBJECT')
```

`angle_limit` の目安: 30=細かく分割（曲面）、66=汎用（家具）、89=ほぼ分割しない（板）。

プロシージャル質感は UV 不要でも動くが、後で画像テクスチャに切り替えやすくするため **モデリング段階で UV を貼っておく** のが推奨。

## Polyhaven 連携メモ

Polyhaven の MCP 連携は Blender MCP パネルの「Use assets from Poly Haven」チェックを ON にすると有効化される。一度 ON にすれば、`mcp__blender__search_polyhaven_assets` で検索 → `download_polyhaven_asset` でダウンロード → `set_texture` で適用、の流れで PBR テクスチャを使える。

OFF のときは **プロシージャル質感で代用** が現実的（むしろ学習効果は高い）。
