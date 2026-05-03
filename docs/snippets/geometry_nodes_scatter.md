# geometry_nodes_scatter.py — ジオメトリノード散布

Blender の **Geometry Nodes** モディファイアでメッシュ表面にオブジェクトを散布する。Phase 5 の核心、**プロシージャルモデリングの王道**。

## コード

```python
--8<-- "snippets/geometry_nodes_scatter.py"
```

## ノードグラフの全体像

```
GroupInput ─→ DistributePointsOnFaces ─→ InstanceOnPoints ─→ RealizeInstances ─┐
                                                ↑                                ↓
                                          ObjectInfo               JoinGeometry → GroupOutput
                                                                       ↑
                                          GroupInput ─────────────────┘
```

| ノード | 役割 |
|---|---|
| `DistributePointsOnFaces` | メッシュ表面にランダムな点を発生（密度指定）|
| `ObjectInfo` | 散布する別オブジェクトのジオメトリを取り出す |
| `InstanceOnPoints` | 各点にオブジェクトをインスタンス化 |
| `RandomValue` | 各インスタンスごとにランダム値（回転・スケール）|
| `RealizeInstances` | インスタンスを実メッシュに変換（後段で結合するため）|
| `JoinGeometry` | 元のメッシュと散布結果を統合 |

## 散布元オブジェクトの位置に注意

`ObjectInfo` で取り出すオブジェクトは、**ワールド座標で配置されたまま** インスタンスとして使われる。原点にない場合は全体がずれる。

→ **散布元は原点（0,0,0）に置いて `hide_render = True / hide_viewport = True` で隠す** のが基本パターン。

## Blender 4.0+ の interface API

ノードグループの入出力定義は Blender 4.0 で大きく変わった:

```python
# 4.0+
ng.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')

# 3.x
ng.inputs.new('NodeSocketGeometry', "Geometry")
```

実行時にバージョン判定するならどちらでも対応可能。

## 応用例

| やりたいこと | アイデア |
|---|---|
| 草原 | 草のメッシュを地面に大量散布 |
| 石ころの河原 | 大小の石を河の Plane に散布 |
| 森 | 木のメッシュを地形に density 0.5 程度で散布 |
| 髪の毛 | Curve に散布して曲げる |

## 落とし穴

- インスタンスのままだとマテリアルが効かないことがある → `RealizeInstances` で実メッシュ化
- `JoinGeometry` の入力ソケットは **複数本接続できる**（元メッシュ + 散布結果の両方を繋ぐ）
- 密度を上げすぎるとビューポートが固まる。学習中は density=10〜50 で十分
