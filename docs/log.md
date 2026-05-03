# 学習ログ

各セッションでの試行錯誤を時系列で記録します。
新しいエントリは **上に追記** してください（最新が一番上）。

---

## テンプレート（コピーして使う）

### YYYY-MM-DD: タイトル

**目標**: 何を作る／学ぼうとしたか

**調べた情報**:
- 参照したサイト・ドキュメント

**実行した手順**:
1. ...
2. ...

**結果**: 成功 / 部分的成功 / 失敗

**学んだこと**:
- ...

**つまずいた点**:
- ...

**再利用可能な成果物**:
- snippets/xxx.py
- memory/xxx.md に追記

---

## 2026-05-04: Phase 1 開始 — 接続テスト & 5プリミティブ配置

**目標**: Blender MCP接続確認 → プリミティブを5種類並べて配置

**実行した手順**:
1. `get_scene_info` で接続確認（デフォルトシーン: Cube/Light/Camera）
2. `get_viewport_screenshot` でビューポート目視
3. シーンクリア → cube/sphere/cylinder/cone/torus を X 軸に1.8間隔で配置
4. Sunライト・カメラを追加してアクティブカメラに設定
5. スクリーンショットで結果確認

**結果**: 成功。5プリミティブが綺麗に並び、ライト・カメラも正常に配置された。

**学んだこと**:
- `bpy.ops.object.select_all(action='SELECT')` + `delete()` でシーン全消しが最短
- プリミティブ追加直後の `bpy.context.active_object` ですぐ参照できる
- `bpy.context.scene.camera = obj` でアクティブカメラを切り替えられる

**つまずいた点**: 特になし

**再利用可能な成果物**:
- `snippets/clear_scene.py` — シーン全消し
- `snippets/add_primitives_row.py` — 5プリミティブ配置
- `memory/basics.md` — 基本操作のリファレンス追加

---

## 2026-05-04: プロジェクト初期化

**目標**: BlenderSkill プロジェクトのフォルダ構成を作成

**実行した手順**:
1. `C:\Users\hoeho\Documents\Claude\BlenderSkill` フォルダを作業ディレクトリとして接続
2. `CLAUDE.md`、`LOG.md`、`TASKS.md` を作成
3. `memory/`、`snippets/`、`outputs/` ディレクトリを作成

**結果**: 成功

**次のアクション**: `TASKS.md` から最初のタスクを選んで開始する
