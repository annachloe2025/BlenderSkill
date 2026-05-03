# スニペット集

Blender MCP の `execute_blender_code` で実行できる、動作確認済みの再利用可能スニペット。

実体は `snippets/` フォルダの `.py` ファイル。各ページではコード本体と使い方を紹介する。

## 一覧

| 名前 | 用途 | リンク |
|---|---|---|
| `clear_scene.py` | シーンの全オブジェクトを削除 | [詳細](clear_scene.md) |
| `add_primitives_row.py` | 5種プリミティブを X 軸に等間隔配置 | [詳細](add_primitives_row.md) |

## 使い方

各 `.py` の中身をそのまま `mcp__blender__execute_blender_code` に渡せば動く。
セッションをまたいで再利用するときは、まずシーン全消し → 用途別スニペットを実行、の流れが安全。
