# ライティング・レンダリング — lighting

Phase 4 で蓄積していく、光と画作りのノウハウ。

## ライト4種の使い分け

| 種類 | 性質 | 主な用途 |
|---|---|---|
| **Point** | 全方向放射、距離減衰 | 電球・ろうそく |
| **Sun** | 平行光線、距離無関係 | 屋外の太陽 |
| **Spot** | 円錐状の光、`spot_size`/`spot_blend` で形を制御 | 演出スポット |
| **Area** | 面光源、柔らかい影 | スタジオ撮影風 |

ライトの追加:

```python
bpy.ops.object.light_add(type='SUN', location=(...))
light = bpy.context.active_object
light.data.energy = 4
light.data.angle = math.radians(2)   # Sun の場合：太陽の見かけ角度
```

## 環境光（World シェーダー）

World は**シーン全体の背景＝広い面光源**。`Sky Texture` か `Background` 単色か HDRI 画像を入力にする。

```python
world = bpy.context.scene.world
world.use_nodes = True
nt = world.node_tree
sky = nt.nodes.new('ShaderNodeTexSky')
sky.sky_type = 'HOSEK_WILKIE'   # or 'NISHITA' (2.90+)
sky.turbidity = 2.5
sky.sun_direction = (0.3, -0.7, 0.6)
```

`sky_type`:

- `NISHITA`: 物理ベース、最も綺麗（Blender 2.90+）
- `HOSEK_WILKIE`: 高品質定番
- `PREETHAM`: 古典的

`turbidity`: 1=澄んだ青空、10=曇り。
`sun_direction`: 太陽方向ベクトル。Sun ライトの向きと揃えると自然。

## レンダリングエンジン

| エンジン | 計算方式 | 速度 | 用途 |
|---|---|---|---|
| **Cycles** | パストレース | 遅・綺麗 | 最終レンダー、作品 |
| **Eevee Next** | ラスタライズ（4.2+）| 速 | プレビュー、アニメ |
| **Eevee（旧）** | ラスタライズ | 速 | プレビュー（旧Blender）|

切替:

```python
scene.render.engine = 'CYCLES'
scene.cycles.samples = 96
scene.cycles.use_denoising = True
```

利用可能エンジンは実行時に判定可能:

```python
available = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
```

## カメラ設定

| 属性 | 意味 |
|---|---|
| `cam.data.lens` | 焦点距離（mm）。50=標準、85=ポートレート向き |
| `cam.data.dof.use_dof` | 被写界深度を有効化 |
| `cam.data.dof.aperture_fstop` | 絞り（小さい=ボケ強）|
| `cam.data.dof.focus_distance` | フォーカス距離（m）|
| `cam.data.dof.focus_object` | フォーカス対象オブジェクト（追従）|

ポートレート風DoFのレシピ: `lens=85`, `aperture_fstop=1.4〜2.0`, `focus_object=被写体`。

## 構図のコツ

- **三分割構図**: 被写体を縦横1/3の線・交点に
- **奥行きを作る**: 手前・中央・奥にオブジェクトを並べる（DoFが活きる）
- **アングル**: カメラを少し低くすると主役が大きく映える

## 落とし穴

- `cam.data.dof.aperture_fstop` の値を **小さく** するとボケが **強く** なる（f値の常識通り）
- `Sky Texture` で `NISHITA` が無い古い Blender では `HOSEK_WILKIE` を使う
- Cycles のサンプル数が低すぎる（< 32）とノイズだらけ。`use_denoising = True` を必ず ON
- Eevee は SSR（Screen Space Reflection）の制限で **画面外のものは反射しない**
