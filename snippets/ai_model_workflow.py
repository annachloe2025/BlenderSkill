# 用途: Hyper3D / Hunyuan3D / Sketchfab のワークフロー（有効化後に使うパターン）
# 動作確認: 2026-05-04 時点では未有効化、コードはMCPツール経由のため Blender スクリプトではない
#
# === 有効化手順（共通）===
# 1. Blender 3D Viewport の右サイドバー（N キー）から「BlenderMCP」パネルを開く
# 2. 該当のチェックボックスを ON:
#    - Use assets from Poly Haven
#    - Use Hyper3D Rodin 3D model generation
#    - Use Tencent Hunyuan 3D model generation
#    - Use assets from Sketchfab（要 API キー）
# 3. Disconnect → Reconnect で Claude との接続を再確立
#
# === 有効化後のワークフロー（MCP ツール）===
#
# # Hyper3D Rodin (テキスト → 3Dモデル)
# resp = mcp__blender__generate_hyper3d_model_via_text(
#     text_prompt="a simple wooden chair",  # 英語推奨
#     bbox_condition=[1.0, 1.0, 1.5],       # オプション: 縦横比
# )
# # 返り値の subscription_key / request_id を保管
# # 数十秒〜数分かかる
# status = mcp__blender__poll_rodin_job_status(subscription_key=...)
# # status が "Done" になったら
# mcp__blender__import_generated_asset(name="MyChair", task_uuid=...)
#
# # Polyhaven (HDRI / テクスチャ / モデル)
# results = mcp__blender__search_polyhaven_assets(asset_type="hdris", categories="indoor")
# mcp__blender__download_polyhaven_asset(asset_id="abandoned_factory_canteen_01",
#                                         asset_type="hdris", resolution="2k")
# # → 自動的にシーンに HDRI が適用される
#
# # Sketchfab (既存3Dモデル取り込み)
# models = mcp__blender__search_sketchfab_models(query="chair", count=10)
# mcp__blender__download_sketchfab_model(uid="...")

# このファイルは実行用スクリプトではなく、ワークフローのリファレンス
