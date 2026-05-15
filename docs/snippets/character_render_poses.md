# character_render_poses.py

`character_setup.py` で準備したシーン上に、Mixamo の **Without Skin** ポーズFBXを順に当てて、ControlNet 4種類の入力画像（Beauty / Depth / Normal / OpenPose）を量産するメインスクリプト。Pillow 非依存（numpy + Blender image API で完結）。

## コード

```python
--8<-- "snippets/character_render_poses.py"
```

## 出力

```
outputs/character/poses/
├── boxing/
│   ├── beauty.png          # 通常レンダー（Cannyの元素材として）
│   ├── depth.png           # 16bit BW、近=白、遠=黒
│   ├── normal.png          # ワールドNormal を 0.5x+0.5 で RGB化
│   └── openpose.png        # アーマチュア由来の自前OpenPose骨格（18点）
├── hook/ ...
└── ...
```

## 仕組み

### ポーズ転写

1. ポーズFBXをインポート（新規アーマチュア + アクションが生成される）
2. アクションの中央フレームに `frame_set` → source の bone 回転値を取得
3. `dst_pose_bone.rotation_quaternion = src_pose_bone.rotation_quaternion` で素体に書き込む
4. 接尾辞マッチで照合（`mixamorig:` でも `mixamorig1:` でも対応）
5. ポーズFBXのアーマチュア + メッシュ群は削除

### 4種類画像の出力

| 種類 | 経路 |
|---|---|
| Beauty | コンポジタ: `Render Layers.Image → OutputFile (PNG, 8bit RGB)` |
| Depth | コンポジタで生EXR出力 → `bpy.data.images.load` で読み → numpyで `1 - clamp((z - near)/(far - near))` → 16bit BW PNG |
| Normal | コンポジタで生EXR出力 → numpyで `0.5 * n + 0.5` → 8bit RGB PNG |
| OpenPose | アーマチュアの18ボーン頭尾を `world_to_camera_view` でカメラ平面に投影 → numpyで線・円描画 → PNG |

## 注意点・落とし穴

- **Blender 5.x のコンポジタAPI大改修**:
    - `scene.compositing_node_group` を使う（旧 `scene.node_tree` は無い）
    - `OutputFile.directory` / `file_output_items` / `format.media_type='IMAGE'` の3点セットが必須
    - `MixRGB`, `MapRange` 等のノードが使えないので、後段は numpy 処理にしている
- **アクション残置**: Jennifer 側に Layer0 アクションが残っていると `frame_set` で T-pose に巻き戻る。`copy_pose` の冒頭で `dst.animation_data.action = None` する保険を入れている
- **ボーン接頭辞**: `mixamorig:` ではなく `mixamorig1:` になることが普通にある。`find_bone(arm, "Neck")` のような接尾辞ベース検索で照合
- **Pillow 不在**: Blender 5.x のバンドルPythonには PIL が無い。numpy で線・円ブラシを描き、Blenderの `image.save_render()` で PNG 出力

## カスタマイズポイント

```python
POSE_FBX_GLOB = r"...\assets\mixamo\*.fbx"
OUTPUT_ROOT = r"...\outputs\character\poses"
CHARACTER_ARMATURE_NAME = "Character"
EXCLUDE_CHARACTER_FILE = "Jennifer.fbx"   # 素体FBXは除外
```

カメラ近遠は `postprocess_passes(pose_dir, depth_near=0.5, depth_far=20.0)` で調整可能。被写体距離（カメラ←→キャラ）に合わせる。
