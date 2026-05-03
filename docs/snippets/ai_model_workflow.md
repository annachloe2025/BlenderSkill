# ai_model_workflow.py — AI生成・外部アセット連携の手順

Hyper3D Rodin / Hunyuan3D / Polyhaven / Sketchfab を使って、AI生成モデルや既存アセットを Blender に取り込むワークフロー。

!!! warning "現在無効化中"
    2026-05-04 時点では BlenderMCP パネルでこれらが OFF。**有効化はユーザーがチェック ON するだけ**。

## 有効化手順（共通）

1. Blender の 3D Viewport で右サイドバー（**N キー** で表示）を開く
2. **BlenderMCP** パネルの該当チェックボックスを ON:
    - Use assets from Poly Haven
    - Use Hyper3D Rodin 3D model generation
    - Use Tencent Hunyuan 3D model generation
    - Use assets from Sketchfab（要 API キー）
3. **Disconnect → Reconnect** ボタンで Claude との接続を再確立

## Hyper3D Rodin（テキスト → 3D）

英語のテキストプロンプトから3Dモデルを生成。生成は数十秒〜数分。

```python
# 1. 生成リクエスト
resp = mcp__blender__generate_hyper3d_model_via_text(
    text_prompt="a simple wooden chair with metal legs",
    bbox_condition=[1.0, 1.0, 1.5],   # 縦横比 [W, D, H]
)
# resp に subscription_key (MAIN_SITE) または request_id (FAL_AI) が入る

# 2. 完了をポーリング
status = mcp__blender__poll_rodin_job_status(subscription_key=...)
# status が "Done" / "COMPLETED" になるまで待つ

# 3. シーンに取り込み
mcp__blender__import_generated_asset(name="AIChair", task_uuid=...)
```

## Hunyuan3D（テキスト → 3D / 画像 → 3D）

テンセントの Hunyuan3D。テキストまたは画像から生成可能。

```python
mcp__blender__generate_hunyuan3d_model(text_prompt="a fantasy wooden chest")
# job_id で進捗確認 → import_generated_asset_hunyuan で取り込み
```

## Polyhaven（HDRI / テクスチャ / モデル）

無料の高品質アセットライブラリ。

```python
# 検索
results = mcp__blender__search_polyhaven_assets(asset_type="hdris", categories="indoor")

# ダウンロード（自動でシーンに適用）
mcp__blender__download_polyhaven_asset(
    asset_id="abandoned_factory_canteen_01",
    asset_type="hdris",
    resolution="2k",
)
```

`asset_type`: `"hdris"`, `"textures"`, `"models"`

## Sketchfab（既存3Dモデル）

ユーザーがアップロードした3Dモデルを検索・ダウンロード。**APIキーが必要**。

```python
models = mcp__blender__search_sketchfab_models(query="medieval sword", count=10)
mcp__blender__download_sketchfab_model(uid="...")
```

## ワークフローの組み合わせ

これらを組み合わせると、AIで生成 → Polyhaven HDRI で照らす → Sketchfab の小道具を追加、といった**コード一本で完結する作品作り**が可能になる。

## 落とし穴

- 生成系（Hyper3D / Hunyuan3D）は **時間がかかる**。`poll_*_job_status` でループ待機する
- 生成モデルは **正規化されたサイズ** で来るので、シーンに合わせて再スケールが必要
- Polyhaven の HDRI は容量が大きい。`resolution="1k"` か `"2k"` から始める（4k はテスト後）
- Sketchfab はモデルによって **ライセンスが異なる**。商用利用前は確認必須
