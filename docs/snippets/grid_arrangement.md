# grid_arrangement.py

ループで NxN のグリッド配置を行う基本パターン。**「中心を原点に置きつつ等間隔配置」** の典型的な計算式。

## コード

```python
--8<-- "snippets/grid_arrangement.py"
```

## ポイント

- 中心を原点に揃える計算式: `(i - (N - 1) / 2) * spacing`
    - `N=5`, `spacing=1.5` → `-3.0, -1.5, 0, 1.5, 3.0` の5点
- このパターンは **木を森に並べる、椅子を会議室に並べる、街の建物を並べる** などあらゆる場面で再利用できる
- 中心からの距離 `sqrt(x²+y²)` を使うと **波・円形・グラデーション** などの装飾が一発でできる

## バリエーション

千鳥配置（六角形グリッド風）にしたいときは、行ごとに X をずらす:

```python
for iy in range(N):
    offset_x = 0.75 if iy % 2 else 0
    for ix in range(N):
        x = (ix - (N - 1) / 2) * spacing + offset_x
        ...
```
