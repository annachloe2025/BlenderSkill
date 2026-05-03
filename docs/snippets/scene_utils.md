# scene_utils.py

毎回のセッションでコピペして使う、シーン管理ユーティリティ関数群。

## コード

```python
--8<-- "snippets/scene_utils.py"
```

## 使い分け

| 関数 | 用途 |
|---|---|
| `clear_all()` | デフォルトの Cube/Light/Camera ごと完全リセットしたい |
| `clear_meshes_only()` | ライティング・カメラはそのままで、メッシュだけ作り直したい |
| `setup_basic_scene()` | 空シーンに Sun + Camera だけ生やしたい |
| `reset_scene()` | 学習セッションの定型スタート（全消し + 基本セット）|

## 推奨パターン

新しい実験を始めるときの定型:

```python
from snippets.scene_utils import reset_scene  # （Blender MCPで使うときは関数を直接コピペでOK）

reset_scene()                         # クリーンな初期状態
bpy.ops.mesh.primitive_cube_add()     # 試したいオブジェクトを追加
# ...以降に試行コードを書く
```

ライティングを保持したまま被写体だけ切り替えたいなら `clear_meshes_only()` を使う。
