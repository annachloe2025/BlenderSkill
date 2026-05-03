# snippets/ — 再利用可能なPythonコード集

Blender上で `mcp__blender__execute_blender_code` を通して実行する、
動作確認済みのPythonスニペットを保存します。

## 命名規則

- `clear_scene.py` — シーン全消し
- `add_primitive_<shape>.py` — プリミティブ追加
- `apply_material_<type>.py` — マテリアル適用
- `setup_<feature>.py` — 何かのセットアップ系
- など、用途が一目で分かる名前にする

## 各ファイルの先頭に書くこと

```python
# 用途: <このコードが何をするか>
# 動作確認: Blender X.Y / YYYY-MM-DD
# 依存: <他のスニペットや前提条件>
```
