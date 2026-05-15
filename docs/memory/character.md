# キャラクター・ポージング — character

Mixamo の Without Skin ポーズFBXを使って、リギング不要で **1キャラ × 多数ポーズ** を量産する手順とノウハウ。AI画像生成（Stable Diffusion + ControlNet）への入力画像（Beauty / Depth / Normal / OpenPose）作りを想定。

## 基本ワークフロー

1. **キャラ取得**: Mixamo から **With Skin** で T-Pose の素体FBXを1個（例: `Jennifer.fbx`）
2. **ポーズ取得**: 同じキャラを選んだまま、**Without Skin** で複数モーションFBX（軽量、骨と動きだけ）
3. **保存**: `assets/mixamo/` に全部置く
4. **インポート＋セットアップ**: `snippets/character_setup.py` で素体をシーンに配置（カメラ・ライト含む）
5. **一括レンダー**: `snippets/character_render_poses.py` で全ポーズを順に当てて、4種類の画像を出力
6. **出力**: `outputs/character/poses/<pose_name>/{beauty,depth,normal,openpose}.png`

ポーズ転写は「ポーズFBXのアーマチュアアクションをアクションの中央フレームで読み、素体アーマチュアのpose bone回転にコピー」する方式。両者ともMixamo命名規則の骨を持つので、接尾辞ベースで照合できる。

## Blender 5.x の落とし穴（重要）

5.x で **コンポジタ周りが大改修** されており、3.x/4.x 用のコードは全滅する。以下が今回ハマった全部:

### 1. `scene.node_tree` が消えた

3.x/4.x:
```python
scn.use_nodes = True
tree = scn.node_tree
```

5.x（CompositorTreeが独立データブロックに）:
```python
scn.use_nodes = True
if scn.compositing_node_group is None:
    ng = bpy.data.node_groups.new("CompositorTree", 'CompositorNodeTree')
    scn.compositing_node_group = ng
tree = scn.compositing_node_group
```

### 2. コンポジタノードがほぼ消えた

新コンポジタで現状作れるのは **`CompositorNodeRLayers` と `CompositorNodeOutputFile` だけ**。`MixRGB`, `MapRange`, `Math`, `Normalize`, `ColorRamp` 等の汎用ノードは全部 `Node type ... undefined` エラーになる。

→ Depth の `1 - clamp((x-near)/(far-near))` や Normal の `0.5 + 0.5 * x` を **コンポジタで完結できない**。**生 EXR で書き出し → Python(numpy) で後段処理** にするのが安全。

### 3. `CompositorNodeOutputFile` の API も全とっかえ

| 旧API（〜4.x） | 新API（5.x） |
|---|---|
| `node.base_path = '...'` | `node.directory = '...'` + `node.file_name = '...'` |
| `node.file_slots.new("name")` | `node.file_output_items.new('RGBA' or 'FLOAT' or 'VECTOR', 'name')` |
| `node.format.file_format = 'PNG'` で即PNG | **`node.format.media_type = 'IMAGE'`** を先に立てないと `file_format` が `OPEN_EXR_MULTILAYER` 固定 |
| 1ノードに複数スロット = 個別ファイル | 1ノードに複数スロット = **マルチレイヤEXR 1個** |

→ パスごとに別 PNG/EXR を出したいなら **1パス = 1 OutputFile ノード** で、各ノードに `media_type='IMAGE'` を立て、`file_output_items.new()` でスロットを1つ追加（追加するとちゃんとフォーマット指定が効く）。接続は `node.inputs[0]`。

最小パターン:
```python
n = tree.nodes.new('CompositorNodeOutputFile')
n.directory = output_dir
n.file_name = "depth_raw"
n.format.media_type = 'IMAGE'   # ← これが無いとOPEN_EXR_MULTILAYER固定
n.format.file_format = 'OPEN_EXR'
n.format.color_mode = 'BW'
n.format.color_depth = '32'
n.file_output_items.new('FLOAT', '')  # ← 必須。inputs[0]が出てくる
tree.links.new(render_layers.outputs['Depth'], n.inputs[0])
```

## Pillow は入っていない

Blender 5.x バンドルのPython（3.13系）には **PIL/Pillow はデフォルト未導入**。3.xや古い記事の「PILで描く」コードは動かない。

**代替案**: numpy + Blender の `bpy.data.images.new()` + `image.save_render()` で PNG が書ける。

```python
def save_png_via_blender(rgba_float_topdown, filepath, color_depth='8'):
    h, w = rgba_float_topdown.shape[:2]
    flipped = np.flipud(rgba_float_topdown).astype(np.float32)
    use_float = (color_depth == '16')
    img = bpy.data.images.new("_tmp", w, h, alpha=True, float_buffer=use_float)
    img.pixels.foreach_set(flipped.ravel())
    scn = bpy.context.scene
    scn.render.image_settings.file_format = 'PNG'
    scn.render.image_settings.color_mode = 'RGBA'
    scn.render.image_settings.color_depth = color_depth
    img.save_render(filepath)
    bpy.data.images.remove(img)
```

太線・円のドローイングもPillow無しでnumpyだけで書ける（円ブラシをパラメトリックに敷き詰める）。コード本体は `snippets/character_render_poses.py` 参照。

## Mixamoボーンの接頭辞は不定

Mixamoの素体FBXは元々 `mixamorig:Hips` のような命名だが、Blenderにインポートすると **既存の "mixamorig" データブロックがあると衝突回避で `mixamorig1:`、`mixamorig2:`、… に書き換わる**。なので `mixamorig:Hips` 決め打ちで `pose.bones.get(...)` するとNoneが返って全部スカる。

→ **接尾辞マッチで照合**:
```python
def find_bone(arm, suffix):
    target = ":" + suffix
    for pb in arm.pose.bones:
        if pb.name.endswith(target) or pb.name == suffix:
            return pb
    return None
```

`pose.bones["mixamorig:Hips"]` ではなく `find_bone(arm, "Hips")` を使う。`copy_pose` でも src と dst の接頭辞が違うことがあるので、接尾辞インデックスで両者を突き合わせる。

## アクションが残ると pose が巻き戻る

Mixamoの素体FBX（With Skin、T-Pose）でも、インポートすると Blender は `Armature|mixamo.com|Layer0` というアクションをアーマチュアに **勝手に紐付ける**。

問題: `copy_pose` でボーン回転を書き換えても、その後の `bpy.ops.render.render()` 直前に `scene.frame_set(1)` するとアクションが再評価されて **T-Pose に巻き戻る**。

→ インポート直後に **アクションを外す**:
```python
if arm.animation_data and arm.animation_data.action:
    old = arm.animation_data.action
    arm.animation_data.action = None
    if old.users == 0:
        bpy.data.actions.remove(old)
```

`copy_pose` 内でも保険として同じことをやっておくと、毎ポーズで安全。

## OpenPose 画像の自前生成

ControlNet の OpenPose 入力は **18点キーポイント** の骨格画像。Mixamoボーンへのマッピングは以下:

| OP idx | 部位 | Mixamoボーン（接尾辞） |
|---:|---|---|
| 0 | Nose | （Head から幾何近似）|
| 1 | Neck | Neck |
| 2/5 | R/L Shoulder | RightArm / LeftArm（上腕の根本=肩関節）|
| 3/6 | R/L Elbow | RightForeArm / LeftForeArm |
| 4/7 | R/L Wrist | RightHand / LeftHand |
| 8/11 | R/L Hip | RightUpLeg / LeftUpLeg |
| 9/12 | R/L Knee | RightLeg / LeftLeg |
| 10/13 | R/L Ankle | RightFoot / LeftFoot |
| 14-17 | 目・耳 | Head と HeadTop_End から幾何近似 |

3D→2D 投影は `bpy_extras.object_utils.world_to_camera_view` を使う:
```python
co = world_to_camera_view(scene, camera, world_position)
x_px = co.x * resolution_x
y_px = (1.0 - co.y) * resolution_y
visible = 0 <= co.x <= 1 and 0 <= co.y <= 1 and co.z > 0
```

線・関節点の色はOpenPose公式の17 limbs / 18 colors を使うとControlNetが認識しやすい。

## Depth / Normal の生EXR後処理

Compositorの File Output で `OPEN_EXR` 浮動小数として書き出し、Pythonで:

```python
img = bpy.data.images.load(exr_path)
w, h = img.size
px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, -1)
px = np.flipud(px)  # Blenderのpixelsは下→上、PNGは上→下

# Depth: 近=1, 遠=0、背景の極大値はクランプ
d = px[:,:,0]
d = np.where(d > 1e6, depth_far, d)
norm = 1.0 - np.clip((d - near) / (far - near), 0, 1)

# Normal: [-1,1] → [0,1] にシフト
rgb = np.clip(px[:,:,:3] * 0.5 + 0.5, 0, 1)
```

カメラのクリップ範囲は `near=0.5, far=20.0` あたりがJenniferをポートレートで撮るとき妥当。被写体までの距離（カメラのlocationとキャラの中心の差）で調整。

## 落とし穴メモ（再掲・要約）

- **コンポジタAPIは5.xで別物**: `node_tree` → `compositing_node_group`、`base_path` → `directory`、`file_slots` → `file_output_items`、`media_type='IMAGE'` 必須
- **Pillowなし**: numpy + Blenderの image API で代替
- **ボーン接頭辞は変わる**: `mixamorig1:`, `mixamorig2:` ... 接尾辞マッチで対処
- **インポート時のアクションがpose上書き**: animation_data.action = None で外す
- **`if __name__ == "__main__"` ガードは exec(open(...).read()) で発火しない場合あり**: `importlib.util` でモジュールロードして `mod.main()` 直叩きが確実
- **Mixamoの100倍スケール**: armature.scale = 0.01 で対応、ただし `transform_apply` には selection が必要なので注意

## VRoid → Mixamo の落とし穴

`vrm_to_fbx_for_mixamo.py` の経緯から得た知見。

### 1. アーマチュア込みでアップロードすると auto-rig が走らない

Mixamo の auto-rigger は **メッシュのみのFBXを期待**する。アーマチュアが入った（=既にリグ済みの）FBXを投げると、「これはもうリグ済み」と判定して **auto-rig画面そのものがスキップされる**。返ってくるのは元のリグそのまま（VRoidなら `J_Bip_C_Hips` 等のHumanoid命名のまま）で、ファイル名やサイズは違うのにリグだけ未更新、というハマり方をする。

→ FBXエクスポートは必ず：
```python
bpy.ops.export_scene.fbx(
    ...
    object_types={'MESH'},          # アーマチュア除外
    use_mesh_modifiers=True,        # T-poseバインドを焼き込んで書き出す
    ...
)
```

VRM Add-on でインポートしたメッシュはアーマチュアモディファイア経由でバインドされているので、`use_mesh_modifiers=True` で評価結果（=T-poseの形）が書き出される。

### 2. Mixamoは同じキャラ判定でキャッシュを返すことがある

同一アカウント内で2回目以降のアップロードで、Mixamo側がコンテンツ重複と判定してauto-rigを省略するケースがある。回避は：
- ファイル名を変える（`motoko_v2.fbx` 等）
- 内容を微妙に変える（armature を Y軸 1mm 移動して apply 等）
- Mixamo Library から既存キャラを削除してから再アップロード

ただし上記1の「アーマチュア除外」さえちゃんとやっていれば、Mixamoは普通に新規キャラ扱いしてauto-rigを実行する。今回のハマりは1が主因で、2は副次的だった。

### 3. ビューポートのマテリアル崩れに騙されない

Mixamoでauto-rigを通ったVRoid系FBXをBlenderで開くと、**Solidビューポートではマゼンタ/欠落で見える**ことがある（MToon→Principled BSDFへの自動変換でテクスチャ参照が部分的に切れるため）。が、**Eeveeで実レンダーすると意外と綺麗に評価される**。崩れて見えても焦らずにレンダーしてみるのが吉。トゥーン陰影は失われるが、肌・髪・服のテクスチャは大体生きてる。

### 4. VRMインポートのメッシュ命名

VRM Add-onでインポートすると `Face`, `Body`, `Hair` という普通の名前のメッシュが3個できる。Mixamo経由で来ると `Face.003`, `Body.003`, `Hair` のように .001/.002/.003 サフィックスが付く（Blender側のdedupe）。`character_setup.py` のメッシュ命名チェックは厳密にせず、armature の子meshを全部拾うだけで良い。

### 5. 壊れたテクスチャ参照（emission_color_texture / normalmap_texture）— ピンクの正体

**症状**: VRoid → Mixamo経由のFBXをBlenderで読み込んでレンダーすると、**靴・顔・目などがshocking pink/magenta** で出る。一見「テクスチャの色」に見えるが実は**リンク切れの magenta フォールバック**。

**原因**: MixamoのFBXエクスポータが MToon → Principled BSDF 変換時に、Emission Color / Normal にも何かを繋ぎたくて、自分のサーバ側tmpフォルダの中間ファイル（`Shader_NoneBlack_002.png` 等）を指す **新規 image data block** を作る。具体的には：

- `emission_color_texture` (Mixamo命名) → filepath が `.../skins_<uuid>.fbm/Shader_NoneBlack_002.png`
- `normalmap_texture` (同上) → filepath が `.../skins_<uuid>.fbm/Shader_NoneNormal_002.png`

このtmpフォルダはMixamo側にしか存在しない（ユーザのPCには無い）ので、Blenderにロードしようとすると **size=0×0 / no-data 状態**になる。マテリアルの Emission Color スロットに繋がっているため、レンダー時にBlenderが magenta（missing texture fallback color）で出力する。

**確認方法**:
```python
for img in bpy.data.images:
    if img.size[0] == 0 and img.users > 0:
        print(img.name, img.filepath, "users:", img.users)
```

典型的に `emission_color_texture` (users=10) と `normalmap_texture` (users=7) が引っかかる。

**修正**: 同じシーン内には既に正常な `Shader_NoneBlack` (8×8 黒) と `Shader_NoneNormal` (8×8 ニュートラル法線) がパックされているので、壊れた参照をそちらに差し替える。

```python
NAME_FIXES = [
    ("emission_color_texture", "Shader_NoneBlack"),
    ("normalmap_texture",      "Shader_NoneNormal"),
]
for img in list(bpy.data.images):
    if img.size[0] != 0 or img.users == 0:
        continue
    for prefix, replacement_name in NAME_FIXES:
        if img.name.startswith(prefix):
            target = bpy.data.images.get(replacement_name)
            if target:
                for mat in bpy.data.materials:
                    if not mat.use_nodes: continue
                    for node in mat.node_tree.nodes:
                        if node.type == 'TEX_IMAGE' and node.image == img:
                            node.image = target
            break
```

これでEmission=黒（無発光）、Normal=ニュートラル（凹凸なし）になり、Mixamoが意図した「ゼロエミッション・ゼロ法線シフト」の Principled BSDF が正しく機能する。

### 6. VRoid テクスチャの番号マッピング（編集したいとき）

VRoid Studio が書き出すテクスチャは `_01.png` 〜 `_15.png` の数字命名で来る。Mixamo経由でも変わらず（接尾辞 .003 などが付くだけ）。Blender内では下記の対応：

| VRoid番号 | 部位 | 典型サイズ |
|---|---|---|
| `_01` | 口・歯 (FaceMouth) | 512×512 |
| `_02` | 虹彩 (EyeIris) | 1024×512 |
| `_03` | 瞳のハイライト (EyeHighlight) | 1024×512 |
| `_04` | 顔の肌 (Face skin) | 1024×1024 |
| `_05` | 顔シェーディング | 1024×1024 |
| `_06` | 白目 (EyeWhite) | 1024×512 |
| `_07` | 眉毛 (FaceBrow) | 1024×256 |
| `_08` | まつげ (FaceEyelash) | 1024×256 |
| `_09` | アイライン (FaceEyeline) | 1024×256 |
| `_10` | 体の肌 (Body skin) | 2048×2048 |
| `_11` | 体シェーディング | 2048×2048 |
| `_12` | 靴 (Shoes) | 512×512 |
| `_13` | 後ろ髪 (HairBack) | 1024×1024 |
| `_14`, `_15` | 前髪 (Hair front) | 512×1024 |

`MatcapWarp`, `Shader_NoneBlack`, `Shader_NoneNormal` 等の小さい (8×8) はMToonのユーティリティで編集対象外。

**テクスチャを外部編集可能にする**:

```python
import bpy, os
out_dir = r"...\textures"
for img in bpy.data.images:
    if not img.packed_file or img.size[0] == 0: continue
    target = os.path.join(out_dir, f"{img.name}.png")
    img.filepath_raw = target
    img.file_format = 'PNG'
    img.save()
    img.unpack(method='REMOVE')
    img.filepath = target
    img.reload()
```

これで `out_dir` 配下に PNG が並び、画像エディタで上書き編集 → Blender 次回レンダーで反映される（packed 状態を解除して FILE 参照に切り替えるのがミソ）。
