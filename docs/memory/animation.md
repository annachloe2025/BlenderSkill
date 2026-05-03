# アニメーション・応用 — animation

Phase 5 のノウハウ。キーフレーム・パーティクル・ジオメトリノード・AI生成。

## キーフレームアニメーション

最も基本的なアニメ手法。属性を時間軸に沿って変化させる:

```python
obj.location = (0, 0, 1)
obj.keyframe_insert(data_path="location", frame=1)
obj.location = (0, 0, 5)
obj.keyframe_insert(data_path="location", frame=60)
```

`data_path` は文字列で、`"location"`, `"rotation_euler"`, `"scale"`, `"hide_render"` など。

## フレームレートと範囲

```python
scene.frame_start = 1
scene.frame_end = 60
scene.render.fps = 24            # 24=映画、30=テレビ、60=ゲーム
```

## 動画として書き出し

```python
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
bpy.ops.render.render(animation=True)
```

## パーティクル vs 散布スクリプト

| 観点 | パーティクル | 散布スクリプト |
|---|---|---|
| 物理 | あり | なし（静止のみ）|
| 動画 | フレームごと更新 | 全フレーム固定 |
| 確実性 | 設定次第で見えないことも | 必ず見える |
| 学習向き | やや複雑 | シンプルで確実 |

**学習中は散布スクリプト**、本格的な降雪・降雨アニメには本物のパーティクル。

散布の最小例:

```python
import random
template = bpy.data.objects["snow_template"]
for i in range(600):
    new = template.copy()                # data はリンク共有
    bpy.context.collection.objects.link(new)
    new.location = (random.uniform(-5,5), random.uniform(-5,5), random.uniform(0,5))
```

## ジオメトリノード

ノードベースのプロシージャルモデリング。**モディファイアとして** メッシュに付ける。

```python
mod = obj.modifiers.new(name="Scatter", type='NODES')
ng = bpy.data.node_groups.new(name="ScatterGroup", type='GeometryNodeTree')
mod.node_group = ng

# Blender 4.0+ の interface API
ng.interface.new_socket(name="Geometry", in_out='INPUT',  socket_type='NodeSocketGeometry')
ng.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

# ノードを追加・接続して散布や変形を構築
```

代表的なノード:

| ノード | 用途 |
|---|---|
| `GeometryNodeDistributePointsOnFaces` | メッシュ表面にランダム点 |
| `GeometryNodeInstanceOnPoints` | 各点にオブジェクトをインスタンス化 |
| `GeometryNodeObjectInfo` | 別オブジェクトのジオメトリを取り出す |
| `GeometryNodeRealizeInstances` | インスタンスを実メッシュ化 |
| `GeometryNodeJoinGeometry` | 複数のジオメトリを結合 |
| `FunctionNodeRandomValue` | ランダム値（位置・回転・スケール）|

## AI生成モデル（Hyper3D / Hunyuan3D / Sketchfab / Polyhaven）

BlenderMCP のオプション機能で、**チェックボックスを ON にすれば使える**。

| サービス | 用途 |
|---|---|
| Polyhaven | 無料 HDRI / PBR テクスチャ / モデル |
| Hyper3D Rodin | テキスト → 3Dモデル生成（AI）|
| Hunyuan3D | テンセント製の AI 3D 生成 |
| Sketchfab | ユーザー投稿の3Dモデル検索・取り込み |

ワークフロー（Hyper3D 例）:

1. `generate_hyper3d_model_via_text(text_prompt="...")` で生成リクエスト
2. `poll_rodin_job_status(...)` で完了待ち（数十秒〜数分）
3. `import_generated_asset(name="...")` でシーン取り込み

## 落とし穴

- キーフレームは **属性を変更してから** `keyframe_insert` する（現在値が記録される）
- ジオメトリノードの散布元は **原点に置いて hide_render** が基本（位置オフセットを避ける）
- Blender 4.0 で interface API が変わった（`interface.new_socket`）
- AI生成は時間がかかる。ポーリングしながら他の作業を進めるのが効率的
- 散布スクリプトは **Linked Duplicate**（`new.data` をコピーしない）でメモリ節約
