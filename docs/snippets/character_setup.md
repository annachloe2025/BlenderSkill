# character_setup.py

Mixamo の **With Skin** FBX（Jennifer 等）を読み込み、ControlNet 入力画像の量産パイプライン向けにシーンを正規化する初期セットアップ。`character_render_poses.py` の前段として使う。

## コード

```python
--8<-- "snippets/character_setup.py"
```

## 実行後の状態

- シーンは空（既存オブジェクト全削除）
- `Character` という名のアーマチュア + 紐付くメッシュ群（顔・体・髪・目・睫毛）が原点に立っている
- ポートレート向け Camera (`PortraitCam`, 50mm, 縦長 768×1024)
- ライト2灯: `KeySun` (Sun) + `FillArea` (Area)
- ワールド背景はニュートラルグレー
- レンダーエンジン = Eevee（バッチ用に速度優先）
- View Layer の Depth / Normal パスが有効化済み

## 使いどころ

- AI 画像生成用に「同じキャラを同じカメラで撮る」ベースを作るとき
- ポーズだけ差し替えて量産するパイプラインのスタート地点

## 注意点

- **Mixamo 100倍スケール**: FBXは cm 単位で来るので 0.01 を掛けてApply。`arm.dimensions.z > 50` で判定して自動補正
- **インポート時のアクション**: Mixamo はT-Pose素体FBXにも `Armature|mixamo.com|Layer0` を勝手に紐付ける。これを外さないと後段の `copy_pose` が render 直前に T-pose へ巻き戻る。本スクリプトでは `animation_data.action = None` で外している
- **`if __name__ == "__main__":` ガード**: Blender MCP の `execute_blender_code` から `exec(open(...).read())` だと発火しないことがある。`importlib.util.spec_from_file_location` で読み込んで `mod.main()` を直叩きするのが確実

## カスタマイズポイント

ファイル冒頭の定数を編集:

```python
CHARACTER_FBX = r"...\Jennifer.fbx"   # 素体FBXのパス
RENDER_WIDTH = 768
RENDER_HEIGHT = 1024
CAMERA_FOCAL_MM = 50.0
CAMERA_HEIGHT = 1.0       # キャラ腰あたりを狙う
CAMERA_DISTANCE = 4.5     # キャラからの距離（m）
SUN_ENERGY = 3.0
AREA_ENERGY = 200.0
WORLD_BG_COLOR = (0.5, 0.5, 0.5, 1.0)
```
