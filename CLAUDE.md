# BlenderSkill プロジェクト

## プロジェクトの目的

AIにBlenderのスキルを段階的に蓄積させ、様々な3Dモデル・シーンを自動で作れるようにする。
「ネットで情報収集 → Blenderで実行 → 振り返り → ノウハウ蓄積」のサイクルを繰り返すことで、再現可能な知識ベースを構築する。

## ワークフロー（毎セッションの基本手順）

1. **テーマ選定**: `docs/tasks.md` から次に取り組む課題を選ぶ
2. **情報収集**: ネット・ドキュメントから手順を調べる
3. **計画立案**: Pythonコード／操作手順を整理する
4. **実行**: Blender MCP（`mcp__blender__*`）でBlender上で実行
5. **検証**: ビューポートのスクリーンショットを取って結果を確認
6. **記録**:
   - 成功/失敗の経緯を `docs/log.md` に追記
   - 再利用可能なコードは `snippets/` に `.py` で保存し、`docs/snippets/` に解説ページ
   - カテゴリ別の知識は `docs/memory/` に蓄積
7. **タスク更新**: `docs/tasks.md` を更新（完了・新タスク追加）
8. **公開**: 必要なら `update.bat` で GitHub Pages にデプロイ

## ディレクトリ構成

```
BlenderSkill/
├── CLAUDE.md          # このファイル（AIへの指示。公開しない）
├── README.md          # GitHub リポジトリトップ
├── mkdocs.yml         # MkDocs設定
├── update.bat         # GitHub Pages デプロイ（ワンクリック）
├── requirements.txt
├── .gitignore
├── docs/              # 公開ドキュメント（このサイトの中身）
│   ├── index.md       # トップ
│   ├── log.md         # 学習ログ（時系列、最新が上）
│   ├── tasks.md       # ロードマップ
│   ├── memory/        # カテゴリ別ノウハウ
│   │   ├── index.md
│   │   └── basics.md  # 基本操作
│   ├── snippets/      # スニペット解説ページ（pymdownx.snippets で .py を埋め込み）
│   ├── images/        # スクリーンショット
│   └── stylesheets/   # 追加CSS
├── overrides/         # MkDocs テーマカスタマイズ
├── snippets/          # 実行用 .py（Blender MCP に流すコード本体）
└── outputs/           # .blendファイル・レンダリング結果
```

**注意**: AIが書く学習ログ・タスク・ノウハウはすべて `docs/` 配下が正本。ルートの `CLAUDE.md` だけは公開対象外（mkdocs から見られないので問題なし）。

## Blender MCP の使い方メモ

主要ツール:
- `mcp__blender__get_scene_info` — シーン状態の確認
- `mcp__blender__get_object_info` — オブジェクト詳細の取得
- `mcp__blender__execute_blender_code` — Pythonコード実行（メイン作業）
- `mcp__blender__get_viewport_screenshot` — 結果を目視確認
- `mcp__blender__search_polyhaven_assets` / `download_polyhaven_asset` — HDRI・テクスチャ・モデル取得
- `mcp__blender__search_sketchfab_models` / `download_sketchfab_model` — 既存モデル取得
- `mcp__blender__generate_hyper3d_model_via_text` / `via_images` — AI 3Dモデル生成

## 学習ロードマップ（大まかな順序）

1. **基礎編**: プリミティブ追加、移動・回転・スケール、削除・複製、モディファイア
2. **モデリング編**: 編集モード、ループカット、押し出し、ベベル、サブディビジョン
3. **マテリアル編**: ノードエディタ、PBRマテリアル、テクスチャ、UV
4. **ライティング・レンダリング編**: ライト種別、HDRI、Cycles vs Eevee、構図
5. **応用編**: リギング、アニメーション、パーティクル、ジオメトリノード、シミュレーション

## ルール

- **必ず記録する**: 試行錯誤も含めて `LOG.md` に残す。次回のセッションで同じ失敗を繰り返さないため。
- **小さく試す**: 一度に大量のコードを実行せず、段階的に確認する。
- **検証を怠らない**: 実行後はスクリーンショットで必ず目視確認。
- **再利用性を意識**: 「次も使えそう」なコードは `snippets/` に切り出す。

## バイナリ・ローカル専用フォルダ

- `blender/` 配下に **FBX / レンダー出力PNG / .blend / EXR 等のバイナリは全部入れる**。`.gitignore` で丸ごと除外済み（GitHubに上がらない）。
- 公開対象（git追跡）は `docs/`, `snippets/`, `overrides/`, `mkdocs.yml`, `requirements.txt` 等のテキスト・コード資産だけ。
- 構造:
  - `blender/assets/mixamo/*.fbx` — Mixamoから手動DLした素体・ポーズFBX
  - `blender/outputs/character/poses/<pose_name>/*.png` — レンダー結果
  - `blender/outputs/*.blend` — 保存した.blendシーン
- スクリプトのハードコードパスも `blender/` 配下を参照する。例: `character_setup.py` の `CHARACTER_FBX`, `character_render_poses.py` の `POSE_FBX_GLOB` / `OUTPUT_ROOT`。

## ⚠️ Cowork の bash マウントキャッシュ問題（重要）

**症状**: Cowork の bash サンドボックス（`mcp__workspace__bash`）から Windows 側のマウントフォルダを `ls` / `find` / `stat` / `cat` / `wc -l` 等で見ると、**最大1時間古いキャッシュ**を返してくる。エラーは出ず、それっぽい結果を返すので **silent corruption** になる。

**原因**: Cowork は Windows フォルダを rclone FUSE 経由でサンドボックスに見せており、その mount オプションが `cache_duration_s = 3600`（1時間キャッシュ）で固定されている。Windows側で（Edit/Write ツールやユーザの手動操作で）ファイルを変更しても、bash側からは1時間経過まで旧状態が見える。

**今日の実例**: ユーザが Explorer で `assets/mixamo/` と `outputs/character/poses/` を `blender/` 配下に移動 → bashの `find` は移動先を空フォルダと判定（移動が見えてない）→ Claude が「ファイルが消えた！」と誤解釈、ユーザは「普通にあるよ」と反論、というすれ違いが発生。

**回避策**:
- ファイル一覧・存在確認は **Glob / Read ツールを使う**（これらはホスト側パスを直接読むのでキャッシュ無関係）
- bash は **コマンド実行（mv, mkdir 等の書き込み系）と、サンドボックス内ファイル(`/tmp` 等)の処理にだけ使う**
- どうしても bash で確認が要るときは「Glob で見た通りなので bash 出力は古いだけ」とユーザに伝えて Glob 結果を信頼する

**関連 issue**: anthropics/claude-code #45433, #41710, #55877, #40191, #42520, #28015 等。
