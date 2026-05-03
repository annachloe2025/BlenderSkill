# material_basics.py — Principled BSDF の基本

色・メタリック・粗さの3つのパラメータをいじるだけで、**木・金属・プラスチック・布** など多彩な質感が出せる。Phase 3 マテリアル編の入口。

## コード

```python
--8<-- "snippets/material_basics.py"
```

## Principled BSDF の主要パラメータ

| 入力名 | 範囲 | 効果 |
|---|---|---|
| `Base Color` | RGBA | 物体の基本色 |
| `Metallic` | 0〜1 | 0=非金属、1=金属（鏡のように映り込む）|
| `Roughness` | 0〜1 | 0=ピカピカ、1=つや消し |
| `IOR` | 1.0〜2.5 | 屈折率（透明物・水・ガラスで使う）|
| `Transmission` | 0〜1 | 透過率（ガラスや水を作るときに上げる）|

## 質感のレシピ

| 質感 | Metallic | Roughness | コメント |
|---|---|---|---|
| 木 | 0.0 | 0.6〜0.8 | 色は茶系、粗さ高め |
| 金属（光沢） | 1.0 | 0.2〜0.4 | 銀・クロム |
| 金属（マット） | 1.0 | 0.6〜0.8 | アルミ・サンドブラスト鋼 |
| プラスチック | 0.0 | 0.4〜0.5 | 色を鮮やかに |
| ゴム | 0.0 | 0.9 | 黒系・ほぼ反射しない |
| ガラス | 0.0 | 0.0 | + Transmission=1.0 |

## マテリアル割り当てのパターン

```python
# 既存スロットを上書き、なければ追加
def assign_material(obj, mat):
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
```

複数スロットを使ってオブジェクトの面ごとに別マテリアルを当てることもできるが、Phase 3 入口では「1オブジェクト = 1マテリアル」で十分。

## レンダリングエンジンの選択

- **Eevee（Eevee Next）**: リアルタイム・高速。学習中の確認向き
- **Cycles**: 物理ベースで光が綺麗。最終レンダリングや作品向き
  - `scene.render.engine = 'CYCLES'`
  - `scene.cycles.samples = 64〜256`
  - `scene.cycles.use_denoising = True`（ノイズ除去）

## 落とし穴

- マテリアルを作ったら **`mat.use_nodes = True`** を必ず立てる。これがないと Principled BSDF が使えない
- `bsdf.inputs["Base Color"].default_value` は **RGBA の4要素タプル**。`(r, g, b, 1.0)` のようにアルファを忘れない
