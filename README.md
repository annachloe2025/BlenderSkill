# BlenderSkill

AIに **Blenderのスキルを段階的に蓄積させる** ための個人学習プロジェクト。
Claude（Cowork）+ Blender MCP を使って、ネットで情報収集 → Blenderで実行 → 振り返り → ノウハウ蓄積、のサイクルを回す。

📖 **ドキュメントサイト**: <https://annachloe2025.github.io/BlenderSkill/>

## ディレクトリ構成

```
BlenderSkill/
├── CLAUDE.md          # AIへの指示（プロジェクトガイド）
├── mkdocs.yml         # サイト設定
├── docs/              # 公開ドキュメント
│   ├── index.md       # トップ
│   ├── log.md         # 学習ログ
│   ├── tasks.md       # ロードマップ
│   ├── memory/        # カテゴリ別ノウハウ
│   └── snippets/      # スニペット解説ページ
├── snippets/          # 実行用 .py
├── outputs/           # .blend / レンダリング結果
└── update.bat         # GitHub Pages へワンクリックデプロイ
```

## デプロイ

`update.bat` をダブルクリックすると、

1. MkDocs / Material / pymdown-extensions を pip でインストール（必要なら）
2. `git add . && git commit && git push`
3. `mkdocs gh-deploy --force` で GitHub Pages に反映

の流れが一気に走る。

## ライセンス

個人学習用。スニペットは自由に流用してOK。
