# add_primitives_row.py

5種類のプリミティブ（Cube / UV Sphere / Cylinder / Cone / Torus）を X 軸に等間隔で並べ、Sunライトとカメラもセットアップする。

## コード

```python
--8<-- "snippets/add_primitives_row.py"
```

## 使いどころ

- マテリアル・ライティングを試したいとき、被写体が複数あったほうが分かりやすい
- 学習の最初の確認用シーンとして

## 想定の見た目

`(i - 2) * 1.8` の式で `-3.6, -1.8, 0, 1.8, 3.6` の位置に並ぶ。カメラは `(0, -8, 3)` から見下ろし気味で全体を捉える。

## 関連スニペット

- [clear_scene.py](clear_scene.md) — 実行前にシーンを空にしたいときに併用
