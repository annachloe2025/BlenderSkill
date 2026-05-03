# snow_scatter.py — 雪片の散布

パーティクルシステムの代替として、**多数の小オブジェクトを Linked Duplicate で散布** する手法。物理シミュレーションは無いが、確実で速い。

## コード

```python
--8<-- "snippets/snow_scatter.py"
```

## なぜパーティクルじゃなくこっち？

| 観点 | パーティクル | 散布スクリプト |
|---|---|---|
| 物理 | 重力・速度を計算 | 静止画のみ |
| 動画 | フレームごとに更新 | 全フレーム同じ位置 |
| 学習コスト | やや高い | 低い |
| 確実性 | レンダリング設定次第で見えなくなることも | 必ず見える |
| メモリ | 効率的 | Linked Duplicate なら問題なし |

**学習中・静止画向け**なら散布スクリプトが圧倒的に楽。動画でリアルな降雪が必要なら本物のパーティクルシステムを使う。

## Linked Duplicate でメモリ節約

```python
new = template.copy()              # オブジェクトはコピー
# new.data = template.data.copy()  # ← これは付けない
bpy.context.collection.objects.link(new)
```

`obj.data` をコピーしないことで、すべての雪片が **同じメッシュデータを共有** する。1万個でも軽い。

## 応用パターン

| やりたいこと | 変更点 |
|---|---|
| 雨 | `radius=0.01`, scale=`(0.5, 0.5, 4)` で縦長、Z 範囲を広く |
| 葉っぱ | テンプレートを Plane + 葉のテクスチャ、ランダム回転 |
| 木の散布 | テンプレートを木モデル、Z=0 で地面に立つように |
| 星空 | Z=10〜30、emission マテリアルで自発光 |

## パーティクル版を試したいとき

```python
emitter = bpy.context.active_object  # 高い位置の Plane
bpy.ops.object.particle_system_add()
ps = emitter.particle_systems[0].settings
ps.count = 800
ps.frame_start, ps.frame_end = 1, 50
ps.lifetime = 80
ps.physics_type = 'NEWTON'
ps.render_type = 'OBJECT'
ps.instance_object = bpy.data.objects["Snowflake"]
```

レンダリングするフレームによっては粒が見えないことがあるので、`scene.frame_set(45)` などパーティクルが画面に充満するフレームを選ぶこと。
