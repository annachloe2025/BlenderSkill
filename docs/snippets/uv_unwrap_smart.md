# uv_unwrap_smart.py — Smart UV Project でUV展開

テクスチャを正しく貼るには、メッシュを **UV座標** に展開する必要がある。Smart UV Project は角度ベースで自動的にいい感じに展開してくれる手軽な方法。

## コード

```python
--8<-- "snippets/uv_unwrap_smart.py"
```

## UV展開とは何か

3Dメッシュは XYZ 座標系の頂点で構成されているが、テクスチャ画像は2Dの UV 座標系に貼られる。**UV展開とは「3Dメッシュを2D平面に切り開く」操作**。

紙でできた箱を、ハサミで切って広げて1枚の紙にするイメージ。

## アンラップの種類

| 方法 | 用途 |
|---|---|
| **Smart UV Project** | 角度自動で切る、汎用的、家具・小物にちょうどいい |
| **Cube Projection** | 立方体6面に投影、箱状の物に最適 |
| **Cylinder Projection** | 円柱状の物に |
| **Sphere Projection** | 球体に |
| **Unwrap（手動シーム）** | 細かい制御が必要な複雑なモデル（キャラなど）|

## Smart UV Project のパラメータ

```python
bpy.ops.uv.smart_project(
    angle_limit=66,       # 度数。低いほど細かく分割される
    island_margin=0.02,   # UVアイランド間の余白
)
```

`angle_limit` の目安:
- **30〜45**: 滑らかな曲面で細かく分割（オーガニックモデル）
- **66**: 汎用的（家具・小物）
- **89**: ほとんど分割しない（板状の物）

## プロシージャルマテリアルでも UV を貼っておく理由

UV 展開しなくてもプロシージャル質感は **動作する**（TexCoord ノードの `Object` 出力を使えば3D空間ベースで動く）。ただし、UV を貼っておくと:

- 後でテクスチャ画像に切り替えるのが楽
- スケールが安定する（オブジェクトのスケールに依存しない）
- テクスチャペイントで直接塗れる

なので **UV展開はモデリング段階で済ませておく** のが Phase 3 以降の鉄則。

## 落とし穴

- `bpy.ops.uv.smart_project` は **編集モード + 全選択** が前提。先に `mode_set(mode='EDIT')` + `select_all`。
- スケールが極端なオブジェクト（1m と 100m の混在など）は UV のテクスチャ密度がバラつく。**先に `bpy.ops.object.transform_apply(scale=True)` でスケールを 1.0 に焼き付け** ておくと安定する。
